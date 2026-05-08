param(
  [string]$BackupFile = "",
  [string]$ContainerName = "society-modern-mssql",
  [string]$DatabaseName = "SocietyApp",
  [string]$SaPassword = "SocietyDev@2026!",
  [string]$LogicalDataName = "BroadBandDB",
  [string]$LogicalLogName = "BroadBandDB_log"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

if ([string]::IsNullOrWhiteSpace($BackupFile)) {
  $backup = Get-ChildItem "$root\backups\*.bak" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $backup) {
    throw "No backup file found in $root\backups"
  }
  $BackupFile = $backup.FullName
}

if (-not (Test-Path $BackupFile)) {
  throw "Backup file not found: $BackupFile"
}

$backupName = Split-Path $BackupFile -Leaf
$containerBackupPath = "/var/opt/mssql/backup/$backupName"

Write-Host "Copying backup into SQL container"
docker cp $BackupFile "${ContainerName}:$containerBackupPath"

$restoreSql = @"
IF DB_ID(N'$DatabaseName') IS NOT NULL
BEGIN
  ALTER DATABASE [$DatabaseName] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
END;
RESTORE DATABASE [$DatabaseName]
FROM DISK = N'$containerBackupPath'
WITH REPLACE,
MOVE N'$LogicalDataName' TO N'/var/opt/mssql/data/$DatabaseName.mdf',
MOVE N'$LogicalLogName' TO N'/var/opt/mssql/data/${DatabaseName}_log.ldf';
ALTER DATABASE [$DatabaseName] SET MULTI_USER;
"@

Write-Host "Restoring database $DatabaseName"
docker exec $ContainerName /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $SaPassword -C -Q $restoreSql
Write-Host "Done."
