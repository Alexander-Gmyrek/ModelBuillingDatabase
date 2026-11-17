const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');
const XLSX = require('xlsx');

const root = path.resolve(__dirname, '..');
const template = fs.readFileSync(path.join(root, 'assets/employee_upload_template.xlsx'));
const spreadsheet = { arrayBuffer: async () => template };
const common = fs.readFileSync(path.join(root, 'employee-import.js'), 'utf8');

function setup(html) {
    const dom = new JSDOM(html, { url: 'http://localhost:8080/importemployees.html?id=1', runScripts: 'outside-only' });
    const window = dom.window;
    window.XLSX = XLSX;
    window.HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
    window.HTMLDialogElement.prototype.close = function (value) {
        this.returnValue = value;
        this.removeAttribute('open');
        this.dispatchEvent(new window.Event('close'));
    };
    window.eval(common);
    return dom;
}

async function waitUntil(check) {
    for (let attempt = 0; attempt < 100; attempt++) {
        if (check()) return;
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error('Expected UI state did not appear.');
}

async function run() {
    const dom = setup('<body></body>');
    const { window } = dom;
    const employees = await window.readEmployeeSpreadsheet(spreadsheet);
    assert.equal(employees.length, 3);
    assert.equal(employees[1].Dependents.length, 1);
    assert.equal(employees[0].CobraStatus, false);
    assert.equal(employees[0].StartDate, '2026-01-01');
    assert.equal(window.formatDate('6/15/2026', 2), '2026-06-15');
    assert.throws(() => window.formatDate('2026-02-30', 2), /Row 2/);
    const normalized = window.normalizeImportRow({ ' GL Code ': '100', Cobra: 'No' });
    assert.equal(normalized.GL, '100');
    assert.equal(normalized.cobra, 'No');
    let preview = window.showEmployeeImportPreview(employees);
    assert.equal(window.document.querySelectorAll('dialog tbody tr').length, 3);
    window.document.querySelector('dialog button.secondary').click();
    assert.equal(await preview, false);
    preview = window.showEmployeeImportPreview(employees, { Errors: ['Plan coverage conflict'] });
    assert.equal(window.document.querySelector('dialog .actions button:last-child').disabled, true);
    window.document.querySelector('dialog button.secondary').click();
    await preview;
    dom.window.close();

    const html = fs.readFileSync(path.join(root, 'importemployees.html'), 'utf8');
    const upload = setup(html);
    const page = upload.window;
    page.billingPageUrl = value => value;
    page.searchEmployerById = async () => ({ EmployerName: 'Synthetic Company' });
    page.crypto.randomUUID = () => 'synthetic-upload-key';
    const requests = [];
    page.fetch = async (url, options) => {
        requests.push({ url, payload: JSON.parse(options.body) });
        return { ok: true, json: async () => url.endsWith('/preview') ?
            { Errors: [], Warnings: [], NewCount: 3, SkippedCount: 0 } : { ImportedCount: 3 } };
    };
    const inline = [...html.matchAll(/<script type="module">([\s\S]*?)<\/script>/g)][0][1]
        .replace(/import\s*\{[\s\S]*?\}\s*from\s*[^;]+;/g, '');
    page.eval(inline);
    Object.defineProperty(page.document.getElementById('roster'), 'files', { value: [spreadsheet] });
    page.document.getElementById('importForm').dispatchEvent(new page.Event('submit', { cancelable: true }));
    await waitUntil(() => page.document.querySelector('dialog'));
    assert.equal(requests.length, 1);
    page.document.querySelector('dialog .actions button:last-child').click();
    await waitUntil(() => page.document.getElementById('importStatus').textContent.includes('3 employees imported'));
    assert.equal(requests.length, 2);
    assert.equal(requests[0].payload.BatchKey, requests[1].payload.BatchKey);
    assert.equal(page.document.getElementById('previewButton').disabled, true);
    upload.window.close();
    for (const name of ['maketable', 'maketier3table', 'maketier4table',
        'makeagetable', 'makeagetiertable', 'makeautogeneratetable', 'makesupertable']) {
        const markup = fs.readFileSync(path.join(root, name + '.html'), 'utf8');
        const wizard = setup(markup);
        const view = wizard.window;
        await waitUntil(() => view.document.readyState === 'complete');
        view.localStorage.setItem('companyData', JSON.stringify({
            EmployerName: 'Synthetic', TierStructure: '4 Tier',
            Employees: [], RenewalDate: '2026-01-01'
        }));
        view.localStorage.setItem('carriers', JSON.stringify([{ CarrierName: 'HMO' }, { CarrierName: 'Other' }]));
        view.localStorage.setItem('tiers', JSON.stringify([{ TierName: 'Employee', MinAge: '', MaxAge: '' }]));
        view.localStorage.setItem('carrierData', JSON.stringify({
            HMO: { Employee: { 'Funding Amount': '100', 'Grenz Fee': '10', 'Grenz Fee C': '', 'Grenz Fee S': '' } },
            Other: { Employee: { 'Funding Amount': '200', 'Grenz Fee': '20', 'Grenz Fee C': '', 'Grenz Fee S': '' } }
        }));
        for (const script of markup.matchAll(/<script(?![^>]*src=)[^>]*>([\s\S]*?)<\/script>/g)) {
            view.eval(script[1].replace(/import\s*\{[\s\S]*?\}\s*from\s*[^;]+;/g, ''));
        }
        view.document.dispatchEvent(new view.Event('DOMContentLoaded'));
        const carrier = view.document.querySelector('.carrier-input');
        assert(carrier, name + ' carrier input');
        const original = carrier.value;
        const draft = JSON.parse(view.localStorage.getItem('companyData'));
        draft.Employees = [
            { EmployeeFullName: 'Linked', Carrier: original, Tier: 'Employee',
                StartDate: '2026-01-01', Dependents: [{ DependentName: 'Child' }] },
            { EmployeeFullName: 'Unaffected', Carrier: 'Other', Tier: 'Employee', StartDate: '2026-01-01' }
        ];
        view.localStorage.setItem('companyData', JSON.stringify(draft));
        for (const next of ['Kaiser', 'Kaiser Permanente']) {
            carrier.value = next;
            carrier.dispatchEvent(new view.Event('input'));
            const changed = JSON.parse(view.localStorage.getItem('companyData'));
            assert.equal(changed.Employees[0].Carrier, next, name);
            assert.equal(changed.Employees[1].Carrier, 'Other', name);
            assert.equal(changed.Employees[0].Dependents[0].DependentName, 'Child');
            assert(view.document.querySelector(`[data-carrier="${next}"]`), name + ' plan link');
        }
        if (name === 'makeautogeneratetable') {
            const amount = view.document.querySelector('[data-carrier="Kaiser Permanente"][data-type="Funding Amount"]');
            assert.equal(amount.value, '100');
            carrier.value = 'Other';
            carrier.dispatchEvent(new view.Event('input'));
            assert.equal(carrier.validity.valid, false);
            assert.equal(JSON.parse(view.localStorage.getItem('companyData')).Employees[0].Carrier, 'Kaiser Permanente');
        }
        view.document.getElementById('tableContainer').replaceChildren();
        view.document.dispatchEvent(new view.Event('DOMContentLoaded'));
        assert.equal(view.document.querySelector('.carrier-input').value, 'Kaiser Permanente', name + ' reload');
        const reloaded = JSON.parse(view.localStorage.getItem('companyData'));
        assert.equal(reloaded.PlanSetupDraft.Carriers[0].CarrierName, 'Kaiser Permanente');
        assert.equal(reloaded.Employees[0].Carrier, 'Kaiser Permanente');
        if (name === 'makeautogeneratetable') {
            assert.equal(view.document.querySelector('[data-carrier="Kaiser Permanente"][data-type="Funding Amount"]').value, '100');
        }
        const tierName = view.document.querySelector('.tier-input').value;
        reloaded.Employees = [{ EmployeeFullName: 'Linked', Carrier: 'Kaiser Permanente',
            Tier: tierName, StartDate: '2026-01-01', Dependents: [] }];
        view.localStorage.setItem('companyData', JSON.stringify(reloaded));
        let submitted = null;
        view.addEmployer = async value => {
            submitted = JSON.parse(JSON.stringify(value));
            return { new_id: 42 };
        };
        view.getFullTable = async () => { throw new Error('Simulated follow-up failure'); };
        view.alert = () => {};
        view.showEmployeeImportPreview = async () => true;
        await view.submitTable({
            Carriers: [{ CarrierName: 'Kaiser Permanente' }],
            Tiers: [{ TierName: tierName }],
            Plans: [{ CarrierName: 'Kaiser Permanente', TierName: tierName,
                StartDate: '2026-01-01', FundingAmount: '100', GrenzFee: '10' }]
        });
        assert(submitted, name + ' submission');
        assert.equal(submitted.Employees[0].Carrier, submitted.Plans[0].CarrierName);
        assert.equal(submitted.PlanSetupDraft, undefined, name + ' UI state excluded');
        view.close();
    }
    console.log('Carrier rename checks passed across all seven setup pages, including repeated renames and duplicate blocking.');
    console.log('Frontend checks passed: real Excel decoding, aliases, dates, preview/cancel/errors, import and retry key.');
}

run().catch(error => { console.error(error); process.exitCode = 1; });
