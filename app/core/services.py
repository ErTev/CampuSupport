import openai
import requests
import asyncio
from app.core.config import settings

# OpenAI client (will be used only if valid key is set)
try:
    openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY != "placeholder" else None
except Exception:
    openai_client = None

# Helper to run async functions in sync context
def run_async(coro):
    """Safely run async function in sync context (for FastAPI sync endpoints)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If already in async context, create task instead
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return loop.run_in_executor(executor, lambda: asyncio.run(coro))
    except RuntimeError:
        pass
    # Default: run normally
    return asyncio.run(coro)


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


async def summarize_text(title: str, description: str) -> str:
    """
    Kısa özet üretir. OpenAI yoksa basit kırpma yapar.
    """
    full_text = f"{title}\n\n{description}" if title else description
    # Prepare a safe fallback snippet
    snippet = full_text.strip()
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
        return template

    prompt = (
        "Sen bir teknik destek temsilcisisin. Aşağıdaki ticket açıklamasına göre kullanıcının anlayacağı, nazik ve çözüm odaklı bir cevap taslağı oluştur. "
        "Cevap Türkçe, kısa ve net olsun; gerekli aksiyonları belirt.\n\n"
        f"Başlık: {title}\nAçıklama: {description}"
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3
        )
        draft = response.choices[0].message.content.strip()
        if draft:
            return draft
        return template
    except Exception as e:
        print(f"OpenAI draft hatasi: {e}")
        return template

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