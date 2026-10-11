def _text(value):
    return value.strip() if isinstance(value, str) else ""


def validate_solarwinds_payload(name, endpoint, payload, secrets_data):
    username = _text(secrets_data.get("username"))
    password = _text(secrets_data.get("password"))
    if not username or not password:
        raise ValueError("Username and password are required for Solarwinds.")
    return name, "Solarwinds", endpoint, username, password, None, payload
