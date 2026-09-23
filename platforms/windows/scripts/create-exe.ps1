param([string]$Dcc32 = "dcc32.exe")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
$project = Join-Path $root "platforms/windows/Keyboard and Spell checker"
if (-not (Get-Command $Dcc32 -ErrorAction SilentlyContinue)) {
  throw "Delphi 2010 dcc32 is required with DISQLite3, ICS, JCL and JVCL installed. Read docs/WINDOWS-RELEASE.md."
}
$out = Join-Path $root "dist/windows"
New-Item -ItemType Directory -Force $out | Out-Null
Push-Location $project
try {
  $brcc = Join-Path (Split-Path (Get-Command $Dcc32).Source) "brcc32.exe"
  & $brcc Bongo.rc
  if ($LASTEXITCODE -ne 0) { throw "Resource compilation failed" }
  & $Dcc32 -B "-E$out" Bongo.dpr
  if ($LASTEXITCODE -ne 0) { throw "Delphi build failed ($LASTEXITCODE)" }
} finally { Pop-Location }
Write-Host "Created dist/windows/Bongo.exe. Complete the runtime-data checklist before release."
