import openai
from datetime import datetime
import requests
import json
import smtplib
from email.message import EmailMessage
from app.core.config import settings
import logging

logger = logging.getLogger("app.core.services")


# OpenAI client (will be used only if valid key is set)
try:
    openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY != "placeholder" else None
except Exception:
    openai_client = None


def suggest_priority_fallback(title: str, description: str) -> str:
    """
    Basit kural tabanlı öncelik önerisi (OpenAI yokken kullan).
    """
    txt = f"{title} {description}".lower()
    if any(k in txt for k in ["acil", "hızlı", "urgent", "çok önemli", "acıl", "kapalı", "sistem", "çöktü"]):
        return "High"
    if any(k in txt for k in ["yavaş", "sürekli", "kopuyor", "erişim", "bağlantı", "ağ", "internet"]):
        return "Medium"
    return "Low"


async def suggest_priority(title: str, description: str) -> str:
    """
    OpenAI veya fallback ile ticket önceliği (High/Medium/Low) önerisi döndürür.
    """
    if not openai_client or settings.OPENAI_API_KEY == "placeholder":
        return suggest_priority_fallback(title, description)

    prompt = (
        f"Aşağıdaki ticket başlığını ve açıklamasını incele ve sadece bir kelime ile önceliği ver: High, Medium veya Low.\n\n"
        f"Başlık: {title}\nAçıklama: {description}"
    )

    try:
        logger.info("AI request: suggest_priority")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.0
        )
        priority = response.choices[0].message.content.strip()
        logger.info("AI suggest_priority success: %s", priority)
        if priority in ["High", "Medium", "Low"]:
            return priority
        if priority.capitalize() in ["High", "Medium", "Low"]:
            return priority.capitalize()
        return "Low"
    except Exception as e:
        logger.exception("OpenAI priority suggestion failed")
        return suggest_priority_fallback(title, description)


async def categorize_ticket(title: str, description: str, departments: list) -> str:
    """
    Ticket başlığı ve içeriğini kullanarak kategori ataması ister.
    """
    if not departments:
        return None

    if not openai_client or settings.OPENAI_API_KEY == "placeholder":
        return departments[0]

    prompt = (
        f"Asagidaki ticket basligini ve aciklamasini analiz et. "
        f"Ticket'in ait olabilecegi departmanlar: {', '.join(departments)}. "
        f"Sadece ve sadece bu departmanlardan birinin adini dondur. Baska hicbir metin, aciklama veya ekleme yapma.\n\n"
        f"Baslik: {title}\nAciklama: {description}"
    )

    try:
        logger.info("AI request: categorize_ticket")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.0
        )
        category = response.choices[0].message.content.strip()
        logger.info("AI categorize_ticket success: %s", category)
        if category in departments:
            return category
        return departments[0]
    except Exception as e:
        logger.exception("OpenAI categorize_ticket failed")
        return departments[0]


async def suggest_ticket(title: str, description: str, departments: list) -> dict:
    """
    Bir ticket için kategori, öncelik ve başlık önerisi döndürür.
    Dönen yapı: {"suggested_title": str, "department_options": [...], "priority_options": [...], "explanation": str}
    """
    # Prepare fallback values
    top_department = await categorize_ticket(title, description, departments)
    top_priority = await suggest_priority(title, description)

    # Simple fallback options
    priority_order = [top_priority]
    for p in ["High", "Medium", "Low"]:
        if p not in priority_order:
            priority_order.append(p)

    dept_options = [top_department] if top_department else []
    # try to add more departments heuristically
    for d in departments:
        if d not in dept_options:
            dept_options.append(d)
        if len(dept_options) >= 3:
            break

    suggested_title = title or (description[:80] + '...' if description else None)
    explanation = "Öneriler kural tabanlı veya LLM tarafından üretilmiştir." 

    if not openai_client or settings.OPENAI_API_KEY == "placeholder":
        return {
            "suggested_title": suggested_title,
                "department_options": dept_options,
                "category_options": dept_options,
            "priority_options": priority_order,
            "explanation": explanation
        }

    # Ask the LLM to return a JSON object with fields
    prompt = (
        "Aşağıdaki ticket açıklamasını kullanarak JSON formatında öneriler oluştur.\n"
        "JSON şu formatta olmalı: {\"suggested_title\": string, \"department_options\": [\"Dep1\",\"Dep2\"], \"priority_options\": [\"High\",\"Medium\"], \"explanation\": string}\n"
        "Departman listesi: " + ", ".join(departments) + "\n\n"
        f"Başlık: {title}\nAçıklama: {description}\n"
        "Sadece geçerli JSON çıktısı ver, ekstra metin çıkışına izin verme.\n"
    )

    try:
        logger.info("AI request: suggest_ticket")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        content = response.choices[0].message.content.strip()
        # Try to parse JSON from the model output
        try:
            parsed = json.loads(content)
            logger.info("AI suggest_ticket success")
            return {
                "suggested_title": parsed.get("suggested_title") or suggested_title,
                "department_options": parsed.get("department_options") or dept_options,
                    "category_options": parsed.get("category_options") or dept_options,
                "priority_options": parsed.get("priority_options") or priority_order,
                "explanation": parsed.get("explanation") or explanation
            }
        except Exception:
            logger.warning("AI suggest_ticket returned non-JSON, using fallback")
            # If parsing fails, return fallback
            return {
                "suggested_title": suggested_title,
                "department_options": dept_options,
                    "category_options": dept_options,
                "priority_options": priority_order,
                "explanation": explanation
            }
    except Exception as e:
        logger.exception("OpenAI suggest_ticket failed")
        return {
            "suggested_title": suggested_title,
            "department_options": dept_options,
                "category_options": dept_options,
            "priority_options": priority_order,
            "explanation": explanation
        }


