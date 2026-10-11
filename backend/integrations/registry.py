from integrations.cato.configuration import validate_cato_payload
from integrations.site24x7.configuration import validate_site24x7_payload
from integrations.solarwinds.configuration import validate_solarwinds_payload


PROVIDERS = {
    "cato": validate_cato_payload,
    "site24x7": validate_site24x7_payload,
    "solarwinds": validate_solarwinds_payload,
    "solarwinds swis api": validate_solarwinds_payload,
}


def validate_provider_payload(provider, endpoint, payload, name):
    secrets_data = payload.get("secrets") or {}
    if not isinstance(secrets_data, dict):
        raise ValueError("Secrets must be a JSON object.")
    validator = PROVIDERS.get(provider.casefold())
    if validator is None:
        raise ValueError(f"Provider '{provider}' is not yet supported by the API.")
    return validator(name, endpoint, payload, secrets_data)
