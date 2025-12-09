"""
Harici bildirim hizmetleri: Email, Slack, SMS vb.
Ticket çözülmesi durumunda bu servisleri çağırır.
"""
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings


class NotificationService(ABC):
    """Bildirim servisleri için temel abstract sınıf."""
    
    @abstractmethod
    def send(self, ticket_id: int, title: str, status: str, description: str, **kwargs) -> bool:
        """
        Bildirim gönder.
        
        Args:
            ticket_id: Ticket ID
            title: Ticket başlığı
            status: Ticket son durumu (Resolved, Closed vb.)
            description: Kısa açıklama
            **kwargs: Ek alanlar (resolver email, created_by_email vb.)
        
        Returns:
            Başarılı olup olmadığı (bool)
        """
        pass


class EmailNotificationService(NotificationService):
    """Email üzerinden bildirim gönderir."""
    
    def send(self, ticket_id: int, title: str, status: str, description: str, **kwargs) -> bool:
        """SMTP üzerinden email gönder."""
        if settings.EMAIL_PROVIDER == "placeholder" or not settings.SMTP_SERVER:
            print("[EMAIL] Bildirim ayarları yapılmadı, bildirim atlandı.")
            return False
        
        try:
            recipient = kwargs.get('created_by_email', 'user@example.com')
            resolver = kwargs.get('resolver_email', 'support@example.com')
            
            subject = f"Ticket #{ticket_id} Çözüldü: {title}"
            body = f"""
Merhaba,

Talebiniz başarıyla çözülmüştür.

Ticket Detayları:
- ID: {ticket_id}
- Başlık: {title}
- Durum: {status}
- Açıklama: {description}
- Çözen: {resolver}

En kısa sürede iletişime geçebilirsiniz.

Saygılarımızla,
CampuSupport Sistem
            """.strip()
            
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_FROM_EMAIL or 'noreply@campusupport.local'
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT or 587) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"[EMAIL] Bildirim başarıyla gönderildi: {recipient}")
            return True
        except Exception as e:
            print(f"[EMAIL] Bildirim gönderme hatası: {e}")
            return False


class SlackNotificationService(NotificationService):
    """Slack webhook üzerinden bildirim gönderir."""
    
    def send(self, ticket_id: int, title: str, status: str, description: str, **kwargs) -> bool:
        """Slack webhook'a bildirim gönder."""
        if settings.SLACK_WEBHOOK_URL == "placeholder" or not settings.SLACK_WEBHOOK_URL:
            print("[SLACK] Webhook ayarı yapılmadı, bildirim atlandı.")
            return False
        
        try:
            resolver = kwargs.get('resolver_email', 'unknown')
            color = "good" if status == "Resolved" else "warning"
            
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Ticket #{ticket_id} - {status}",
                        "fields": [
                            {"title": "Başlık", "value": title, "short": False},
                            {"title": "Durum", "value": status, "short": True},
                            {"title": "Çözen", "value": resolver, "short": True},
                            {"title": "Açıklama", "value": description, "short": False},
                        ]
                    }
                ]
            }
            
            response = requests.post(settings.SLACK_WEBHOOK_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[SLACK] Bildirim başarıyla gönderildi (Ticket #{ticket_id})")
                return True
            else:
                print(f"[SLACK] Gönderme hatası: {response.status_code}")
                return False
        except Exception as e:
            print(f"[SLACK] Bildirim gönderme hatası: {e}")
            return False


class SMSNotificationService(NotificationService):
    """SMS üzerinden bildirim gönderir (Twilio vb. servisler için)."""
    
    def send(self, ticket_id: int, title: str, status: str, description: str, **kwargs) -> bool:
        """SMS API üzerinden kısa bildirim gönder."""
        if settings.SMS_API_URL == "placeholder" or not settings.SMS_API_URL:
            print("[SMS] API ayarı yapılmadı, bildirim atlandı.")
            return False
        
        try:
            phone = kwargs.get('phone_number', '')
            if not phone:
                print("[SMS] Telefon numarası bulunamadı.")
                return False
            
            message = f"Ticket #{ticket_id} ({title}) {status} durumuna geçmiştir."
            
            payload = {
                "to": phone,
                "message": message,
                "api_key": settings.SMS_API_KEY
            }
            
            response = requests.post(settings.SMS_API_URL, json=payload, timeout=5)
            if response.status_code in [200, 201]:
                print(f"[SMS] Bildirim başarıyla gönderildi: {phone}")
                return True
            else:
                print(f"[SMS] Gönderme hatası: {response.status_code}")
                return False
        except Exception as e:
            print(f"[SMS] Bildirim gönderme hatası: {e}")
            return False


class NotificationFactory:
    """Bildirim servisi factory; yapılandırılmış servisleri sağlar."""
    
    _services: dict = {}
    
    @classmethod
    def get_service(cls, service_type: str) -> Optional[NotificationService]:
        """Belirli bir bildirim servisini al."""
        if service_type == "email":
            return EmailNotificationService()
        elif service_type == "slack":
            return SlackNotificationService()
        elif service_type == "sms":
            return SMSNotificationService()
        return None
    
    @classmethod
    def send_all_enabled(cls, ticket_id: int, title: str, status: str, description: str, **kwargs):
        """Tüm etkinleştirilmiş servislere bildirim gönder."""
        results = {}
        
        # Email
        if settings.ENABLE_EMAIL_NOTIFICATIONS:
            email_svc = cls.get_service("email")
            results['email'] = email_svc.send(ticket_id, title, status, description, **kwargs) if email_svc else False
        
        # Slack
        if settings.ENABLE_SLACK_NOTIFICATIONS:
            slack_svc = cls.get_service("slack")
            results['slack'] = slack_svc.send(ticket_id, title, status, description, **kwargs) if slack_svc else False
        
        # SMS
        if settings.ENABLE_SMS_NOTIFICATIONS:
            sms_svc = cls.get_service("sms")
            results['sms'] = sms_svc.send(ticket_id, title, status, description, **kwargs) if sms_svc else False
        
        return results
