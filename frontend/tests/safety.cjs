const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const root = path.resolve(__dirname, '..');
const stripImports = source => source.replace(/import\s*\{[\s\S]*?\}\s*from\s*[^;]+;/g, '');
const label = 'Carrier "Quoted" & <em id="injected-markup">Example</em>';

async function waitUntil(check) {
    for (let count = 0; count < 100; count++) {
        if (check()) return;
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error('Expected UI state did not appear.');
}

async function create(name) {
    const html = fs.readFileSync(path.join(root, name + '.html'), 'utf8');
    const dom = new JSDOM(html, {
        url: 'http://localhost:8080/' + name + '.html?id=1', runScripts: 'outside-only'
    });
    await waitUntil(() => dom.window.document.readyState === 'complete');
    dom.window.console.log = () => {};
    return { dom, view: dom.window, html };
}

async function checkWizard(name) {
    const { dom, view, html } = await create(name);
    view.eval(fs.readFileSync(path.join(root, 'employee-import.js'), 'utf8'));
    view.localStorage.setItem('companyData', JSON.stringify({
        EmployerName: 'Synthetic', TierStructure: '4 Tier', RenewalDate: '2026-01-01', Employees: []
    }));
    view.localStorage.setItem('carriers', JSON.stringify([{ CarrierName: 'HMO' }]));
    view.localStorage.setItem('tiers', JSON.stringify([{ TierName: 'Employee', MinAge: '', MaxAge: '' }]));
    view.localStorage.setItem('carrierData', JSON.stringify({
        HMO: { Employee: { 'Funding Amount': '100', 'Grenz Fee': '10' } }
    }));
    let previews = 0;
    let posts = 0;
    let submitted;
    let rejectPost = false;
    const alerts = [];
    const navigations = [];
    view.alert = message => alerts.push(message);
    view.billingPageUrl = value => { navigations.push(value); return '#done'; };
    view.showEmployeeImportPreview = async () => { previews++; return false; };
    view.addEmployer = async payload => {
        posts++;
        if (rejectPost) throw Object.assign(new Error('Synthetic rejected request'), { status: 400 });
        submitted = payload;
        return { new_id: 42 };
    };
    view.getFullTable = async () => ({
        Element: { Carriers: submitted.Carriers, Tiers: submitted.Tiers,
            Employees: submitted.Employees.map(employee => ({ ...employee, EmployeePlan: [{}] })) }
    });
    for (const match of html.matchAll(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/g)) {
        view.eval(stripImports(match[1]));
    }
    view.document.dispatchEvent(new view.Event('DOMContentLoaded'));
    const input = view.document.querySelector('.carrier-input');
    input.value = label;
    input.dispatchEvent(new view.Event('input'));
    view.document.getElementById('addTierButton').click();
    assert.equal(view.document.getElementById('injected-markup'), null, name);
    assert.equal(view.document.querySelector('.carrier-input').value, label, name);
    assert([...view.document.querySelectorAll('.data-input')].some(field => field.dataset.carrier === label));
    const company = JSON.parse(view.localStorage.getItem('companyData'));
    company.Employees = [{ EmployeeFullName: 'Synthetic Employee', Carrier: label,
        Tier: view.document.querySelector('.tier-input').value,
        StartDate: '2026-01-01', InformStartDate: '2026-01-01', Dependents: [] }];
    view.localStorage.setItem('companyData', JSON.stringify(company));
    const button = view.document.getElementById('submitButton');
    button.click();
    await waitUntil(() => previews === 1 && !button.disabled);
    assert.equal(posts, 0, name + ' cancelled preview');
    assert.deepEqual(navigations, [], name + ' cancelled navigation');
    company.RenewalDate = '2027-01-01';
    view.localStorage.setItem('companyData', JSON.stringify(company));
    button.click();
    await waitUntil(() => alerts.length > 0 && !button.disabled);
    assert.equal(posts, 0, name + ' validation failure');
    assert.deepEqual(navigations, [], name + ' validation navigation');
    company.RenewalDate = '2026-01-01';
    view.localStorage.setItem('companyData', JSON.stringify(company));
    view.showEmployeeImportPreview = async () => true;
    rejectPost = true;
    button.click();
    await waitUntil(() => posts === 1 && !button.disabled);
    assert.deepEqual(navigations, [], name + ' rejected submission navigation');
    rejectPost = false;
    button.click();
    await waitUntil(() => posts === 2 && button.disabled);
    assert.equal(JSON.parse(view.localStorage.getItem('companyData')).EmployerID, 42);
    if (name !== 'maketable') {
        await waitUntil(() => navigations.length === 1);
        assert.deepEqual(navigations, ['index.html']);
    }
    dom.window.close();
}

async function checkCompanyRendering() {
    const { dom, view, html } = await create('company1');
    view.billingPageUrl = value => value;
    view.searchEmployerById = async () => ({ EmployerName: 'Synthetic' });
    view.searchEmployeeByJson = async () => [];
    view.searchCarrierByJson = async () => [{ CarrierID: 1, CarrierName: label }];
    view.searchTierByJson = async () => [{ TierID: 1, TierName: label }];
    view.searchActiveEmployees = async () => [];
    view.searchPlanByJson = async () => [{ PlanID: 1, CarrierID: 1, TierID: 1, FundingAmount: 100, GrenzFee: 10 }];
    view.searchActivePlans = async () => [[1]];
    view.eval(stripImports(html.match(/<script type="module">([\s\S]*?)<\/script>/)[1]));
    view.document.dispatchEvent(new view.Event('DOMContentLoaded'));
    await waitUntil(() => view.document.querySelector('#tableContainer h2'));
    assert.equal(view.document.getElementById('injected-markup'), null);
    assert.equal(view.document.querySelector('#tableContainer h2').textContent, label);
    assert.equal(view.document.querySelector('#tableContainer tbody td').textContent, label);
    dom.window.close();
}

(async () => {
    for (const name of ['maketable', 'maketier3table', 'maketier4table', 'makeagetable',
        'makeagetiertable', 'makeautogeneratetable', 'makesupertable']) await checkWizard(name);
    await checkCompanyRendering();
    console.log('Safety checks passed: escaped labels, cancelled previews, rejected submissions and success navigation across setup pages.');
})().catch(error => { console.error(error); process.exitCode = 1; });
