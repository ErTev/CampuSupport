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
    # SMTP / Email bildirimleri (opsiyonel). Eğer `NOTIFICATION_METHOD` == "email" veya
    # `SMTP_HOST` dolu ise e-posta gönderimi kullanılacaktır.
    NOTIFICATION_METHOD: str = "email"  # "email" - varsayılan olarak e-posta gönder
    SMTP_HOST: str = "smtp.gmail.com"  # Gmail SMTP sunucusu
    SMTP_PORT: int = 587  # Gmail TLS port
    SMTP_USER: str = "mehmetcansever232@gmail.com"
    SMTP_PASSWORD: str = "placeholder"  # .env dosyasından yüklenecek veya ortam değişkeninden
    SMTP_USE_TLS: bool = True  # Gmail için TLS gerekli
    SMTP_FROM: str = "mehmetcansever232@gmail.com"
    # Varsayılan alıcılar (virgülle ayrılmış). Eğer boşsa `SMTP_USER` kullanılabilir.
    SMTP_TO: str = ""

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()