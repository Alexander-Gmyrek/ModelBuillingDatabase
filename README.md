# Health Insurance Billing Database

This app is a local billing database for health-insurance administration. It manages employers, employees, dependents, carriers, tiers, plans, enrollment data, and monthly billing reports.

The app runs locally on a person's device using Docker. The current install flow includes an easy-start wizard for macOS and Windows.

## App Functionality

- Local self-contained billing database for health-insurance administration.
- Easy-start launcher for macOS and Windows.
- First-run setup page to check the API, database, and app readiness.
- Local MySQL database managed through Docker Compose.
- Company/employer management:
  - add companies
  - view companies
  - search companies
  - delete companies
  - configure renewal and preferred billing dates
- Employee enrollment management:
  - add employees
  - view employees by company
  - search employees
  - edit employee details
  - mark employees active or inactive
  - terminate employees with termination dates
- Dependent management:
  - add dependents when creating or editing employees
  - edit dependent details
  - end dependent coverage through employee termination
- Carrier management:
  - add carriers
  - edit carrier names
  - remove carriers from the active plan setup while preserving historical plan records
- Tier management:
  - add tiers
  - edit tier names
  - edit age-band minimum and maximum ages
  - remove tiers from the active plan setup while preserving historical plan records
- Plan management:
  - create plan rows for carrier/tier combinations
  - edit funding amounts
  - edit Grenz fees
  - edit child/spouse fee fields
  - set plan start dates
  - save carrier, tier, and plan setup in one maintenance screen
  - end removed active plans instead of hard-deleting historical records
- Employee plan tracking:
  - change an employee's carrier/plan with effective and informed dates while preserving enrollment history
  - assign employees to plans through carrier/tier selection
  - find active employee plans
  - preserve plan history for billing/reporting
- Monthly billing report generation:
  - include a month-by-month Adjustment Details worksheet that reconciles to the bill
  - reopen exact saved bill workbooks from the company page after later record/rate edits
  - generate Excel billing reports by company, year, and month
  - download generated reports from the browser
  - include backdated billing adjustments for late employee, dependent, and plan changes
- Database backup and restore:
  - include saved bills and change history in backups, with support for older backup files
  - download a local JSON backup of all billing tables
  - restore the local database from a selected backup file
- Employee spreadsheet imports:
  - preview employee counts, carriers, tiers, dates, and validation messages before saving
  - create a company without a roster, then import employees from the company page
  - skip matching existing employee names and prevent repeated imports of the same submission
- Change history:
  - review timestamped before/after changes, terminations, imports, and restores on the company page
- API access for all core billing tables:
  - Employer
  - Employee
  - Dependent
  - Carrier
  - Tier
  - Plan
  - EmployeePlan
- Search and lookup tools:
  - search employers, employees, carriers, tiers, dependents, plans, and employee plans
  - fetch full company records with related employees, carriers, tiers, and plans
- Local app navigation:
  - setup page
  - company list
  - new company setup
  - company details
  - employee add/edit pages
  - plan maintenance page

## Backdated Billing Adjustments

The billing report tracks both the actual coverage date and the date the employer informed the user about the change.

- `StartDate`: when employee, dependent, or plan coverage actually started.
- `InformStartDate`: when the app user was informed that coverage started.
- `EndDate`: when employee, dependent, or plan coverage actually ended.
- `InformEndDate`: when the app user was informed that coverage ended.

When a monthly bill is generated, the app uses the informed date to decide which bill should receive the adjustment, then uses the actual coverage date to calculate the months affected.

- Late employee or dependent additions create catch-up charges for the missed coverage months.
- Late employee or dependent terminations create credits for months that should no longer have been billed.
- Late plan starts or plan ends create matching catch-up charges or credits tied to the affected carrier and tier.
- The adjustment appears on the next generated bill for the month when the user was informed.

### Monthly Coverage Rules

- Start and termination months are charged in full, including mid-month dates.
- Before an employee's start month, the employee is absent from newly generated bills.
- Between the start month and informed-start month, the employee appears at zero with `Hire (dd-mm-yyyy)`.
- The informed-start bill charges the missed coverage months plus the current month. Later bills use normal monthly charges without the hire note.
- Through the termination month, normal coverage charges apply. Before the informed-termination month, subsequent bills continue charging coverage and show `Term (dd-mm-yyyy)`.
- The informed-termination bill credits the months after termination that were previously chargeable. The termination month itself is not credited. The term note remains on this bill.
- After the termination and notification months have passed, the employee is omitted.
- A late carrier, plan, or tier switch keeps the old rate on bills before notification. The notification bill charges the new current-month rate and adjusts each earlier affected month by the difference.
- `Plan change (dd-mm-yyyy)` appears from the effective month through the notification month.
- Newly generated historical bills follow these rules. Previously saved bill workbooks remain unchanged.

## Requirements

Before downloading and running the app, install:

- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Git, if you want to download the project with `git clone`

Docker Desktop must be running before you start the app.

## Download

### Option 1: Download ZIP

1. Go to the GitHub repo:
   https://github.com/Alexander-Gmyrek/ModelBuillingDatabase
2. Click the green `Code` button.
3. Click `Download ZIP`.
4. Unzip the downloaded file.
5. Open the unzipped project folder.

### Option 2: Clone With Git

```bash
git clone https://github.com/Alexander-Gmyrek/ModelBuillingDatabase.git
cd ModelBuillingDatabase
```

## Easy Start

Use the launcher for your device:

- macOS: double-click `installer/start-macos.command`
- Windows: double-click `installer/start-windows.bat`

The launcher checks that Docker is installed and running, starts the database/API/frontend, waits for the app to become ready, then opens:

```text
http://localhost:8080/setup.html
```

On the setup page, run the checks and initialize the database if needed. Then click `Open App`.

The setup page also includes backup and restore controls. Download a fresh backup before restoring a backup, resetting sample data, moving devices, or making a major billing update.

## Manual Start

From the project folder, run:

```bash
docker compose up --build
```

Then open:

- Setup page: `http://localhost:8080/setup.html`
- App: `http://localhost:8080/index.html`
- API check: `http://localhost:3000/api`
- Database check: `http://localhost:3000/testconnection`

## Stop The App

Use the launcher for your device:

- macOS: double-click `installer/stop-macos.command`
- Windows: double-click `installer/stop-windows.bat`

Or run:

```bash
docker compose down
```

To also delete the local database data:

```bash
docker compose down -v
```

## Local Ports

- Frontend: `8080`
- Backend API: `3000`
- MySQL: `3307` on the host

If one of these ports is already being used, stop the other app or update `docker-compose.yml`.

## Troubleshooting

- If Docker is missing, install Docker Desktop and run the start launcher again.
- If Docker is installed but not running, open Docker Desktop and wait for it to finish starting.
- If the setup page opens but checks fail, wait one minute and click `Run Checks`.
- If the API still does not respond, open Docker Desktop and confirm `billing-db`, `backend`, and `frontend` are running.
- If another app is using ports `8080`, `3000`, or `3307`, stop that app or update `docker-compose.yml`.
- If restore fails, make sure the file is a JSON backup downloaded from this app.

## Optional Signed Installer

This app does not need a commercial installer to be useful on an approved device. If you later want the launchers to feel more official, package the same Docker-based start and stop scripts as a signed macOS `.app`/`.pkg` or Windows `.exe`/`.msi`.

## Notes

This project is still a work in progress. Before using real health-insurance records, the app should have backup/restore, login/authentication, audit logging, and stronger data-protection controls.

More setup details are in `INSTALL.md`.
