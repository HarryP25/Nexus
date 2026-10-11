from django.db import transaction

from apps.telemetry.models import MetricPoint, Site24x7Metric


SAMPLE_METRICS = [
    ("app-web-01", "CPU utilization", 42.0, "%", "Healthy"),
    ("app-web-01", "Memory usage", 68.4, "%", "Healthy"),
    ("app-web-01", "Availability", 99.98, "%", "Healthy"),
    ("app-web-01", "Response time", 184.0, "ms", "Healthy"),
    ("app-web-02", "CPU utilization", 57.0, "%", "Warning"),
    ("app-web-02", "Memory usage", 72.1, "%", "Healthy"),
    ("app-web-02", "Availability", 99.95, "%", "Healthy"),
    ("app-web-02", "Response time", 236.0, "ms", "Warning"),
    ("db-prod-01", "CPU utilization", 64.0, "%", "Warning"),
    ("db-prod-01", "Memory usage", 81.3, "%", "Warning"),
    ("db-prod-01", "Availability", 99.99, "%", "Healthy"),
    ("db-prod-01", "Response time", 92.0, "ms", "Healthy"),
]


@transaction.atomic
def seed_site24x7_metrics(datasource, recorded_at):
    if Site24x7Metric.objects.extra(
        where=["TRY_CONVERT(uniqueidentifier, datasourceID) = %s"],
        params=[str(datasource.unique_id)],
    ).exists():
        return
    old_rows = [
        Site24x7Metric(
            datasource_id=datasource.unique_id,
            host_name=host,
            metric_name=name,
            metric_value=value,
            unit=unit,
            status=status,
            recorded_at=recorded_at,
        )
        for host, name, value, unit, status in SAMPLE_METRICS
    ]
    Site24x7Metric.objects.bulk_create(old_rows)
    MetricPoint.objects.bulk_create([
        MetricPoint(
            datasource_id=datasource.unique_id,
            host_name=metric.host_name,
            metric_name=metric.metric_name,
            metric_value=metric.metric_value,
            unit=metric.unit,
            status=metric.status,
            recorded_at=metric.recorded_at,
        )
        for metric in old_rows
    ])
