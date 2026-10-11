import json

from django.http import JsonResponse


def read_json_object(request):
    if not request.body:
        return {}
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("Request body must contain valid JSON.") from error
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    return payload


def method_not_allowed(allowed):
    response = JsonResponse({"message": "Method not allowed."}, status=405)
    response["Allow"] = ", ".join(allowed)
    return response
