import uuid

from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone

from apps.accounts.models import NexusUser
from apps.accounts.services.sessions import require_authenticated_user
from api.http import method_not_allowed, read_json_object
from apps.connections.services import persist_datasource, serialize_datasource, user_datasource, user_datasources, validate_datasource_payload
from apps.telemetry.models import Site24x7Metric
from apps.telemetry.services import seed_site24x7_metrics


@require_authenticated_user
def list_or_create_datasources(request):
    if request.method == "GET":
        rows = user_datasources(request.current_user_id)
        return JsonResponse({"datasources": [serialize_datasource(row) for row in rows]})
    if request.method != "POST":
        return method_not_allowed(["GET", "POST"])

    user = NexusUser.objects.get(unique_id=request.current_user_id)
    validated = validate_datasource_payload(read_json_object(request))
    with transaction.atomic():
        datasource = persist_datasource(validated, user)
        if datasource.provider == "Site24x7":
            seed_site24x7_metrics(datasource, timezone.now())
    return JsonResponse({"datasource": serialize_datasource(datasource)}, status=201)


@require_authenticated_user
def datasource_detail(request, datasource_id):
    try:
        datasource_id = uuid.UUID(str(datasource_id))
    except ValueError as error:
        raise ValueError("Data source ID must be a valid UUID.") from error
    datasource = user_datasource(request.current_user_id, datasource_id)
    if not datasource:
        return JsonResponse({"message": "Data source was not found."}, status=404)

    if request.method == "PUT":
        user = NexusUser.objects.get(unique_id=request.current_user_id)
        validated = validate_datasource_payload(read_json_object(request))
        datasource = persist_datasource(validated, user, existing=datasource)
        return JsonResponse({"datasource": serialize_datasource(datasource)})
    if request.method == "DELETE":
        datasource.delete()
        return JsonResponse({"message": "Data source deleted."})
    return method_not_allowed(["PUT", "DELETE"])


@require_authenticated_user
def analyse_datasource(request, datasource_id):
    if request.method != "GET":
        return method_not_allowed(["GET"])
    datasource = user_datasource(request.current_user_id, datasource_id)
    if not datasource:
        return JsonResponse({"message": "Data source was not found."}, status=404)
    if datasource.provider != "Site24x7":
        return JsonResponse({"message": "Analysis is currently available for Site24x7 data sources."}, status=400)

    seed_site24x7_metrics(datasource, timezone.now())
    metrics = Site24x7Metric.objects.extra(
        where=["TRY_CONVERT(uniqueidentifier, datasourceID) = %s"],
        params=[str(datasource.unique_id)],
    ).order_by("host_name", "metric_name")
    return JsonResponse({
        "datasource": {"id": str(datasource.unique_id), "name": datasource.display_name},
        "metrics": [
            {
                "host": metric.host_name,
                "name": metric.metric_name,
                "value": metric.metric_value,
                "unit": metric.unit,
                "status": metric.status,
                "recordedAt": timezone.localtime(metric.recorded_at).strftime("%Y-%m-%d %H:%M:%S"),
            }
            for metric in metrics
        ],
    })
