"""Verificación de contraseñas. Los hashes viven fuera del repositorio."""

from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path


def verify_password(password: str, stored: str) -> bool:
    if not password or not stored:
        return False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds_s, salt_hex, digest_hex = stored.split("$", 3)
            rounds = int(rounds_s)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
        except (ValueError, TypeError):
            return False
        got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(got, expected)
    return hmac.compare_digest(password.encode("utf-8"), stored.encode("utf-8"))


def load_json_secret(raw: str, file_path: str) -> dict[str, str]:
    text = (raw or "").strip()
    if not text and file_path:
        path = Path(file_path)
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key).strip().lower(): str(value)
        for key, value in data.items()
        if isinstance(value, str) and value
    }
