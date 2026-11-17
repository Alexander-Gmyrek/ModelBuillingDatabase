const employerId = Number(new URLSearchParams(location.search).get('id'));
const api = window.BILLING_API_BASE_URL || 'http://localhost:3000';
let oldestChange = null;

async function getHistoryData(path) {
    const response = await fetch(`${api}/employer/${employerId}/${path}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.Error || 'Could not load records.');
    return result;
}

async function loadBills() {
    const status = document.getElementById('savedBillsStatus');
    try {
        const bills = await getHistoryData('reports');
        const body = document.getElementById('savedBills');
        body.replaceChildren();
        for (const bill of bills) {
            const row = body.insertRow();
            row.insertCell().textContent = bill.BillingMonth.slice(0, 7);
            row.insertCell().textContent = new Date(bill.CreatedAt).toLocaleString();
            const link = document.createElement('a');
            link.href = `${api}/employer/${employerId}/reports/${bill.ReportID}`;
            link.textContent = 'Download bill #' + bill.ReportID;
            row.insertCell().appendChild(link);
        }
        status.textContent = bills.length ? `${bills.length} saved bills.` : 'No saved bills yet.';
    } catch (error) {
        status.textContent = error.message;
    }
}

async function loadChanges(reset = false) {
    const status = document.getElementById('changeHistoryStatus');
    const button = document.getElementById('olderChanges');
    button.disabled = true;
    try {
        if (reset) oldestChange = null;
        const changes = await getHistoryData('history' + (oldestChange ? `?before=${oldestChange}` : ''));
        const container = document.getElementById('changeHistory');
        if (reset) container.replaceChildren();
        for (const change of changes) {
            const item = document.createElement('details');
            const summary = document.createElement('summary');
            summary.textContent = `${new Date(change.CreatedAt).toLocaleString()} - ${change.Action} - ${change.TableName} ${change.RecordID ?? ''}`;
            item.appendChild(summary);
            const table = document.createElement('table');
            const heading = table.createTHead().insertRow();
            for (const label of ['Field', 'Before', 'After']) {
                const cell = document.createElement('th');
                cell.textContent = label;
                heading.appendChild(cell);
            }
            const body = table.createTBody();
            const before = change.Before || {};
            const after = change.After || {};
            for (const field of new Set([...Object.keys(before), ...Object.keys(after)])) {
                if (change.Action === 'Update' && JSON.stringify(before[field]) === JSON.stringify(after[field])) continue;
                const row = body.insertRow();
                row.insertCell().textContent = field;
                for (const value of [before[field], after[field]]) {
                    row.insertCell().textContent = value == null ? '' :
                        typeof value === 'object' ? JSON.stringify(value) : String(value);
                }
            }
            const wrapper = document.createElement('div');
            wrapper.className = 'tableWrapper';
            wrapper.appendChild(table);
            item.appendChild(wrapper);
            container.appendChild(item);
        }
        if (changes.length) oldestChange = changes[changes.length - 1].ChangeID;
        button.hidden = changes.length < 100;
        status.textContent = container.childElementCount ? `${container.childElementCount} changes shown.` : 'No changes recorded yet.';
    } catch (error) {
        status.textContent = error.message;
    } finally {
        button.disabled = false;
    }
}

document.getElementById('olderChanges').addEventListener('click', () => loadChanges());
document.addEventListener('billing-report-saved', () => {
    loadBills();
    loadChanges(true);
});
if (employerId) {
    loadBills();
    loadChanges(true);
}
