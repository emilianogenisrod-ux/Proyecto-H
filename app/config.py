from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./data/hospital.db"
    APP_TITLE: str = "Gestor de Citas Hospitalarias"


settings = Settings()
