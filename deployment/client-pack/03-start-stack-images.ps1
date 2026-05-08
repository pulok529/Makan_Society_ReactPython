$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

Write-Host "Starting Docker stack from exported images"
docker compose -f docker-compose.images.yml up -d
Write-Host "Done."