async def summarize_text(title: str, description: str) -> str:
    """
    Kısa özet üretir. OpenAI yoksa basit kırpma yapar.
    """
    full_text = f"{title}\n\n{description}" if title else description
    # Prepare a safe fallback snippet
    snippet = full_text.strip() if full_text else ""
    if len(snippet) > 200:
        end = snippet.find('. ', 150)
        if end != -1 and end < 300:
            snippet = snippet[:end+1]
        else:
            snippet = snippet[:200] + '...'

    if not openai_client or settings.OPENAI_API_KEY == "placeholder":
        return snippet

    prompt = (
        "Aşağıdaki ticket başlığı ve açıklamasını kısa ve net bir şekilde Türkçe olarak 1-2 cümleyle özetle. "
        "Sadece özeti döndür.\n\n"
        f"Başlık: {title}\nAçıklama: {description}"
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.2
        )
        summary = response.choices[0].message.content.strip()
        if summary:
            return summary
        return snippet
    except Exception as e:
        print(f"OpenAI summary hatasi: {e}")
        return snippet


async def draft_response(title: str, description: str) -> str:
    """
    Destek personeline yönelik cevap taslağı üretir. OpenAI yoksa basit şablon döner.
    """
    # Prepare a simple fallback template
    short_desc = (description or "").strip()
    if len(short_desc) > 150:
        short_summary = short_desc[:150] + '...'
    else:
        short_summary = short_desc

    template = (
        f"Merhaba,\n\nTalebinizi aldık: '{title}'. \nKısa özet: {short_summary}\n\n"
        "En kısa sürede ilgileneceğiz. Ek bilgi gerekiyorsa lütfen bize iletin.\n\nSaygılarımızla,\nDestek Ekibi"
    )

    if not openai_client or settings.OPENAI_API_KEY == "placeholder":
        logger.info("AI draft_response skipped - no API key configured, using fallback template")
        return template

    prompt = (
        "Sen bir teknik destek temsilcisisin. Aşağıdaki ticket açıklamasına göre kullanıcının anlayacağı, nazik ve çözüm odaklı bir cevap taslağı oluştur. "
        "Cevap Türkçe, kısa ve net olsun; gerekli aksiyonları belirt.\n\n"
        f"Başlık: {title}\nAçıklama: {description}"
    )

    try:
        logger.info("AI request: draft_response")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3
        )
        draft = response.choices[0].message.content.strip()
        logger.info("AI draft_response success")
        if draft:
            return draft
        return template
    except Exception as e:
        logger.exception("OpenAI draft_response failed")
        return template


