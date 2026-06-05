# Frontend Audit

Reviewed the individual frontend HTML pages for broken imports, missing handlers, bad field names, and obvious workflow gaps.

## Pages Reviewed

- `TestInputTable.html`
- `addcompany.html`
- `addemployee.html`
- `company1.html`
- `diffrentaddcompany.html`
- `editCarrier.html`
- `employee1.html`
- `index.html`
- `makeagetable.html`
- `makeagetiertable.html`
- `makeautogeneratetable.html`
- `makesupertable.html`
- `maketable.html`
- `maketier3table.html`
- `maketier4table.html`
- `reviewcompany.html`
- `setup.html`
- `test.html`

## Fixes Made

- Added shared `frontend/app.css` styling for consistent layout, navigation, forms, tables, buttons, and empty states.
- Added shared `frontend/app-shell.js` navigation and workflow hints across all pages.
- Improved the company list with clearer loading, empty, search, and delete states.
- Improved the add-company page wording and layout so it reads like a guided setup step.
- Improved the company detail page with clearer employee status messages and report action text.
- Added guidance text to the add/edit employee pages.
- Converted `reviewcompany.html` from raw JavaScript into a real placeholder page.
- Rebuilt `addemployee.html` so it submits actual employee values instead of DOM elements.
- Rebuilt `employee1.html` so it can update employees, add/change dependents, and call the termination endpoint.
- Fixed employee active/inactive display in `company1.html`.
- Removed a broken inline search handler from `index.html` and fixed the delete button event handler.
- Fixed strict-mode undeclared variables in `addcompany.html`.
- Fixed `makeautogeneratetable.html` local-storage fallback variables.
- Removed redirects to missing `default_page.html`.
- Fixed `searchActiveEmployeePlans` in `apiFunctions.js`.
- Fixed `endPlan` in `apiFunctions.js` to use the backend route method.
- Added `terminateEmployee` to `apiFunctions.js`.
- Fixed the backend employee termination route so it uses a database cursor and commits changes.
- Added backup and restore controls to `setup.html`.
- Rebuilt `editCarrier.html` into a working plan maintenance screen backed by a transaction-style API endpoint.

## Verification

- All frontend HTML pages include the shared app stylesheet and shell script.
- All frontend HTML inline scripts pass JavaScript syntax checks.
- Backend Python compile check passes for `Backend/app.py` and `Generate_Test_Data.py`.
- A stale-reference scan no longer finds the old broken field names or missing `default_page.html` redirect.

## Remaining Product Work

- The `make*table.html` pages are still duplicated and should eventually be consolidated into one reusable plan-builder page.
- `reviewcompany.html`, `test.html`, and `TestInputTable.html` look like prototype/test pages and should be either finished, hidden, or removed from the user-facing install.
- A browser test with the Docker stack running is still needed to verify API behavior end to end.
