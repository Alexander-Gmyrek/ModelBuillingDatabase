$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$FrontendUrl = "http://127.0.0.1:8080/setup.html"
$BackendUrl = "http://127.0.0.1:3000/api"

function Test-LocalEndpoint {
    param([string]$Url)
    $response = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create($Url)
        $request.Proxy = $null
        $request.Timeout = 2000
        $request.ReadWriteTimeout = 2000
        $request.KeepAlive = $false
        $response = $request.GetResponse()
        return @{ Ready = ([int]$response.StatusCode -eq 200); Error = "" }
    } catch {
        return @{ Ready = $false; Error = $_.Exception.Message }
    } finally {
        if ($null -ne $response) { $response.Close() }
    }
}

function Open-AppBrowser {
    try {
        Start-Process -FilePath $FrontendUrl -ErrorAction Stop
        Write-Host "Opened $FrontendUrl"
        Write-Host "You can close this window after the app opens."
    } catch {
        Write-Host "The app is responding, but Windows could not open your browser."
        Write-Host $_.Exception.Message
        Write-Host "Open this address in your browser: $FrontendUrl"
        Read-Host "Press Enter to close"
    }
}

Clear-Host
Write-Host "Health Insurance Billing Database"
Write-Host "---------------------------------"
Write-Host ""
Write-Host "This wizard will start the local database, API, and app UI."
Write-Host ""

try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker version check failed with exit code $LASTEXITCODE."
    }
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
    if ($LASTEXITCODE -ne 0) {
        throw "Docker daemon check failed with exit code $LASTEXITCODE."
    }
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
Write-Host "Waiting for the API and setup page to respond..."
$deadline = (Get-Date).AddMinutes(3)
do {
    $apiStatus = Test-LocalEndpoint $BackendUrl
    $frontendStatus = Test-LocalEndpoint $FrontendUrl
    if ($apiStatus.Ready -and $frontendStatus.Ready) {
        Write-Host "The app is ready."
        Open-AppBrowser
        exit 0
    }
    Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)

Write-Host ""
if ($frontendStatus.Ready) {
    Write-Host "The setup page is ready, but the launcher could not confirm the API."
    Write-Host "API check: $($apiStatus.Error)"
    Write-Host "Opening Setup so you can run the service checks."
    Open-AppBrowser
    exit 0
}
Write-Host "The containers started, but startup checks did not finish."
Write-Host "API check: $($apiStatus.Error)"
Write-Host "Setup page check: $($frontendStatus.Error)"
Write-Host "Try these steps:"
Write-Host "1. Wait one more minute, then refresh the setup page."
Write-Host "2. Open Docker Desktop and check that billing-db, backend, and frontend are running."
Write-Host "3. Make sure ports 8080, 3000, and 3307 are not being used by another app."
Write-Host ""
Write-Host "Setup page:"
Write-Host $FrontendUrl
Read-Host "Press Enter to close"
