# Product Roadmap

This app is intended to become an installable local billing database for health-insurance administration.

## Milestone 1: Reliable Local Install

Status: started

- Self-contained Docker Compose stack with frontend, backend, and MySQL.
- Persistent local database volume.
- Frontend served at `http://localhost:8080`.
- Backend API served at `http://localhost:3000`.
- Install instructions in `INSTALL.md`.
- Easy-start launchers in `installer/`.
- First-run setup page at `frontend/setup.html`.

Remaining:

- Run the wizard on a machine with Docker installed.
- Add automated smoke tests for startup and core API routes.
- Verify the backup/restore workflow against the Docker MySQL database.

## Milestone 2: Desktop Installer

Goal: make the app feel installable for non-developers.

Recommended path:

- Keep Docker Compose for development and technical installs.
- Add a desktop launcher that starts/stops the local services.
- Package the launcher for macOS and Windows.
- Open the app UI automatically after startup.
- Add first-run checks for port conflicts and database readiness.
- Sign/notarize the macOS app and sign the Windows installer for easier trust prompts.

## Milestone 3: Billing Product Completion

Core workflows to finish:

- Employer setup wizard.
- Carrier, tier, and plan management.
- Employee and dependent enrollment.
- Coverage change history.
- Termination and COBRA status handling.
- Monthly billing report generation.
- Report review and export.
- Search, filtering, and audit-friendly record views.

## Milestone 4: Data Safety

Before real health-insurance records are used:

- Add login/authentication.
- Add automatic local backups.
- Add restore/import controls.
- Add user-visible data export.
- Add audit logging for changes.
- Remove or protect destructive test endpoints such as database reset/clear routes.
- Review storage and access practices for sensitive employee and dependent data.

## Milestone 5: Polish

- Replace one-off HTML pages with a consistent app shell.
- Improve error messages and loading states.
- Add validation for dates, plan/tier selection, and required billing fields.
- Add end-to-end tests for the main workflows.
- Add a release checklist for each packaged version.
