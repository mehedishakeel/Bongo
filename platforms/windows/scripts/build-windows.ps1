# Bongo Windows Packaging Script in PowerShell
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$windowsRoot = [System.IO.Path]::GetFullPath("$scriptDir\..")
$projectRoot = [System.IO.Path]::GetFullPath("$windowsRoot\..\..")
$buildDir = "$windowsRoot\build"
$releaseDir = "$windowsRoot\release"
$issPath = "$windowsRoot\installer\bongo.iss"
$wxsPath = "$windowsRoot\installer\bongo.wxs"

if (-not (Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir -Force | Out-Null }
if (-not (Test-Path $releaseDir)) { New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null }

Write-Host "=== Bongo Windows Release Packaging ==="
Write-Host "Windows Root: $windowsRoot"
Write-Host "Release Dir:  $releaseDir"

# 1. Build Inno Setup Installer
Write-Host "[1/3] Building Inno Setup EXE installer..."
$iscc = $null
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
foreach ($c in $isccCandidates) {
    if (Test-Path $c -ErrorAction SilentlyContinue) {
        $iscc = $c
        break
    }
}
if (-not $iscc) {
    $cmd = Get-Command "iscc.exe" -ErrorAction SilentlyContinue
    if ($cmd) { $iscc = $cmd.Source }
}

if ($iscc) {
    Write-Host "Compiling with Inno Setup: $iscc"
    Push-Location "$windowsRoot\installer"
    & "$iscc" /O"$releaseDir" "$issPath"
    Pop-Location
    Write-Host "Inno Setup compilation finished."
} else {
    Write-Warning "Inno Setup compiler (ISCC.exe) not found."
}

# 2. Build WiX MSI Package
Write-Host "[2/3] Building WiX MSI installer..."
$wix = $null
$wixCandidates = @(
    "$env:ProgramFiles\WiX Toolset v7.0\bin\wix.exe",
    "$env:ProgramFiles\WiX Toolset v4\bin\wix.exe"
)
foreach ($w in $wixCandidates) {
    if (Test-Path $w -ErrorAction SilentlyContinue) {
        $wix = $w
        break
    }
}
if (-not $wix) {
    $cmd = Get-Command "wix.exe" -ErrorAction SilentlyContinue
    if ($cmd) { $wix = $cmd.Source }
}

if ($wix) {
    Write-Host "Compiling with WiX: $wix"
    Push-Location "$windowsRoot\installer"
    & "$wix" build -arch x64 -o "$releaseDir\Bongo-1.1.0-x64.msi" "$wxsPath"
    Pop-Location
    Write-Host "WiX compilation finished."
} else {
    $candle = Get-Command candle.exe -ErrorAction SilentlyContinue
    $light = Get-Command light.exe -ErrorAction SilentlyContinue
    if ($candle -and $light) {
        Push-Location "$windowsRoot\installer"
        & candle.exe -arch x64 -out "$buildDir\bongo.wixobj" "$wxsPath"
        & light.exe -ext WixUIExtension -out "$releaseDir\Bongo-1.1.0-x64.msi" "$buildDir\bongo.wixobj"
        Pop-Location
        Write-Host "WiX v3 compilation finished."
    } else {
        Write-Warning "WiX toolset not found."
    }
}

# 3. Build Portable ZIP Package
Write-Host "[3/4] Creating Portable ZIP package..."
$portableDir = "$buildDir\Bongo-Portable"
if (Test-Path $portableDir) { Remove-Item -Recurse -Force $portableDir }
New-Item -ItemType Directory -Path "$portableDir\data" -Force | Out-Null

if (Test-Path "$buildDir\bongo.exe") { Copy-Item "$buildDir\bongo.exe" "$portableDir\" }
if (Test-Path "$buildDir\bongo-settings.exe") { Copy-Item "$buildDir\bongo-settings.exe" "$portableDir\" }
if (Test-Path "$buildDir\bongo_engine.dll") { Copy-Item "$buildDir\bongo_engine.dll" "$portableDir\" }
if (Test-Path "$windowsRoot\data") { Copy-Item "$windowsRoot\data\*" "$portableDir\data\" }
if (Test-Path "$projectRoot\LICENSE") { Copy-Item "$projectRoot\LICENSE" "$portableDir\" }
if (Test-Path "$projectRoot\THIRD_PARTY_NOTICES.md") { Copy-Item "$projectRoot\THIRD_PARTY_NOTICES.md" "$portableDir\" }

$zipPath = "$releaseDir\Bongo-1.1.0-windows-portable.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path "$portableDir\*" -DestinationPath $zipPath -Force
Write-Host "Portable ZIP created: $zipPath"

# 4. Generate SHA256 Checksums
Write-Host "[4/4] Generating SHA256 checksums..."
Get-ChildItem -Path $releaseDir -Filter "*.exe" | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    Set-Content -Path ($_.FullName + ".sha256") -Value "$hash  $($_.Name)"
    Write-Host "  $($_.Name) -> $hash"
}
Get-ChildItem -Path $releaseDir -Filter "*.msi" | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    Set-Content -Path ($_.FullName + ".sha256") -Value "$hash  $($_.Name)"
    Write-Host "  $($_.Name) -> $hash"
}
Get-ChildItem -Path $releaseDir -Filter "*.zip" | ForEach-Object {
    $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
    Set-Content -Path ($_.FullName + ".sha256") -Value "$hash  $($_.Name)"
    Write-Host "  $($_.Name) -> $hash"
}

Write-Host "=== Packaging Complete ==="
