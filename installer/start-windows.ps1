$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$FrontendUrl = "http://localhost:8080/setup.html"
$BackendUrl = "http://localhost:3000/api"

Clear-Host
Write-Host "Health Insurance Billing Database"
Write-Host "---------------------------------"
Write-Host ""
Write-Host "This wizard will start the local database, API, and app UI."
Write-Host ""

try {
    docker --version | Out-Null
} catch {
    Write-Host "Docker Desktop is required before this app can run."
    Write-Host "Install Docker Desktop, start it, then run this wizard again."
    Write-Host ""
    Write-Host "Download: https://www.docker.com/products/docker-desktop/"
    Read-Host "Press Enter to close"
    exit 1
}

try {
    docker info | Out-Null
} catch {
    Write-Host "Docker is installed, but it is not running yet."
    Write-Host "Start Docker Desktop, wait for it to finish loading, then run this wizard again."
    Read-Host "Press Enter to close"
    exit 1
}

Set-Location $ProjectDir

Write-Host "Starting the app. The first run can take a few minutes..."
docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The app did not start successfully. See the Docker output above."
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "Waiting for the API to respond..."
for ($i = 1; $i -le 60; $i++) {
    try {
        Invoke-WebRequest -Uri $BackendUrl -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "The app is ready."
        Start-Process $FrontendUrl
        Write-Host ""
        Write-Host "Opened $FrontendUrl"
        Write-Host "You can close this window after the app opens."
        exit 0
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "The containers started, but the API did not respond yet."
Write-Host "Open Docker Desktop to check container status, then try:"
Write-Host $FrontendUrl
Read-Host "Press Enter to close"

