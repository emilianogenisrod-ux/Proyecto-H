from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret_file(path: str) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.is_file():
        return ""
    return file_path.read_text(encoding="utf-8").strip()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/hospital.db"
    APP_TITLE: str = "Gestor de Citas Hospitalarias"
    SESSION_SECRET: str = "proyecto-h-dev-secret-change-me"
    MAX_IMAGE_BYTES: int = 5 * 1024 * 1024
    MAX_VIDEO_BYTES: int = 50 * 1024 * 1024

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    MINIO_ENDPOINT: str = ""
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "hospital"
    MINIO_SECURE: bool = True
    MINIO_PUBLIC_BASE_URL: str = ""
    MINIO_ENABLED: bool = False

    USER_PASSWORDS_JSON: str = ""

    DATABASE_URL_FILE: str = ""
    SESSION_SECRET_FILE: str = ""
    MINIO_ACCESS_KEY_FILE: str = ""
    MINIO_SECRET_KEY_FILE: str = ""
    USER_PASSWORDS_JSON_FILE: str = ""

    @model_validator(mode="after")
    def load_docker_secrets(self):
        database_url = _read_secret_file(self.DATABASE_URL_FILE)
        if database_url:
            self.DATABASE_URL = database_url
        session_secret = _read_secret_file(self.SESSION_SECRET_FILE)
        if session_secret:
            self.SESSION_SECRET = session_secret
        minio_access = _read_secret_file(self.MINIO_ACCESS_KEY_FILE)
        if minio_access:
            self.MINIO_ACCESS_KEY = minio_access
        minio_secret = _read_secret_file(self.MINIO_SECRET_KEY_FILE)
        if minio_secret:
            self.MINIO_SECRET_KEY = minio_secret
        passwords = _read_secret_file(self.USER_PASSWORDS_JSON_FILE)
        if passwords:
            self.USER_PASSWORDS_JSON = passwords
        return self


settings = Settings()
