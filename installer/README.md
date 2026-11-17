# Easy Start Wizard

These launchers are the first install-wizard layer for the local billing database app.

## macOS

Double-click:

```text
installer/start-macos.command
```

If macOS blocks it, right-click the file, choose Open, then approve it.

## Windows

Double-click:

```text
installer/start-windows.bat
```

## What The Wizard Does

1. Checks whether Docker is installed.
2. Checks whether Docker is running.
3. Starts the app with `docker compose up --build -d`.
4. Waits for the backend API.
5. Opens the first-run setup page at `http://localhost:8080/setup.html`.

## Stop The App

When finished, use the matching stop launcher:

- macOS: double-click `installer/stop-macos.command`
- Windows: double-click `installer/stop-windows.bat`

The stop launcher runs `docker compose down`. It stops the app containers but keeps the database data saved in Docker.

## Backup Reminder

Before restoring a backup, resetting sample data, moving devices, or making a major billing change, download a backup from the setup page.

## Troubleshooting

- If Docker is missing, install Docker Desktop and run the start launcher again.
- If Docker is installed but not running, open Docker Desktop and wait for it to finish starting.
- If the app starts but the setup page says the API is not ready, wait one minute and run checks again.
- If it still does not respond, open Docker Desktop and confirm the `billing-db`, `backend`, and `frontend` containers are running.
- If another app is using ports `8080`, `3000`, or `3307`, stop that app or change the ports in `docker-compose.yml`.

## Current Limitation

This is not yet a signed `.app`, `.pkg`, `.msi`, or `.exe` installer. It is a guided launcher that proves the user flow before we package it as a native installer.
