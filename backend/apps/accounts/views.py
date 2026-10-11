from django.db import IntegrityError, transaction
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from werkzeug.security import check_password_hash, generate_password_hash

from apps.accounts.models import NexusUser
from apps.accounts.services.sessions import issue_session, rotate_session_to_anonymous, set_session_cookie, valid_user_id
from api.http import method_not_allowed, read_json_object
from apps.accounts.services.sessions import require_authenticated_user


def current_session(request):
    if request.method != "GET":
        return method_not_allowed(["GET"])
    auth_session = getattr(request, "auth_session", None)
    raw_token = None
    if not auth_session:
        auth_session, raw_token, _ = issue_session()
    # Older/stale session rows may contain a non-UUID userUniqueID. Avoid
    # passing that value into SQL Server's UNIQUEIDENTIFIER comparison.
    user_id = valid_user_id(auth_session.user_id)
    # Some pre-Django databases stored uniqueID as text and may contain legacy
    # non-UUID values. SQL Server's implicit text-to-UUID comparison fails on
    # those rows, so explicitly convert safely during this compatibility path.
    user = None
    if user_id:
        users = NexusUser.objects.raw(
            """
            SELECT TRY_CONVERT(uniqueidentifier, uniqueID) AS uniqueID,
                   username, passwordHash, createdAt
            FROM dbo.NexusUsers
            WHERE TRY_CONVERT(uniqueidentifier, uniqueID) = %s
            """,
            [str(user_id)],
        )
        user = next(iter(users), None)
    response = JsonResponse({
        "authenticated": user is not None,
        "user": {"uniqueID": str(user.unique_id), "username": user.username} if user else None,
        "csrfToken": auth_session.csrf_token,
    })
    if raw_token:
        set_session_cookie(response, raw_token)
    return response


def signup(request):
    if request.method != "POST":
        return method_not_allowed(["POST"])
    payload = read_json_object(request)
    username_value = payload.get("username")
    password_value = payload.get("password")
    username = username_value.strip() if isinstance(username_value, str) else ""
    password = password_value.strip() if isinstance(password_value, str) else ""
    if not username or not password:
        return JsonResponse({"message": "Please enter both a username and password."}, status=400)
    if len(username) > 100:
        return JsonResponse({"message": "Username must be 100 characters or fewer."}, status=400)
    if len(password) < 12:
        return JsonResponse({"message": "Use a password with at least 12 characters."}, status=400)
    if len(password) > 256:
        return JsonResponse({"message": "Password must be 256 characters or fewer."}, status=400)
    if NexusUser.objects.filter(username=username).exists():
        return JsonResponse({"message": "Username already exists. Please sign in or choose another username."}, status=409)

    try:
        with transaction.atomic():
            user = NexusUser.objects.create(
                username=username,
                password_hash=generate_password_hash(password),
                created_at=timezone.now(),
            )
    except IntegrityError:
        return JsonResponse({"message": "Username already exists. Please sign in or choose another username."}, status=409)
    return JsonResponse({"uniqueID": str(user.unique_id), "username": user.username}, status=201)


def login(request):
    if request.method != "POST":
        return method_not_allowed(["POST"])
    payload = read_json_object(request)
    username_value = payload.get("username")
    password_value = payload.get("password")
    username = username_value.strip() if isinstance(username_value, str) else ""
    password = password_value.strip() if isinstance(password_value, str) else ""
    if not username or not password:
        return JsonResponse({"message": "Please enter both a username and password."}, status=400)
    user = NexusUser.objects.filter(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return JsonResponse({"message": "Invalid username or password."}, status=401)

    _, raw_token, csrf_token = issue_session(user=user, replacing=getattr(request, "auth_session", None))
    response = JsonResponse({"uniqueID": str(user.unique_id), "username": user.username, "csrfToken": csrf_token})
    return set_session_cookie(response, raw_token)


def logout(request):
    if request.method != "POST":
        return method_not_allowed(["POST"])
    raw_token, csrf_token = rotate_session_to_anonymous(getattr(request, "auth_session", None))
    response = JsonResponse({"message": "Signed out.", "csrfToken": csrf_token})
    return set_session_cookie(response, raw_token)


@require_authenticated_user
def user_count(request):
    if request.method != "GET":
        return method_not_allowed(["GET"])
    return JsonResponse({"count": NexusUser.objects.aggregate(total=Count("unique_id"))["total"]})
