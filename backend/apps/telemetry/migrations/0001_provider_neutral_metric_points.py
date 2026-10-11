from django.db import migrations


CREATE_METRIC_POINTS = """
IF OBJECT_ID('dbo.NexusMetricPoints', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.NexusMetricPoints (
        metricID UNIQUEIDENTIFIER NOT NULL PRIMARY KEY,
        datasourceID UNIQUEIDENTIFIER NOT NULL,
        hostName NVARCHAR(150) NOT NULL,
        metricName NVARCHAR(150) NOT NULL,
        metricValue FLOAT NOT NULL,
        unit NVARCHAR(32) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        recordedAt DATETIME2 NOT NULL,
        dimensionsJson NVARCHAR(MAX) NULL,
        CONSTRAINT FK_NexusMetricPoints_NexusDataSources
            FOREIGN KEY (datasourceID) REFERENCES dbo.NexusDataSources(UniqueID) ON DELETE CASCADE
    )
END
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_NexusMetricPoints_source_recorded'
      AND object_id = OBJECT_ID('dbo.NexusMetricPoints')
)
    CREATE INDEX IX_NexusMetricPoints_source_recorded
        ON dbo.NexusMetricPoints(datasourceID, recordedAt)
IF NOT EXISTS (
    SELECT 1 FROM sys.indexes
    WHERE name = 'IX_NexusMetricPoints_name_recorded'
      AND object_id = OBJECT_ID('dbo.NexusMetricPoints')
)
    CREATE INDEX IX_NexusMetricPoints_name_recorded
        ON dbo.NexusMetricPoints(metricName, recordedAt)
IF OBJECT_ID('dbo.NexusSite24x7Metrics', 'U') IS NOT NULL
BEGIN
    INSERT INTO dbo.NexusMetricPoints
        (metricID, datasourceID, hostName, metricName, metricValue, unit, status, recordedAt)
    SELECT old.metricID, old.datasourceID, old.hostName, old.metricName,
           old.metricValue, old.unit, old.status, old.recordedAt
    FROM dbo.NexusSite24x7Metrics AS old
    WHERE NOT EXISTS (
        SELECT 1 FROM dbo.NexusMetricPoints AS current_metric
        WHERE current_metric.metricID = old.metricID
    )
END
"""


class Migration(migrations.Migration):
    initial = True
    atomic = False
    dependencies = [("accounts", "0001_adopt_nexus_schema")]
    operations = [migrations.RunSQL(CREATE_METRIC_POINTS, migrations.RunSQL.noop)]
