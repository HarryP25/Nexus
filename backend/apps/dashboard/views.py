import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

from django.db.models import Avg, Count, Max, Min, Q, Sum, Case, When, Value, IntegerField
from django.db.models.functions import TruncDate, TruncHour, TruncWeek
from django.http import JsonResponse
from django.utils import timezone

from apps.accounts.services.sessions import require_authenticated_user
from apps.telemetry.models import MetricPoint
from apps.connections.services import user_datasources


MAX_RANGE = timedelta(days=366)


def parse_range(request):
    start_value = request.GET.get("start")
    end_value = request.GET.get("end")
    if not start_value and not end_value:
        end = timezone.now()
        return end - timedelta(hours=24), end, "Last 24 hours"
    if not start_value or not end_value:
        raise ValueError("Provide both start and end dates.")
    try:
        start_date = datetime.strptime(start_value, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_value, "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("Dates must use YYYY-MM-DD format.") from error
    if start_date > end_date:
        raise ValueError("Start date must be on or before the end date.")
    start = datetime.combine(start_date, datetime.min.time(), tzinfo=dt_timezone.utc)
    end = datetime.combine(end_date + timedelta(days=1), datetime.min.time(), tzinfo=dt_timezone.utc)
    if end - start > MAX_RANGE:
        raise ValueError("Date range cannot exceed 366 days.")
    return start, end, f"{start_date.isoformat()} to {end_date.isoformat()}"


@require_authenticated_user
def dashboard_overview(request):
    if request.method != "GET":
        return JsonResponse({"message": "Method not allowed."}, status=405)
    start, end, range_label = parse_range(request)
    source_ids = request.GET.getlist("source_id")
    try:
        source_ids = [uuid.UUID(source_id) for source_id in source_ids]
    except (ValueError, AttributeError) as error:
        raise ValueError("A source_id is not a valid UUID.") from error

    sources = list(user_datasources(request.current_user_id))
    if source_ids:
        source_id_set = set(source_ids)
        sources = [source for source in sources if source.unique_id in source_id_set]
    metric_query = MetricPoint.objects.filter(
        recorded_at__gte=start,
        recorded_at__lt=end,
    ).extra(where=[
        "TRY_CONVERT(uniqueidentifier, datasourceID) IN ("
        "SELECT TRY_CONVERT(uniqueidentifier, UniqueID) FROM dbo.NexusDataSources "
        "WHERE TRY_CONVERT(uniqueidentifier, ownerUniqueID) = %s)"
    ], params=[str(request.current_user_id)])
    if source_ids:
        if sources:
            placeholders = ", ".join(["%s"] * len(sources))
            metric_query = metric_query.extra(
                where=[f"TRY_CONVERT(uniqueidentifier, datasourceID) IN ({placeholders})"],
                params=[str(source.unique_id) for source in sources],
            )
        else:
            metric_query = metric_query.none()

    summary = metric_query.aggregate(
        measurement_count=Count("metric_id"),
        services_monitored=Count("host_name", distinct=True),
        active_alerts=Sum(
            Case(
                When(status__in=["Warning", "Critical"], then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ),
    )

    duration = end - start
    bucket_minutes = 60 if duration <= timedelta(days=2) else 1440 if duration <= timedelta(days=31) else 10080
    bucket_expression = TruncHour("recorded_at") if bucket_minutes == 60 else TruncDate("recorded_at") if bucket_minutes == 1440 else TruncWeek("recorded_at")
    rows = metric_query.annotate(bucket=bucket_expression).values("metric_name", "unit", "bucket").annotate(
        average=Avg("metric_value"),
        minimum=Min("metric_value"),
        maximum=Max("metric_value"),
        count=Count("metric_id"),
    ).order_by("bucket", "metric_name")

    series_by_key = {}
    for row in rows:
        key = (row["metric_name"], row["unit"])
        series = series_by_key.setdefault(key, {"name": row["metric_name"], "unit": row["unit"], "points": []})
        series["points"].append({
            "timestamp": row["bucket"].isoformat(sep=" ", timespec="seconds") if isinstance(row["bucket"], datetime) else datetime.combine(row["bucket"], datetime.min.time(), tzinfo=dt_timezone.utc).isoformat(sep=" ", timespec="seconds"),
            "average": round(float(row["average"]), 3),
            "minimum": round(float(row["minimum"]), 3),
            "maximum": round(float(row["maximum"]), 3),
            "count": row["count"],
        })

    return JsonResponse({
        "range": {
            "start": start.isoformat(sep=" ", timespec="seconds"),
            "endExclusive": end.isoformat(sep=" ", timespec="seconds"),
            "label": range_label,
            "bucketMinutes": bucket_minutes,
        },
        "generatedAt": timezone.now().isoformat(timespec="seconds"),
        "summary": {
            "dataSources": len(sources),
            "servicesMonitored": summary["services_monitored"] or 0,
            "activeAlerts": summary["active_alerts"] or 0,
            "measurementCount": summary["measurement_count"] or 0,
        },
        "series": list(series_by_key.values()),
    })
