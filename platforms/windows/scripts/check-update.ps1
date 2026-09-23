param(
  [string]$Repository = $env:BONGO_GITHUB_REPOSITORY,
  [string]$CurrentVersion = "1.0",
  [switch]$Open
)
$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($Repository)) {
  throw "Set BONGO_GITHUB_REPOSITORY to owner/Bongo, or pass -Repository owner/Bongo."
}
$headers = @{ Accept = "application/vnd.github+json"; "User-Agent" = "Bongo-Windows" }
$release = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Repository/releases/latest"
$latest = $release.tag_name -replace '^[vV]', ''
if ([version]$latest -gt [version]$CurrentVersion) {
  Write-Host "Bongo $latest is available: $($release.html_url)"
  if ($Open) { Start-Process $release.html_url }
  exit 10
}
Write-Host "Bongo $CurrentVersion is up to date."
