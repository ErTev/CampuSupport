# CampuSupport - Üniversite Ticket Yönetim Sistemi

## 📋 Proje Açıklaması

CampuSupport, üniversite kampüsündeki destek taleplerini yönetmek için tasarlanmış bir web uygulamasıdır. Öğrenciler, akademisyenler ve idari personel çeşitli departmanlardan destek alabilirler.

**Temel Özellikler:**
- 👥 Rol tabanlı kullanıcı yönetimi (Öğrenci, Destek Personeli, Departman Yöneticisi, Admin)
- 🎫 Ticket oluşturma, takip ve yönetimi
- 💬 Ticket'lara yorum ekleme sistemi
- 🔐 Güvenli kimlik doğrulama (JWT Token + Bcrypt)
- 📊 Filtreleme ve sıralama
- 📱 Responsive web arayüzü

---

## 🚀 Başlangıç

### Gereksinimler
- Python 3.8+
- SQLite3
- pip (Python paket yöneticisi)

### Kurulum Adımları

#### 1. Depoyu Klonlayın
```bash
git clone https://github.com/yourusername/campusupport.git
cd campusupport
```

#### 2. Sanal Ortam Oluşturun
```bash
python -m venv venv
```

#### 3. Sanal Ortamı Etkinleştirin

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

#### 4. Bağımlılıkları Yükleyin
```bash
pip install -r requirements.txt
```

#### 5. Uygulamayı Çalıştırın
```bash
python -m uvicorn app.main:app --reload
```

Uygulama `http://localhost:8000` adresinde çalışacaktır.

---

## 📁 Proje Yapısı

```
CampuSupport-NEW/
├── app/
│   ├── __pycache__/
│   ├── core/                 # Çekirdek yapılandırma
│   │   ├── auth.py          # JWT ve rol kontrolü
│   │   ├── config.py        # Ayarlar
│   │   ├── security.py      # Şifre hashing
│   │   └── services.py      # İşletme servisleri
│   ├── models/              # Veritabanı modelleri
│   │   ├── user.py          # Kullanıcı modeli
│   │   └── ticket.py        # Ticket ve Comment modelleri
│   ├── routers/             # API endpoint'leri
│   │   ├── auth.py          # Kimlik doğrulama
│   │   └── tickets.py       # Ticket yönetimi
│   ├── schemas/             # Pydantic şemaları (validasyon)
│   │   ├── user.py          # Kullanıcı şemaları
│   │   └── ticket.py        # Ticket şemaları
│   ├── database.py          # Veritabanı konfigürasyonu
│   └── main.py              # Uygulama giriş noktası
├── static/                  # Frontend dosyaları
│   ├── index.html           # Ana sayfa
│   ├── css/
│   │   └── style.css        # Stil dosyaları
│   └── js/
│       └── app.js           # JavaScript mantığı
├── requirements.txt         # Python bağımlılıkları
└── README.md               # Bu dosya
```

---

## 🔧 API Endpoints

### Kimlik Doğrulama (Auth)
| Method | Endpoint | Açıklama | Rol |
|--------|----------|----------|-----|
| POST | `/api/v1/auth/register` | Yeni kullanıcı kayıt | Herkese açık |
| POST | `/api/v1/auth/login` | Kullanıcı giriş | Herkese açık |

### Ticket Yönetimi
| Method | Endpoint | Açıklama | Rol |
|--------|----------|----------|-----|
| POST | `/api/v1/tickets/` | Yeni ticket oluştur | Öğrenci |
| GET | `/api/v1/tickets/my` | Kendi ticket'larını görmek | Öğrenci |
| GET | `/api/v1/tickets/department` | Departman ticket'ları | Departman Yöneticisi |
| GET | `/api/v1/tickets/support` | Atanmış ticket'lar | Support Personeli |
| GET | `/api/v1/tickets/` | Tüm ticket'lar (filtreleme) | Admin |
| PUT | `/api/v1/tickets/{id}/assign` | Ticket atama | Departman Yöneticisi |
| PUT | `/api/v1/tickets/{id}/status` | Ticket durumu değiştirme | Support Personeli |
| POST | `/api/v1/tickets/{id}/comment` | Yorum ekleme | Öğrenci / Support |

---

## 👥 Kullanıcı Rolleri

### 1. **Öğrenci (student)**
- ✅ Ticket oluşturabilir
- ✅ Kendi ticket'larını görebilir
- ✅ Ticket'larına yorum yazabilir
- ❌ Diğer ticket'ları göremez

### 2. **Destek Personeli (support)**
- ✅ Kendisine atanan ticket'ları görebilir
- ✅ Ticket durumunu değiştirebilir
- ✅ Ticket'lara yorum yazabilir
- ✅ Departmanında çalışır

