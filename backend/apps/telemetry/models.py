import uuid

from django.db import models

from apps.connections.models import DataSource


class Site24x7Metric(models.Model):
    metric_id = models.UUIDField(primary_key=True, db_column="metricID", default=uuid.uuid4)
    datasource = models.ForeignKey(
        DataSource, db_column="datasourceID", on_delete=models.DO_NOTHING,
        db_constraint=False, related_name="site24x7_metrics",
    )
    host_name = models.CharField(max_length=150, db_column="hostName")
    metric_name = models.CharField(max_length=100, db_column="metricName")
    metric_value = models.FloatField(db_column="metricValue")
    unit = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    recorded_at = models.DateTimeField(db_column="recordedAt")

    class Meta:
        managed = False
        db_table = "[dbo].[NexusSite24x7Metrics]"


class MetricPoint(models.Model):
    metric_id = models.UUIDField(primary_key=True, db_column="metricID", default=uuid.uuid4)
    datasource = models.ForeignKey(
        DataSource, db_column="datasourceID", on_delete=models.DO_NOTHING,
        db_constraint=False, related_name="metric_points",
    )
    host_name = models.CharField(max_length=150, db_column="hostName")
    metric_name = models.CharField(max_length=150, db_column="metricName")
    metric_value = models.FloatField(db_column="metricValue")
    unit = models.CharField(max_length=32)
    status = models.CharField(max_length=30)
    recorded_at = models.DateTimeField(db_column="recordedAt")
    dimensions_json = models.TextField(null=True, blank=True, db_column="dimensionsJson")

    class Meta:
        managed = False
        db_table = "[dbo].[NexusMetricPoints]"
        indexes = [
            models.Index(fields=["datasource", "recorded_at"], name="IX_NMP_source_time"),
            models.Index(fields=["metric_name", "recorded_at"], name="IX_NMP_name_time"),
        ]
