from django.db import migrations


ADOPT_NEXUS_SCHEMA = """
IF OBJECT_ID('dbo.NexusUsers', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NexusUsers (
        uniqueID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        username NVARCHAR(100) NOT NULL UNIQUE,
        passwordHash NVARCHAR(255) NOT NULL,
        createdAt DATETIME2 NOT NULL
    )
END
IF OBJECT_ID('dbo.NexusDataSources', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NexusDataSources (
        UniqueID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        ownerUniqueID UNIQUEIDENTIFIER NOT NULL,
        displayName NVARCHAR(150) NOT NULL,
        provider NVARCHAR(100) NOT NULL,
        endpoint NVARCHAR(500) NOT NULL,
        logoUrl NVARCHAR(500) NULL,
        settingsJson NVARCHAR(MAX) NULL,
        secretsEncrypted NVARCHAR(MAX) NULL,
        CATO_API_URL NVARCHAR(500) NULL,
        CATO_API_KEY NVARCHAR(500) NULL,
        CATO_ACCOUNT_ID NVARCHAR(100) NULL,
        CATO_SITE_IDS NVARCHAR(MAX) NULL,
        SITE24X7_ENDPOINT NVARCHAR(500) NULL,
        SITE24X7_ACCESS_TOKEN NVARCHAR(500) NULL,
        SOLARWINDS_ENDPOINT NVARCHAR(500) NULL,
        SOLARWINDS_USERNAME NVARCHAR(255) NULL,
        SOLARWINDS_PASSWORD NVARCHAR(500) NULL,
        createdAt DATETIME2 NOT NULL,
        updatedAt DATETIME2 NOT NULL,
        CONSTRAINT FK_NexusDataSources_NexusUsers FOREIGN KEY (ownerUniqueID)
            REFERENCES dbo.NexusUsers(uniqueID)
    )
END
IF COL_LENGTH('dbo.NexusDataSources', 'UniqueID') IS NULL
   AND COL_LENGTH('dbo.NexusDataSources', 'datasourceID') IS NOT NULL
    EXEC sp_rename 'dbo.NexusDataSources.datasourceID', 'UniqueID', 'COLUMN'
IF COL_LENGTH('dbo.NexusDataSources', 'logoUrl') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD logoUrl NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'settingsJson') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD settingsJson NVARCHAR(MAX) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'secretsEncrypted') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD secretsEncrypted NVARCHAR(MAX) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'CATO_API_URL') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD CATO_API_URL NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'CATO_API_KEY') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD CATO_API_KEY NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'CATO_ACCOUNT_ID') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD CATO_ACCOUNT_ID NVARCHAR(100) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'CATO_SITE_IDS') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD CATO_SITE_IDS NVARCHAR(MAX) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'SITE24X7_ENDPOINT') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD SITE24X7_ENDPOINT NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'SITE24X7_ACCESS_TOKEN') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD SITE24X7_ACCESS_TOKEN NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'SOLARWINDS_ENDPOINT') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD SOLARWINDS_ENDPOINT NVARCHAR(500) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'SOLARWINDS_USERNAME') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD SOLARWINDS_USERNAME NVARCHAR(255) NULL
IF COL_LENGTH('dbo.NexusDataSources', 'SOLARWINDS_PASSWORD') IS NULL
    ALTER TABLE dbo.NexusDataSources ADD SOLARWINDS_PASSWORD NVARCHAR(500) NULL
IF OBJECT_ID('dbo.NexusSite24x7Metrics', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NexusSite24x7Metrics (
        metricID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        datasourceID UNIQUEIDENTIFIER NOT NULL,
        hostName NVARCHAR(150) NOT NULL,
        metricName NVARCHAR(100) NOT NULL,
        metricValue FLOAT NOT NULL,
        unit NVARCHAR(30) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        recordedAt DATETIME2 NOT NULL,
        CONSTRAINT FK_NexusSite24x7Metrics_NexusDataSources
            FOREIGN KEY (datasourceID) REFERENCES dbo.NexusDataSources(UniqueID) ON DELETE CASCADE
    )
END
IF OBJECT_ID('dbo.NexusSessions', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NexusSessions (
        sessionID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        userUniqueID UNIQUEIDENTIFIER NULL,
        tokenHash VARCHAR(64) NOT NULL,
        csrfToken NVARCHAR(128) NOT NULL,
        createdAt DATETIME2 NOT NULL,
        expiresAt DATETIME2 NOT NULL,
        CONSTRAINT FK_NexusSessions_NexusUsers FOREIGN KEY (userUniqueID)
            REFERENCES dbo.NexusUsers(uniqueID) ON DELETE CASCADE,
        CONSTRAINT UQ_NexusSessions_tokenHash UNIQUE (tokenHash)
    )
END
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_NexusSessions_expiresAt'
      AND object_id = OBJECT_ID('dbo.NexusSessions')
)
    CREATE INDEX IX_NexusSessions_expiresAt ON dbo.NexusSessions(expiresAt)
"""


class Migration(migrations.Migration):
    initial = True
    atomic = False
    dependencies = []
    operations = [migrations.RunSQL(ADOPT_NEXUS_SCHEMA, migrations.RunSQL.noop)]
