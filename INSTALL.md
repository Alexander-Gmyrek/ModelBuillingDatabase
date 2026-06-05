# Install And Run Locally

This app is a local health-insurance billing database with:

- a Flask API backend,
- a MySQL database,
- a static HTML frontend,
- Docker Compose orchestration for a self-contained local install.

## Requirements

- Docker Desktop or another Docker Engine with Docker Compose support.

## Easy Start Wizard

Use the launcher for your device:

- macOS: double-click `installer/start-macos.command`
- Windows: double-click `installer/start-windows.bat`

The wizard checks that Docker is installed and running, starts the app, waits for the API, then opens:

```text
http://localhost:8080/setup.html
```

The setup page checks the API and database before sending the user into the app.

## Manual Start

From the project folder, run:

```bash
docker compose up --build
```

Then open:

- Setup page: `http://localhost:8080/setup.html`
- Frontend: `http://localhost:8080/index.html`
- Backend health check: `http://localhost:3000/api`
- Database connection check: `http://localhost:3000/testconnection`

The MySQL database is created automatically from `Backend/init.sql` the first time the app starts. Database data is stored in the Docker volume `billing-db-data`, so it persists across restarts.

The setup page also includes backup and restore controls. Backups download a JSON file containing the local billing database. Restore replaces the current local database with the selected backup file.

## Stop The App

```bash
docker compose down
```

To remove the database data as well:

```bash
docker compose down -v
```

## Current Local Ports

- Frontend: `8080`
- Backend API: `3000`
- MySQL: `3307` on the host, mapped to `3306` inside Docker

## Packaging Roadmap

The current install path is Docker-based. To make this feel like a normal end-user desktop app, the next packaging milestone should wrap this local web app in a desktop shell and installer:

1. Keep Docker Compose as the reliable developer and power-user install path.
2. Improve the app launcher that starts/stops the backend and database services.
3. Package the launcher as a signed macOS `.app`/`.pkg` and Windows `.exe`/`.msi`.
4. Add backup, restore, and export controls before real customer data is used.
5. Add authentication and local data-protection controls before handling sensitive production health-insurance records.
