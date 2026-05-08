$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

Write-Host "Stopping Docker stack"
if (Test-Path "$root\docker-compose.images.yml") {
  docker compose -f docker-compose.images.yml down
} else {
  docker compose down
}
Write-Host "Done."
