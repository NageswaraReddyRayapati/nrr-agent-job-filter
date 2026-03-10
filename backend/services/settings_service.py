"""Settings service — stores and retrieves API keys with masking."""
from __future__ import annotations

import base64
import logging
import os

from sqlalchemy.orm import Session

from models.db_models import AppSettings

logger = logging.getLogger(__name__)

_FERNET_KEY_ENV = "SECRET_KEY"


def _get_fernet():
    """Get or create a Fernet encryption instance."""
    try:
        from cryptography.fernet import Fernet
        secret = os.getenv(_FERNET_KEY_ENV, "default-secret-key-change-me")
        # Derive a 32-byte key from the secret
        key_bytes = secret.encode()[:32].ljust(32, b"0")
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)
    except Exception as exc:
        logger.warning("Encryption not available: %s", exc)
        return None


def _encrypt(value: str) -> str:
    fernet = _get_fernet()
    if fernet:
        return fernet.encrypt(value.encode()).decode()
    return value  # fallback: store as-is


def _decrypt(value: str) -> str:
    fernet = _get_fernet()
    if fernet:
        try:
            return fernet.decrypt(value.encode()).decode()
        except Exception:
            return value  # already plain text
    return value


def _mask(value: str) -> str:
    """Mask an API key, showing only first 4 and last 4 characters."""
    if not value or len(value) < 8:
        return "****"
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


class SettingsService:
    """Manages application settings stored in the database."""

    OPENAI_KEY = "openai_api_key"
    SERPAPI_KEY = "serpapi_key"

    def save(self, db: Session, openai_key: str | None, serpapi_key: str | None) -> None:
        """Save API keys to the database (encrypted)."""
        if openai_key is not None:
            self._upsert(db, self.OPENAI_KEY, openai_key)
        if serpapi_key is not None:
            self._upsert(db, self.SERPAPI_KEY, serpapi_key)
        db.commit()

    def get(self, db: Session) -> dict:
        """Get settings with masked keys for display."""
        openai_raw = self._get_decrypted(db, self.OPENAI_KEY)
        serpapi_raw = self._get_decrypted(db, self.SERPAPI_KEY)
        return {
            "openai_api_key_set": bool(openai_raw),
            "serpapi_key_set": bool(serpapi_raw),
            "openai_api_key_masked": _mask(openai_raw) if openai_raw else None,
            "serpapi_key_masked": _mask(serpapi_raw) if serpapi_raw else None,
        }

    def get_openai_key(self, db: Session) -> str:
        """Get decrypted OpenAI API key."""
        return self._get_decrypted(db, self.OPENAI_KEY) or os.getenv("OPENAI_API_KEY", "")

    def get_serpapi_key(self, db: Session) -> str:
        """Get decrypted SerpAPI key."""
        return self._get_decrypted(db, self.SERPAPI_KEY) or os.getenv("SERPAPI_KEY", "")

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    def _upsert(self, db: Session, key: str, value: str) -> None:
        row = db.query(AppSettings).filter(AppSettings.key == key).first()
        encrypted = _encrypt(value)
        if row:
            row.value = encrypted
            row.is_encrypted = True
        else:
            row = AppSettings(key=key, value=encrypted, is_encrypted=True)
            db.add(row)

    def _get_decrypted(self, db: Session, key: str) -> str:
        row = db.query(AppSettings).filter(AppSettings.key == key).first()
        if not row or not row.value:
            return ""
        if row.is_encrypted:
            return _decrypt(row.value)
        return row.value
