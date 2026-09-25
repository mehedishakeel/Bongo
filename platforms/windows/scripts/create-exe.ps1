param([string]$Dcc32 = "dcc32.exe")
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "../../..")).Path
$project = Join-Path $root "platforms/windows/Keyboard and Spell checker"
if (-not (Get-Command $Dcc32 -ErrorAction SilentlyContinue)) {
  throw "Delphi 2010 dcc32 is required with DISQLite3, JCL and JVCL installed. Read docs/BUILDING.md."
}
$dccCommand = Get-Command $Dcc32
$brcc = Join-Path (Split-Path $dccCommand.Source) "brcc32.exe"
if (-not (Test-Path $brcc)) {
  throw "Delphi 2010 brcc32.exe was not found beside $($dccCommand.Source). Read docs/BUILDING.md."
}
$out = Join-Path $root "platforms/windows/release"
$build = Join-Path $root "platforms/windows/build"
New-Item -ItemType Directory -Force $out | Out-Null
New-Item -ItemType Directory -Force $build | Out-Null
Remove-Item (Join-Path $out "Bongo.exe") -Force -ErrorAction SilentlyContinue
Push-Location $project
try {
  & $brcc Bongo.rc
  if ($LASTEXITCODE -ne 0) { throw "Resource compilation failed" }
  & $Dcc32 -B "-E$out" "-N0$build" "-LE$build" "-LN$build" Bongo.dpr
  if ($LASTEXITCODE -ne 0) { throw "Delphi build failed ($LASTEXITCODE)" }
} finally { Pop-Location }
Write-Host "Created platforms/windows/release/Bongo.exe. Complete the runtime-data checklist before release."
