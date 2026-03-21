#Requires -Version 5
<#
.SYNOPSIS
    Start the AI Assistant platform (backend + optionally build frontend).

.PARAMETER Dev
    Run Vite dev server alongside FastAPI (default — hot reload, faster iteration).

.PARAMETER Prod
    Build the frontend and serve everything from FastAPI on port 8000.
    Suitable for VPN/remote access.
#>
param(
    [switch]$Dev,
    [switch]$Prod
)

$Root = Split-Path $PSScriptRoot

if (-not $Dev -and -not $Prod) { $Dev = $true }

Set-Location $Root

if ($Prod) {
    Write-Host "Building frontend..." -ForegroundColor Cyan
    Push-Location frontend-web
    npm run build
    Pop-Location
    Write-Host "Starting backend (serving frontend at /ui)..." -ForegroundColor Cyan
    & ".venv\Scripts\python.exe" -m backend.gateway.main
} else {
    Write-Host "Starting backend..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root'; .venv\Scripts\python.exe -m backend.gateway.main"
    Write-Host "Starting frontend dev server..." -ForegroundColor Cyan
    Push-Location frontend-web
    npm run dev
    Pop-Location
}
