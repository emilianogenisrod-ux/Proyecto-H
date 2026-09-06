from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = "sqlite:///./data/hospital.db"
    APP_TITLE: str = "Gestor de Citas Hospitalarias"
    SESSION_SECRET: str = "proyecto-h-dev-secret-change-me"
    DEMO_EMAIL: str = "recepcion@proyectoh.local"
    DEMO_PASSWORD: str = "hospital123"
    DEMO_NAME: str = "Recepción Central"
    DEMO_ROLE: str = "Recepcionista"
    MAX_IMAGE_BYTES: int = 5 * 1024 * 1024
    MAX_VIDEO_BYTES: int = 50 * 1024 * 1024

    # Supabase / API pública
    SUPABASE_URL: str = "https://iagenteksupabase.iagentek.com.mx"
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # MinIO (imágenes, plantillas, videos)
    MINIO_ENDPOINT: str = "https://iagentekminioback.iagentek.com.mx"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "hospital"
    MINIO_SECURE: bool = True
    MINIO_PUBLIC_BASE_URL: str = "https://iagentekminioback.iagentek.com.mx"
    MINIO_ENABLED: bool = False


settings = Settings()
