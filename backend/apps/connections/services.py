import json

from django.utils import timezone

from apps.connections.models import DataSource
from integrations.credentials import encrypt_secret_value
from integrations.registry import validate_provider_payload


def user_datasources(user_id):
    """Read legacy datasource rows safely when GUID columns are stored as text."""
    return DataSource.objects.raw(
        """
        SELECT *
        FROM dbo.NexusDataSources
        WHERE TRY_CONVERT(uniqueidentifier, ownerUniqueID) = %s
          AND TRY_CONVERT(uniqueidentifier, UniqueID) IS NOT NULL
        ORDER BY updatedAt DESC
        """,
        [str(user_id)],
    )


def user_datasource(user_id, datasource_id):
    rows = DataSource.objects.raw(
        """
        SELECT *
        FROM dbo.NexusDataSources
        WHERE TRY_CONVERT(uniqueidentifier, ownerUniqueID) = %s
          AND TRY_CONVERT(uniqueidentifier, UniqueID) = %s
        """,
        [str(user_id), str(datasource_id)],
    )
    return next(iter(rows), None)


def text_value(value):
    return value.strip() if isinstance(value, str) else ""


def serialize_datasource(datasource):
    settings_data = {}
    if datasource.provider == "Cato":
        settings_data = {"accountId": datasource.cato_account_id, "siteIds": datasource.cato_site_ids}
    return {
        "id": str(datasource.unique_id),
        "databaseId": True,
        "name": datasource.display_name,
        "type": datasource.provider,
        "endpoint": datasource.endpoint,
        "logoUrl": datasource.logo_url,
        "settings": settings_data,
        "configuredAt": timezone.localtime(datasource.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
        "demoData": {"hosts": 3, "metrics": 12, "status": "Demo data imported"},
    }


def validate_datasource_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    name = text_value(payload.get("name"))
    provider = text_value(payload.get("provider"))
    endpoint = text_value(payload.get("endpoint"))
    if not name or not provider:
        raise ValueError("Name and provider are required.")
    if len(name) > 150 or len(provider) > 100 or len(endpoint) > 500:
        raise ValueError("One or more connection fields exceed the allowed length.")

    return validate_provider_payload(provider, endpoint, payload, name)


def persist_datasource(validated, user, existing=None):
    name, provider, endpoint, secret, secondary_secret, site_ids, payload = validated
    now = timezone.now()
    datasource = existing or DataSource(owner=user, created_at=now)
    datasource.owner = user
    datasource.display_name = name
    datasource.provider = provider
    datasource.endpoint = endpoint
    datasource.logo_url = payload.get("logoUrl") or None
    datasource.settings_json = json.dumps(payload.get("settings") or {})
    datasource.updated_at = now

    if provider == "Cato":
        datasource.cato_api_url = endpoint
        datasource.cato_api_key = encrypt_secret_value(secret)
        datasource.cato_account_id = secondary_secret
        datasource.cato_site_ids = site_ids
    elif provider == "Site24x7":
        datasource.site24x7_endpoint = endpoint
        datasource.site24x7_access_token = encrypt_secret_value(secret)
    elif provider == "Solarwinds":
        datasource.solarwinds_endpoint = endpoint
        datasource.solarwinds_username = encrypt_secret_value(secret)
        datasource.solarwinds_password = encrypt_secret_value(secondary_secret)
    datasource.save()
    return datasource
