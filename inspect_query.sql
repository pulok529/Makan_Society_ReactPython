SET NOCOUNT ON;
SELECT name, create_date FROM sys.databases WHERE name = N'SocietyAppInspect';
SELECT COUNT(*) AS member_count FROM [SocietyAppInspect].[society].[members];
