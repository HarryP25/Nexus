import hashlib
import hmac
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import AuthSession


def valid_user_id(value):
    """Return a normalized UUID, or None for stale/malformed legacy session data."""
    if value is None:
        return None
    try:
        return uuid.UUID(str(value))
    except (AttributeError, TypeError, ValueError):
        return None


def _replace_session_row(auth_session, user, raw_token, csrf_token, now):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE dbo.NexusSessions
            SET userUniqueID = TRY_CONVERT(uniqueidentifier, %s),
                tokenHash = %s,
                csrfToken = %s,
                createdAt = %s,
                expiresAt = %s
            WHERE tokenHash = %s
            """,
            [
                str(user.unique_id) if user is not None else None,
                hash_token(raw_token),
                csrf_token,
                now.replace(tzinfo=None),
                (now + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS)).replace(tzinfo=None),
                auth_session.token_hash,
            ],
        )
        return cursor.rowcount


def hash_token(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_request_session(request):
    raw_token = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
    if not raw_token:
        return None
    auth_session = AuthSession.objects.filter(token_hash=hash_token(raw_token)).first()
    if auth_session and auth_session.expires_at <= timezone.now():
        auth_session.delete()
        return None
    return auth_session


def issue_session(user=None, replacing=None):
    now = timezone.now()
    raw_token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    with transaction.atomic():
        AuthSession.objects.filter(expires_at__lte=now).delete()
        if replacing is not None:
            # Reuse the row and explicitly convert the UUID input on SQL Server.
            # The ORM's FK update can trigger a text-to-UUID conversion failure.
            updated = _replace_session_row(replacing, user, raw_token, csrf_token, now)
            if updated != 1:
                raise RuntimeError("The current session could not be replaced.")
            auth_session = replacing
            auth_session.user = user
            auth_session.token_hash = hash_token(raw_token)
            auth_session.csrf_token = csrf_token
            auth_session.created_at = now
            auth_session.expires_at = now + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS)
        else:
            session_id = uuid.uuid4()
            expires_at = now + timedelta(seconds=settings.SESSION_LIFETIME_SECONDS)
            token_hash = hash_token(raw_token)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dbo.NexusSessions
                        (sessionID, userUniqueID, tokenHash, csrfToken, createdAt, expiresAt)
                    VALUES
                        (TRY_CONVERT(uniqueidentifier, %s),
                         TRY_CONVERT(uniqueidentifier, %s), %s, %s, %s, %s)
                    """,
                    [
                        str(session_id),
                        str(user.unique_id) if user is not None else None,
                        token_hash,
                        csrf_token,
                        now.replace(tzinfo=None),
                        expires_at.replace(tzinfo=None),
                    ],
                )
            auth_session = AuthSession(
                session_id=session_id,
                user=user,
                token_hash=token_hash,
                csrf_token=csrf_token,
                created_at=now,
                expires_at=expires_at,
            )
    return auth_session, raw_token, csrf_token


def rotate_session_to_anonymous(auth_session):
    """Revoke an authenticated token and keep the same DB row for the next login."""
    if auth_session is None:
        raise RuntimeError("There is no active session to sign out.")

    now = timezone.now()
    raw_token = secrets.token_urlsafe(48)
    csrf_token = secrets.token_urlsafe(32)
    updated = _replace_session_row(auth_session, None, raw_token, csrf_token, now)
    if updated != 1:
        raise RuntimeError("The active session could not be revoked.")
    return raw_token, csrf_token


def set_session_cookie(response, raw_token):
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        raw_token,
        max_age=settings.SESSION_LIFETIME_SECONDS,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        path="/",
    )
    return response


def clear_session_cookie(response):
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        path="/",
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    return response


def csrf_token_matches(auth_session, supplied_token):
    return bool(auth_session and supplied_token and hmac.compare_digest(auth_session.csrf_token, supplied_token))


def require_authenticated_user(view):
    def authenticated_view(request, *args, **kwargs):
        auth_session = getattr(request, "auth_session", None)
        user_id = valid_user_id(auth_session.user_id) if auth_session else None
        if user_id is None:
            from django.http import JsonResponse
            return JsonResponse({"message": "Sign in to continue."}, status=401)
        request.current_user_id = user_id
        return view(request, *args, **kwargs)
    authenticated_view.__name__ = view.__name__
    authenticated_view.__doc__ = view.__doc__
    return authenticated_view
