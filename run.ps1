# Grocery Billing App PowerShell Runner
Set-Location -Path $PSScriptRoot

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "         Grocery Billing Web App (Windows)            " -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "[ERROR] Virtual environment not found in .venv." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Checking and applying database migrations..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" manage.py migrate --noinput

Write-Host "`n[2/3] Starting Model Vision Service on port 8001..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$PSScriptRoot'; & '.\.venv\Scripts\uvicorn.exe' model_service.main:app --host 0.0.0.0 --port 8001"

$localIp = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.IPAddress -notmatch '^169\.' } | Select-Object -First 1).IPAddress

Write-Host "`n=======================================================" -ForegroundColor Green
Write-Host "App is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "PC Browser:    http://localhost:8000" -ForegroundColor White
if ($localIp) {
    Write-Host "Phone Browser: http://${localIp}:8000" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Default Admin:" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor White
Write-Host "  Password: admin123" -ForegroundColor White
Write-Host "=======================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Starting Django Web Server on 0.0.0.0:8000 (Ctrl+C to stop)..." -ForegroundColor Cyan

& ".\.venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
