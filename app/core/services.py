import openai
import requests
from app.core.config import settings

openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

async def categorize_ticket(title: str, description: str, departments: list) -> str:
    """
    Ticket basligi ve icerigini kullanarak OpenAI'dan kategori atamasi ister.
    """
    if settings.OPENAI_API_KEY == "placeholder":
        # Yapay zeka anahtari tanimli degilse varsayilan departmani dondur
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
        # Cevabi temizle ve departman listesinde olup olmadigini kontrol et
        category = response.choices[0].message.content.strip()
        if category in departments:
            return category
        else:
            # Gecersiz veya alakasiz cevap gelirse varsayilan departmani dondur
            return departments[0]

    except Exception as e:
        print(f"OpenAI API Hatasi: {e}")
        return departments[0]

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