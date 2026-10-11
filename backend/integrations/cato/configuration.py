def _text(value):
    return value.strip() if isinstance(value, str) else ""


def validate_cato_payload(name, endpoint, payload, secrets_data):
    cato = payload.get("cato") or {}
    if not isinstance(cato, dict):
        raise ValueError("Cato settings must be a JSON object.")
    api_url = "https://api.catonetworks.com/api/v1/graphql2"
    api_key = _text(cato.get("CATO_API_KEY") or secrets_data.get("apiKey"))
    account_id = _text(cato.get("CATO_ACCOUNT_ID"))
    site_ids = _text(cato.get("CATO_SITE_IDS"))
    if not api_key or not account_id or not site_ids:
        raise ValueError("API Key, Account ID, and Site IDs are all required for Cato.")
    return name, "Cato", api_url, api_key, account_id, site_ids, payload
