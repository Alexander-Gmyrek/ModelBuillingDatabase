const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, '../employee1.html'), 'utf8');
const script = html.match(/<script type="module">([\s\S]*?)<\/script>/)[1];
assert(script.includes("apiFunctions.js?v="));
const executable = script.replace(/import\s*\{[\s\S]*?\}\s*from\s*[^;]+;/g, '');

async function waitUntil(check) {
    for (let count = 0; count < 100; count++) {
        if (check()) return;
        await new Promise(resolve => setTimeout(resolve, 10));
    }
    throw new Error('Employee page did not finish loading.');
}

async function testPage(failingSection) {
    const dom = new JSDOM(html, { url: 'http://localhost:8080/employee1.html?id=1', runScripts: 'outside-only' });
    const view = dom.window;
    await waitUntil(() => view.document.readyState === 'complete');
    view.billingPageUrl = value => value;
    view.searchEmployeeById = async () => ({
        EmployeeID: 1, EmployerID: 1, EmployeeFullName: 'Synthetic Employee',
        StartDate: '2026-01-01', InformStartDate: 'Thu, 15 Jan 2026 00:00:00 GMT',
        CobraStatus: true
    });
    view.searchDependentByJson = async () => {
        if (failingSection === 'dependents') throw new Error('Synthetic dependent error');
        return [{ DependentID: 2, DependentName: 'Synthetic Child', Relationship: 'Child', DOB: '2015-01-01' }];
    };
    view.getFullTable = async () => {
        if (failingSection === 'enrollment') throw new Error('Synthetic enrollment error');
        return { Element: { Plans: [], Carriers: [], Tiers: [] } };
    };
    view.searchEmployeePlanByJson = async () => [];
    view.eval(executable);
    view.document.dispatchEvent(new view.Event('DOMContentLoaded'));
    await waitUntil(() => view.document.getElementById('currentEnrollment').textContent !== 'Loading enrollment...');
    assert.equal(view.document.getElementById('employeeFullName').value, 'Synthetic Employee');
    assert.equal(view.document.getElementById('joinDate').value, '2026-01-01');
    assert.equal(view.document.getElementById('informJoinDate').value, '2026-01-15');
    assert.equal(view.document.getElementById('CobraStatus').checked, true);
    assert.equal(view.document.querySelectorAll('#editableTable tbody tr').length, 1);
    assert.equal(view.document.querySelector('input[type="submit"]').disabled, failingSection === 'dependents');
    assert.equal(view.document.getElementById('changePlan').disabled, failingSection === 'enrollment');
    if (!failingSection) {
        assert.equal(view.document.querySelector('[name="dependentName"]').value, 'Synthetic Child');
    }
    if (failingSection === 'dependents') {
        assert(view.document.getElementById('employeeLoadStatus').textContent.includes('dependents could not be loaded'));
    }
    if (failingSection === 'enrollment') {
        assert(view.document.getElementById('currentEnrollment').textContent.includes('Could not load enrollment'));
    }
    dom.window.close();
}

(async () => {
    await testPage(null);
    await testPage('dependents');
    await testPage('enrollment');
    console.log('Employee page checks passed: profile, dates, COBRA, dependents, enrollment, and partial loading failures.');
})().catch(error => { console.error(error); process.exitCode = 1; });
