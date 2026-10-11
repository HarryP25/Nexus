import json

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse

from apps.accounts.services.sessions import csrf_token_matches, get_request_session


class ApiSecurityMiddleware:
    """Apply JSON errors, custom session CSRF, CORS, and cache policy to the API."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_api = request.path.startswith("/api/")
        origin = request.headers.get("Origin")
        allowed_origin = origin if origin in settings.FRONTEND_ORIGINS else None

        if is_api and request.method == "OPTIONS":
            response = HttpResponse(status=204)
        else:
            try:
                if is_api and request.META.get("CONTENT_LENGTH"):
                    if int(request.META["CONTENT_LENGTH"]) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
                        response = JsonResponse({"message": "Request body is too large."}, status=413)
                    else:
                        response = None
                else:
                    response = None

                if response is None and is_api:
                    request.auth_session = get_request_session(request)
                    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
                        supplied = request.headers.get("X-CSRF-Token", "")
                        if not csrf_token_matches(request.auth_session, supplied):
                            response = JsonResponse({"message": "Your session security token is missing or expired. Refresh the page and try again."}, status=403)

                if response is None:
                    response = self.get_response(request)
            except RequestDataTooBig:
                response = JsonResponse({"message": "Request body is too large."}, status=413)
            except ValueError as error:
                response = JsonResponse({"message": str(error)}, status=400) if is_api else None
                if response is None:
                    raise
            except RuntimeError as error:
                response = JsonResponse({"message": str(error)}, status=500) if is_api else None
                if response is None:
                    raise
            except DatabaseError:
                response = JsonResponse({
                    "message": "The API is running, but it cannot connect to SQL Server. Check the MSSQL settings in backend/.env and that the SQL Server instance is available."
                }, status=503) if is_api else None
                if response is None:
                    raise

        if is_api:
            response["Cache-Control"] = "no-store"
        if allowed_origin:
            response["Access-Control-Allow-Origin"] = allowed_origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRF-Token"
            response["Vary"] = "Origin"
        return response
