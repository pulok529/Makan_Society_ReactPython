param(
  [string]$InputFile = "society-modern-images.tar"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $InputFile)) {
  throw "Image archive not found: $InputFile"
}

Write-Host "Loading Docker images from $InputFile"
docker load -i $InputFile
Write-Host "Done."
