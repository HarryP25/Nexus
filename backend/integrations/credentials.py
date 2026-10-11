import json
import os

from cryptography.fernet import Fernet, InvalidToken


def get_secret_cipher():
    encryption_key = os.getenv("DATASOURCE_ENCRYPTION_KEY")
    if not encryption_key:
        raise RuntimeError("Missing DATASOURCE_ENCRYPTION_KEY. Configure it before saving data-source credentials.")
    try:
        return Fernet(encryption_key.encode())
    except (TypeError, ValueError) as error:
        raise RuntimeError("DATASOURCE_ENCRYPTION_KEY is invalid. Generate a valid Fernet key.") from error


def encrypt_secret_value(value):
    return get_secret_cipher().encrypt(value.encode()).decode()


def decrypt_secrets(encrypted_secrets):
    if not encrypted_secrets:
        return {}
    try:
        return json.loads(get_secret_cipher().decrypt(encrypted_secrets.encode()).decode())
    except (InvalidToken, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError("Saved data-source credentials could not be decrypted.") from error
