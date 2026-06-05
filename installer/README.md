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

## Current Limitation

This is not yet a signed `.app`, `.pkg`, `.msi`, or `.exe` installer. It is a guided launcher that proves the user flow before we package it as a native installer.

