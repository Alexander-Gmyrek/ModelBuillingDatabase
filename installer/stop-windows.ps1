$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Clear-Host
Write-Host "Health Insurance Billing Database"
Write-Host "---------------------------------"
Write-Host ""
Write-Host "This will stop the local app containers without deleting database data."
Write-Host ""

try {
    docker --version | Out-Null
} catch {
    Write-Host "Docker was not found. There is nothing this launcher can stop."
    Read-Host "Press Enter to close"
    exit 1
}

Set-Location $ProjectDir

Write-Host "Stopping the app..."
docker compose down
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "The app did not stop cleanly. Open Docker Desktop and stop the containers named billing-db, backend, and frontend."
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "The app is stopped. Your database data is still saved in Docker."
Read-Host "Press Enter to close"
