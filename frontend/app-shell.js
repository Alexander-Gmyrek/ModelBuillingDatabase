(function () {
    const hiddenPages = new Set([
        'TestInputTable.html',
        'test.html',
        'reviewcompany.html',
        'diffrentaddcompany.html'
    ]);

    function currentPage() {
        const page = window.location.pathname.split('/').pop();
        return page || 'index.html';
    }

    function addShell() {
        if (document.querySelector('.app-topbar')) return;

        const page = currentPage();
        const topbar = document.createElement('header');
        topbar.className = 'app-topbar';
        topbar.innerHTML = `
            <div class="app-brand">
                <strong>Billing Database</strong>
                <span>Health insurance billing workspace</span>
            </div>
            <nav class="app-nav" aria-label="Primary">
                <a href="setup.html">Setup</a>
                <a href="index.html">Companies</a>
                <a href="addcompany.html">New Company</a>
            </nav>
        `;
        document.body.insertBefore(topbar, document.body.firstChild);

        if (hiddenPages.has(page)) {
            const notice = document.createElement('div');
            notice.className = 'app-message';
            notice.textContent = 'This page is a prototype or test page. Use the main navigation for normal billing work.';
            topbar.insertAdjacentElement('afterend', notice);
        }

        addPageHint(page);
    }

    function addPageHint(page) {
        const hints = {
            'addcompany.html': 'Step 1 of company setup: enter employer details and upload the employee template.',
            'makeagetable.html': 'Step 2 of company setup: review age-banded tiers, carriers, and plan amounts before saving.',
            'makeagetiertable.html': 'Step 2 of company setup: review age-banded composite tiers, carriers, and plan amounts before saving.',
            'makeautogeneratetable.html': 'Step 2 of company setup: confirm the carrier and tier table built from the employee file.',
            'makesupertable.html': 'Step 2 of company setup: review supercomposite carriers and plan amounts before saving.',
            'maketable.html': 'Step 2 of company setup: review carriers, tiers, and plan amounts before saving.',
            'maketier3table.html': 'Step 2 of company setup: review 3-tier plan amounts before saving.',
            'maketier4table.html': 'Step 2 of company setup: review 4-tier plan amounts before saving.',
            'editCarrier.html': 'Plan maintenance: update carriers, tiers, and plan amounts for this company.'
        };

        if (!hints[page]) return;
        if (document.querySelector('.app-workflow-hint')) return;

        const hint = document.createElement('div');
        hint.className = 'app-message app-workflow-hint';
        hint.textContent = hints[page];

        const topbar = document.querySelector('.app-topbar');
        topbar.insertAdjacentElement('afterend', hint);
    }

    document.addEventListener('DOMContentLoaded', addShell);
})();