### 3. **Departman Yöneticisi (department)**
- ✅ Departmana gelen tüm ticket'ları görebilir
- ✅ Ticket'ları support personeline atayabilir
- ✅ Ticket durumunu filtreleyebilir
- ✅ Support personelini yönetebilir
- ✅ Ticket'lara yorum yazabilir

### 4. **Yönetici (admin)**
- ✅ Tüm ticket'ları görebilir
- ✅ Tüm işlemleri yapabilir
- ✅ Filtreleme ve sıralama seçenekleri

---

## 🛠️ Teknoloji Stack

| Teknoloji | Kullanım |
|-----------|----------|
| **FastAPI** | Web framework (Python) |
| **SQLAlchemy** | ORM (Object Relational Mapping) |
| **SQLite** | Veritabanı |
| **Pydantic** | Veri doğrulama |
| **Bcrypt** | Şifre hashing |
| **JWT (Jose)** | Token tabanlı kimlik doğrulama |
| **Jinja2** | Template rendering |
| **Vanilla JS** | Frontend JavaScript |
| **HTML5 + CSS3** | Frontend UI |

---

## 📝 Örnek Kullanım

### 1. Kayıt Ol
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ogrenci@universite.edu.tr",
    "password": "sifre123",
    "role_name": "student"
  }'
```

### 2. Giriş Yap
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ogrenci@universite.edu.tr",
    "password": "sifre123"
  }'
```

**Yanıt:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Ticket Oluştur
```bash
curl -X POST http://localhost:8000/api/v1/tickets/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "Şifre sıfırlama isteği",
    "description": "Şifremi unuttum ve sıfırlamak istiyorum",
    "department_name": "Bilgi Islem",
    "priority": "High"
  }'
```

---

## 🔐 Güvenlik

- ✅ Şifreler **bcrypt** ile 72-byte UTF-8 sınırında hashlanır
- ✅ JWT token ile kimlik doğrulama
- ✅ Rol tabanlı erişim kontrolü (RBAC)
- ✅ HTTPS önerilir (production için)
- ✅ Environment variables kullanılır (gizli ayarlar)

---

## 📊 Veritabanı Şeması

### Users Tablosu
| Sütun | Tür | Açıklama |
|-------|-----|----------|
| id | Integer | Birincil anahtar |
| email | String | E-posta adresi (benzersiz) |
| password_hash | String | Şifre (bcrypt) |
| role_id | Integer | Rol referansı |
| department_id | Integer | Departman referansı |

### Tickets Tablosu
| Sütun | Tür | Açıklama |
|-------|-----|----------|
| id | Integer | Birincil anahtar |
| title | String | Ticket başlığı |
| description | String | Detaylı açıklama |
| priority | String | Düşük / Orta / Yüksek |
| status | String | Open / In Progress / Resolved / Closed |
| created_by_user_id | Integer | Oluşturan öğrenci |
| assigned_support_id | Integer | Atanmış support personeli |
| assigned_department_id | Integer | Atanmış departman |
| created_at | DateTime | Oluşturma tarihi |
| updated_at | DateTime | Güncelleme tarihi |

### Comments Tablosu
| Sütun | Tür | Açıklama |
|-------|-----|----------|
| id | Integer | Birincil anahtar |
| ticket_id | Integer | Ticket referansı |
| user_id | Integer | Yorum yapan kullanıcı |
| content | String | Yorum içeriği |
| created_at | DateTime | Oluşturma tarihi |

---

## 🧪 Test Etme

### Postman Koleksiyonu
`postman_collection.json` dosyasını Postman'a import edin veya manuel olarak endpoint'leri test edin.

### Manuel Test
1. `http://localhost:8000` adresine gidin
2. Kayıt formundan yeni hesap oluşturun
3. Giriş yapın
4. Ticket oluşturun ve takip edin

---

## 🐛 Troubleshooting

### Port 8000 Meşgul
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Veritabanı Hataları
```bash
# Veritabanı dosyasını sil ve yeniden oluştur
rm campusupport.db
python -m uvicorn app.main:app --reload
```

### Modül Bulunamadı
```bash
# Bağımlılıkları yeniden yükle
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Kaynaklar

- [FastAPI Dokumentasyon](https://fastapi.tiangolo.com/)
- [SQLAlchemy Dokumentasyon](https://docs.sqlalchemy.org/)
- [Pydantic Dokumentasyon](https://docs.pydantic.dev/)
- [JWT.io](https://jwt.io/)

---

## 📄 Lisans

Bu proje MIT Lisansı altında yayınlanmıştır.

---

## 👨‍💼 Katkılar

Katkı yapmak isterseniz:
1. Depoyu fork edin
2. Özellik dalı oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişiklikleri commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Dalı push edin (`git push origin feature/AmazingFeature`)
5. Pull Request açın

---

## 📧 İletişim

Sorular veya öneriler için lütfen issue açın veya bize email gönderin.

---

**Son Güncelleme:** Aralık 2025
