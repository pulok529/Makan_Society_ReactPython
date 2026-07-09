IF DB_ID(N'SocietyAppInspect') IS NOT NULL
BEGIN
  ALTER DATABASE [SocietyAppInspect] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
  DROP DATABASE [SocietyAppInspect];
END;
RESTORE DATABASE [SocietyAppInspect]
FROM DISK = N'/var/opt/mssql/backup/SocietyApp_corrected_20260509_235843.bak'
WITH REPLACE,
MOVE N'BroadBandDB' TO N'/var/opt/mssql/data/SocietyAppInspect.mdf',
MOVE N'BroadBandDB_log' TO N'/var/opt/mssql/data/SocietyAppInspect_log.ldf';
