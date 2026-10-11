import uuid

from django.db import models

from apps.accounts.models import NexusUser


class DataSource(models.Model):
    unique_id = models.UUIDField(primary_key=True, db_column="UniqueID", default=uuid.uuid4)
    owner = models.ForeignKey(
        NexusUser,
        db_column="ownerUniqueID",
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="datasources",
    )
    display_name = models.CharField(max_length=150, db_column="displayName")
    provider = models.CharField(max_length=100)
    endpoint = models.CharField(max_length=500)
    logo_url = models.CharField(max_length=500, null=True, blank=True, db_column="logoUrl")
    settings_json = models.TextField(null=True, blank=True, db_column="settingsJson")
    secrets_encrypted = models.TextField(null=True, blank=True, db_column="secretsEncrypted")
    cato_api_url = models.CharField(max_length=500, null=True, blank=True, db_column="CATO_API_URL")
    cato_api_key = models.CharField(max_length=500, null=True, blank=True, db_column="CATO_API_KEY")
    cato_account_id = models.CharField(max_length=100, null=True, blank=True, db_column="CATO_ACCOUNT_ID")
    cato_site_ids = models.TextField(null=True, blank=True, db_column="CATO_SITE_IDS")
    site24x7_endpoint = models.CharField(max_length=500, null=True, blank=True, db_column="SITE24X7_ENDPOINT")
    site24x7_access_token = models.CharField(max_length=500, null=True, blank=True, db_column="SITE24X7_ACCESS_TOKEN")
    solarwinds_endpoint = models.CharField(max_length=500, null=True, blank=True, db_column="SOLARWINDS_ENDPOINT")
    solarwinds_username = models.CharField(max_length=255, null=True, blank=True, db_column="SOLARWINDS_USERNAME")
    solarwinds_password = models.CharField(max_length=500, null=True, blank=True, db_column="SOLARWINDS_PASSWORD")
    created_at = models.DateTimeField(db_column="createdAt")
    updated_at = models.DateTimeField(db_column="updatedAt")

    class Meta:
        managed = False
        db_table = "[dbo].[NexusDataSources]"
