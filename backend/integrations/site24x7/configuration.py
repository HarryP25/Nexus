def validate_site24x7_payload(name, endpoint, payload, secrets_data):
    access_token = secrets_data.get("accessToken")
    access_token = access_token.strip() if isinstance(access_token, str) else ""
    if not access_token:
        raise ValueError("Access Token is required for Site24x7.")
    return name, "Site24x7", endpoint, access_token, None, None, payload
