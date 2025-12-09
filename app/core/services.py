import openai
import requests
from app.core.config import settings

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
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.0
        )
        priority = response.choices[0].message.content.strip()
        if priority in ["High", "Medium", "Low"]:
            return priority
        if priority.capitalize() in ["High", "Medium", "Low"]:
            return priority.capitalize()
        return "Low"
    except Exception as e:
        print(f"OpenAI priority suggestion hatasi: {e}")
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
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0.0
        )
        category = response.choices[0].message.content.strip()
        if category in departments:
            return category
        return departments[0]
    except Exception as e:
        print(f"OpenAI API Hatasi: {e}")
        return departments[0]


async def suggest_ticket(title: str, description: str, departments: list) -> dict:
    """
    Bir ticket için kategori ve öncelik önerisi döndürür.
    Dönen yapı: {"department": ..., "priority": ...}
    """
    category = await categorize_ticket(title, description, departments)
    priority = await suggest_priority(title, description)
    return {"department": category, "priority": priority}

async def send_notification(ticket_id: int, old_status: str, new_status: str):
    """
    Ticket durumu degistiginde harici bir servise bildirim gonderir.
    """
    if settings.NOTIFICATION_API_KEY == "placeholder":
        print("Bildirim API anahtari tanimli degil, bildirim atlandi.")
        return

    notification_data = {
        "ticket_id": ticket_id,
        "message": f"Ticket {ticket_id} durumu {old_status} -> {new_status} olarak degisti."
    }

    try:
        response = requests.post(
            settings.NOTIFICATION_API_URL,
            json=notification_data,
            headers={"Authorization": f"Bearer {settings.NOTIFICATION_API_KEY}"},
            timeout=5
        )
        response.raise_for_status()
        print(f"Bildirim basariyla gonderildi: Ticket {ticket_id}")

    except requests.exceptions.RequestException as e:
        print(f"Bildirim gonderme hatasi: {e}")