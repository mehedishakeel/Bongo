# Bongo for Windows - One-Command PowerShell Installer
# Usage: powershell -c "irm https://raw.githubusercontent.com/mehedishakeel/Bongo/main/platforms/windows/scripts/install.ps1 | iex"

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "           Bongo Windows Installation             " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$InstallerUrl = "https://github.com/mehedishakeel/Bongo/releases/latest/download/Bongo-Setup-1.1.0.exe"
$TempInstaller = Join-Path $env:TEMP "Bongo-Setup-1.1.0.exe"

Write-Host "--> Downloading Bongo Setup from GitHub..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $InstallerUrl -OutFile $TempInstaller -UseBasicParsing

Write-Host "--> Launching Bongo Setup..." -ForegroundColor Green
Start-Process -FilePath $TempInstaller -ArgumentList "/VERYSILENT", "/NORESTART" -Wait

Write-Host "--> Bongo for Windows installed successfully!" -ForegroundColor Green
Write-Host "--> Press F12 anywhere to toggle between English and Bangla." -ForegroundColor Cyan
