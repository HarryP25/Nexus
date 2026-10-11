import uuid

from django.db import models


class NexusUser(models.Model):
    unique_id = models.UUIDField(primary_key=True, db_column="uniqueID", default=uuid.uuid4)
    username = models.CharField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255, db_column="passwordHash")
    created_at = models.DateTimeField(db_column="createdAt")

    class Meta:
        managed = False
        db_table = "[dbo].[NexusUsers]"


class AuthSession(models.Model):
    session_id = models.UUIDField(primary_key=True, db_column="sessionID", default=uuid.uuid4)
    user = models.ForeignKey(
        NexusUser,
        db_column="userUniqueID",
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        db_constraint=False,
        related_name="api_sessions",
    )
    token_hash = models.CharField(max_length=64, db_column="tokenHash", unique=True)
    csrf_token = models.CharField(max_length=128, db_column="csrfToken")
    created_at = models.DateTimeField(db_column="createdAt")
    expires_at = models.DateTimeField(db_column="expiresAt", db_index=True)

    class Meta:
        managed = False
        db_table = "[dbo].[NexusSessions]"
