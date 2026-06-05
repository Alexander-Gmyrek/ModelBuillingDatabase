# Project Workspace

This repo was pulled from `Alexander-Gmyrek/ModelBuillingDatabase` on GitHub.

## Local Project Shape

- `Backend/`: Flask API, MySQL connector code, schema initialization SQL, sample Excel reports.
- `frontend/`: Static HTML/JavaScript frontend served by nginx in Docker.
- `docker-compose.yml`: Builds frontend and backend containers and starts a local MySQL database.

## Current Baseline

- Default GitHub branch: `main`.
- Python syntax check passes for `Backend/app.py` and `Generate_Test_Data.py` using the bundled Codex Python runtime.
- `Backend/requirements.txt` has been normalized from UTF-16 to plain UTF-8 so standard `pip install -r Backend/requirements.txt` and Docker builds can read it.
- `frontend/apiFunctions.js` has been added so the frontend pages can import the API helper directly.
- Backend database connection settings are now read from environment variables.
- Easy-start launchers now live in `installer/`.
- A browser setup wizard now lives at `frontend/setup.html`.

## Setup Notes

- The backend listens on port `3000` in Docker.
- Docker Compose runs MySQL as the `db` service with a persistent `billing-db-data` volume.
- The backend connects to the Compose database through `MYSQL_HOST=db`.
- The frontend is exposed on `http://localhost:8080`.

## Good Next Steps

1. Run the easy-start wizard on a machine with Docker installed and verify `/api`, `/testconnection`, and the frontend.
2. Add smoke tests for core API routes.
3. Add a desktop-app packaging layer for non-technical users.
4. Add backup, restore, authentication, and data-protection controls before production health-insurance use.
