param(
  [string]$OutputFile = "society-modern-images.tar"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

$images = @(
  "society-modern-api",
  "society-modern-frontend",
  "society-modern-worker",
  "redis:7-alpine",
  "mcr.microsoft.com/mssql/server:2022-latest"
)

Write-Host "Exporting Docker images to $OutputFile"
docker save -o $OutputFile @images
Write-Host "Done."
