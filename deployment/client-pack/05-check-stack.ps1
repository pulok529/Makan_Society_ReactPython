$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

Write-Host "Docker services"
if (Test-Path "$root\docker-compose.images.yml") {
  docker compose -f docker-compose.images.yml ps
} else {
  docker compose ps
}

Write-Host ""
Write-Host "Frontend check"
try {
  (Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 10).StatusCode
} catch {
  Write-Host $_.Exception.Message
}

Write-Host ""
Write-Host "API check"
try {
  (Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 10).StatusCode
} catch {
  Write-Host $_.Exception.Message
}
