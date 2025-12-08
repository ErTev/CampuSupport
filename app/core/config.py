from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    # Veritabanı Ayarları
    DATABASE_URL: str = "sqlite:///./campusupport.db"

    # JWT Ayarları
    # ----------------------------------------------
    SECRET_KEY: str = "YOUR_SUPER_SECRET_KEY_PLACEHOLDER"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # ----------------------------------------------

    # Yapay Zeka Ayarları (Bölüm 2)
    OPENAI_API_KEY: str = "placeholder"

    # Bildirim Servisi Ayarları (Bölüm 2)
    NOTIFICATION_API_URL: str = "http://notifications.example.com/api/v1/send"
    NOTIFICATION_API_KEY: str = "placeholder"

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()