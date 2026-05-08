param(
  [string]$OutputFolder = "client-deployment-output"
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$packRoot = Join-Path $root $OutputFolder

if (Test-Path $packRoot) {
  Remove-Item -Recurse -Force $packRoot
}

New-Item -ItemType Directory -Force -Path $packRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packRoot "backups") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packRoot "deployment\client-pack") | Out-Null

Write-Host "Copying project files"
Copy-Item "$root\docker-compose.yml" $packRoot
if (Test-Path "$root\docker-compose.images.yml") {
  Copy-Item "$root\docker-compose.images.yml" $packRoot
}
Copy-Item "$root\README.md" $packRoot
Copy-Item "$root\.env.example" (Join-Path $packRoot ".env.client.template")

robocopy "$root\backend" (Join-Path $packRoot "backend") /E /XD "__pycache__" ".pytest_cache" ".mypy_cache" | Out-Null
robocopy "$root\frontend" (Join-Path $packRoot "frontend") /E /XD "node_modules" "dist" | Out-Null
if (Test-Path "$root\infra") {
  robocopy "$root\infra" (Join-Path $packRoot "infra") /E | Out-Null
}

Write-Host "Copying deployment scripts"
Copy-Item "$PSScriptRoot\*" (Join-Path $packRoot "deployment\client-pack") -Recurse -Force

$latestBackup = Get-ChildItem "$root\backups\*.bak" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($latestBackup) {
  Write-Host "Copying latest backup: $($latestBackup.Name)"
  Copy-Item $latestBackup.FullName (Join-Path $packRoot "backups\$($latestBackup.Name)")
}

Write-Host "Client pack ready at: $packRoot"
