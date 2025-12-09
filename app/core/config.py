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

    # ===== BİLDİRİM AYARLARI (Harici API) =====
    
    # Email Bildirim (SMTP)
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    EMAIL_PROVIDER: str = "placeholder"  # "smtp", "sendgrid", vb.
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str = "placeholder"
    SMTP_PASSWORD: str = "placeholder"
    SMTP_FROM_EMAIL: str = "noreply@campusupport.local"
    
    # Slack Bildirim (Webhook)
    ENABLE_SLACK_NOTIFICATIONS: bool = False
    SLACK_WEBHOOK_URL: str = "placeholder"
    
    # SMS Bildirim (3. parti API)
    ENABLE_SMS_NOTIFICATIONS: bool = False
    SMS_API_URL: str = "placeholder"  # Twilio, Nexmo vb.
    SMS_API_KEY: str = "placeholder"
    
    # ===== ESKI BİLDİRİM API AYARLARI (Opsiyonel) =====
    NOTIFICATION_API_URL: str = "http://notifications.example.com/api/v1/send"
    NOTIFICATION_API_KEY: str = "placeholder"

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()