def send_notification(ticket_id: int, old_status: str, new_status: str, title: str = None, description: str = None, resolver: str = None, recipient_email: str = None):
    """
    Ticket durumu degistiginde harici bir servise bildirim gonderir.
    Bu fonksiyon senkron çalışır ve arka planda thread ile çağrılmalıdır.
    """
    # Determine whether email (SMTP) is configured or webhook/API is available
    use_email = (settings.NOTIFICATION_METHOD == "email") or bool(settings.SMTP_HOST)
    use_webhook = bool(settings.NOTIFICATION_API_URL)

    if not use_email and not use_webhook:
        logger.warning("Notification service not configured (no SMTP or webhook). Skipping notification.")
        return

    short_desc = (description or "").strip()
    if len(short_desc) > 200:
        short_desc = short_desc[:197] + '...'

    payload = {
        "ticket_id": ticket_id,
        "title": title or "(başlık yok)",
        "new_status": new_status,
        "old_status": old_status,
        "short_description": short_desc,
        "resolver": resolver,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }

    # Build headers only if API key is provided and not placeholder
    headers = {"Content-Type": "application/json"}
    if settings.NOTIFICATION_API_KEY and settings.NOTIFICATION_API_KEY != "placeholder":
        headers["Authorization"] = f"Bearer {settings.NOTIFICATION_API_KEY}"

    # If email configured and chosen, try sending email first
    attempts = 3
    if use_email:
        # recipients: prefer explicit recipient_email (ticket creator), otherwise settings.SMTP_TO (comma separated) or fallback to SMTP_USER
        if recipient_email:
            recipients = [recipient_email]
        else:
            recipients = [r.strip() for r in (settings.SMTP_TO or settings.SMTP_USER or "").split(",") if r.strip()]

        if not recipients:
            logger.error("No email recipients configured. Set SMTP_TO or SMTP_USER or pass recipient_email.")
        else:
            subject = f"[Ticket {ticket_id}] {title or ''} - {new_status}"
            
            # Durum rengi ve emoji'si
            if new_status == "Resolved":
                status_color = "#28a745"
                status_emoji = "✅"
            elif new_status == "In Progress":
                status_color = "#ffc107"
                status_emoji = "⏳"
            elif new_status == "Open":
                status_color = "#17a2b8"
                status_emoji = "📋"
            else:
                status_color = "#dc3545"
                status_emoji = "🔒"
            
            # Description ve resolver HTML (ternary yerine)
            desc_html = f"<div class='description-box'><strong>📝 Açıklama / Çözüm Notu:</strong><div style='margin-top: 12px;'>{short_desc.replace(chr(10), '<br>')}</div></div>" if short_desc else ""
            resolver_html = f"<div class='resolver-box'><strong>👤 Çözen Kişi:</strong><div style='margin-top: 6px; color: #666;'>{resolver}</div></div>" if resolver else ""
            
            # HTML email body template
            html_body = f"""<html>
<head>
<meta charset="utf-8">
<style>
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5; margin: 0; padding: 0; }}
.container {{ max-width: 650px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow: hidden; }}
.header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 30px; text-align: center; }}
.header h1 {{ margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
.content {{ padding: 40px 30px; color: #333; }}
.info-table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
.info-table tr {{ border-bottom: 1px solid #e5e5e5; }}
.info-table td {{ padding: 14px 0; }}
.info-label {{ font-weight: 700; color: #667eea; width: 140px; font-size: 14px; vertical-align: top; }}
.info-value {{ color: #333; font-size: 15px; line-height: 1.5; }}
.status-badge {{ display: inline-block; padding: 8px 16px; border-radius: 24px; color: white; font-weight: 700; background-color: {status_color}; font-size: 13px; }}
.description-box {{ background: linear-gradient(135deg, #f0f9ff 0%, #f5f9ff 100%); padding: 20px; border-left: 5px solid #17a2b8; border-radius: 6px; margin: 20px 0; line-height: 1.7; color: #555; }}
.description-box strong {{ color: #17a2b8; }}
.resolver-box {{ background-color: #f8f9fa; padding: 14px; border-radius: 6px; border-left: 4px solid #667eea; margin: 15px 0; }}
.resolver-box strong {{ color: #667eea; }}
.footer {{ background-color: #f8f9fa; padding: 25px; text-align: center; font-size: 12px; color: #777; border-top: 2px solid #e5e5e5; }}
.footer a {{ color: #667eea; text-decoration: none; font-weight: 600; }}
.divider {{ height: 1px; background-color: #e5e5e5; margin: 25px 0; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🎫 Ticket Bildirimi</h1>
<p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.95;">CampuSupport Sistem</p>
</div>

<div class="content">
<p style="margin-top: 0; color: #666; font-size: 15px;">Merhaba,</p>
<p style="color: #666; font-size: 15px;">Ticket durumunuzla ilgili bir bildirim bulunmaktadır:</p>

<table class="info-table">
<tr>
<td class="info-label">🎯 Ticket ID</td>
<td class="info-value"><strong>#{ticket_id}</strong></td>
</tr>
<tr>
<td class="info-label">📌 Başlık</td>
<td class="info-value"><strong>{title or 'Başlıksız'}</strong></td>
</tr>
<tr>
<td class="info-label">{status_emoji} Durum</td>
<td class="info-value">
<span class="status-badge">{new_status}</span>
<br><span style="color: #999; font-size: 12px; margin-top: 4px; display: block;">({old_status} → {new_status})</span>
</td>
</tr>
</table>

{desc_html}
{resolver_html}

<div class="divider"></div>

<div style="font-size: 12px; color: #999; text-align: center;">
📅 <strong>{datetime.utcnow().strftime('%d.%m.%Y')}</strong> | ⏰ <strong>{datetime.utcnow().strftime('%H:%M:%S')}</strong>
</div>
</div>

<div class="footer">
<p style="margin: 0 0 10px 0;">Bu mesaj CampuSupport Ticket Management Sistemi tarafından otomatik olarak gönderilmiştir.</p>
<p style="margin: 10px 0;"><a href="http://localhost:8000">🔗 Sistemi Aç</a></p>
<p style="margin: 15px 0 0 0; font-size: 11px; color: #aaa;">© 2025 CampuSupport. Tüm hakları saklıdır.</p>
</div>
</div>
</body>
</html>"""
            
            # Plain text fallback
            body_lines = [f"Ticket ID: {ticket_id}", f"Başlık: {title or ''}", f"Durum: {old_status} -> {new_status}", ""]
            if short_desc:
                body_lines.append(f"Kısa Açıklama: {short_desc}")
            if resolver:
                body_lines.append(f"Çözen: {resolver}")
            body_lines.append(f"Zaman: {datetime.utcnow().strftime('%d.%m.%Y %H:%M:%S')}")
            body = "\n".join(body_lines)

            for attempt in range(1, attempts + 1):
                # HTML + plain text versiyonu gönder
                try:
                    msg = EmailMessage()
                    msg["Subject"] = subject
                    msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
                    msg["To"] = ",".join(recipients)
                    msg.set_content(body)  # Plain text fallback
                    msg.add_alternative(html_body, subtype='html')  # HTML versiyonu
                    
                    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
                    if settings.SMTP_USE_TLS:
                        try:
                            server.starttls()
                        except Exception as e:
                            print(f"STARTTLS failed: {e}, continuing without TLS")
                    
                    if settings.SMTP_USER:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    
                    server.send_message(msg)
                    server.quit()
                    logger.info("Email notification sent: Ticket %s", ticket_id)
                    return
                except Exception as e:
                    logger.exception("Email send error (attempt %s) for ticket %s", attempt, ticket_id)
                    import time
                    if attempt < attempts:
                        time.sleep(1 * attempt)

    # Fallback: webhook / HTTP API (keeps existing behavior)
    if use_webhook and settings.NOTIFICATION_API_URL:
        is_slack = "hooks.slack.com" in settings.NOTIFICATION_API_URL
        for attempt in range(1, attempts + 1):
            try:
                if is_slack:
                    # Simple Slack text message including resolver and short description
                    text_lines = [f"Ticket *{ticket_id}* - *{title or ''}*", f"Durum: {old_status} -> {new_status}"]
                    if resolver:
                        text_lines.append(f"Çözen: {resolver}")
                    if description:
                        text_lines.append(f"Açıklama: {description[:200]}")
                    text = "\n".join(text_lines)
                    slack_payload = {"text": text}
                    resp = requests.post(settings.NOTIFICATION_API_URL, json=slack_payload, timeout=5)
                else:
                    resp = requests.post(settings.NOTIFICATION_API_URL, json=payload, headers=headers, timeout=5)

                resp.raise_for_status()
                logger.info("Webhook notification success: Ticket %s", ticket_id)
                return
            except requests.exceptions.RequestException as e:
                logger.exception("Notification send error (attempt %s) for ticket %s", attempt, ticket_id)
                if attempt < attempts:
                    import time
                    time.sleep(1 * attempt)
                else:
                    logger.error("Notification failed after %s attempts: Ticket %s", attempts, ticket_id)