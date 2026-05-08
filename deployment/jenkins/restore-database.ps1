param(
  [string]$BackupFile,
  [string]$ProjectRoot = "C:\deploy\makan-society",
  [string]$ComposeFile = "docker-compose.deploy.yml",
  [string]$ContainerName = "society-modern-mssql",
  [string]$DatabaseName = "SocietyApp",
  [string]$SaPassword = "",
  [string]$LogicalDataName = "BroadBandDB",
  [string]$LogicalLogName = "BroadBandDB_log"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($SaPassword)) {
  throw "Provide -SaPassword."
}

if ([string]::IsNullOrWhiteSpace($BackupFile)) {
  throw "Provide -BackupFile."
}

if (-not (Test-Path $BackupFile)) {
  throw "Backup file not found: $BackupFile"
}

Set-Location $ProjectRoot

Write-Host "Starting SQL Server container"
docker compose -f $ComposeFile up -d mssql

Write-Host "Waiting for SQL Server to become healthy"
Start-Sleep -Seconds 25

$backupName = Split-Path $BackupFile -Leaf
$containerBackupPath = "/var/opt/mssql/backup/$backupName"

Write-Host "Copying backup to container"
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

Write-Host "Restoring database"
docker exec $ContainerName /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P $SaPassword -C -Q $restoreSql

Write-Host "Database restore completed."
