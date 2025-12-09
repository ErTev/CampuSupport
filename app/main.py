from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
import sys
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.routers import auth, tickets
from app.models import user, ticket
from app.models.user import Role, Department
from starlette.middleware.cors import CORSMiddleware # CORS için yeni import

Base.metadata.create_all(bind=engine)

# Configure basic logging for the application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        # you can also add a FileHandler here if persistent logs are desired
    ]
)

def seed_database(db: Session):
    roles = ["student", "support", "department", "admin"]
    for role_name in roles:
        if not db.query(Role).filter(Role.name == role_name).first():
            db.add(Role(name=role_name))

    # Türkçe karakterler sorun çıkarmasın diye yine İngilizce karşılıklarını kullanıyoruz
    departments = ["Bilgi Islem", "Yapi Isleri", "Ogrenci Isleri", "Akademik Danismanlik"]
    for dept_name in departments:
        if not db.query(Department).filter(Department.name == dept_name).first():
            db.add(Department(name=dept_name))

    db.commit()

app = FastAPI(title="CampuSupport - Ticket Management System")

# CORS Middleware (Frontend'den gelen isteklere izin verir)
origins = ["*"] # Geliştirme ortamında her yerden izin veriyoruz

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik dosyaları (HTML, CSS, JS) sunmak için
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    seed_database(db)
    # Ensure `category` column exists in tickets table (simple SQLite-safe check)
    try:
        # Use raw connection to check columns
        conn = engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(tickets);")
        cols = [r[1] for r in cursor.fetchall()]
        if 'category' not in cols:
            try:
                cursor.execute("ALTER TABLE tickets ADD COLUMN category TEXT;")
                conn.commit()
                print('Added `category` column to tickets table')
            except Exception as e:
                print('Failed to add category column:', e)
        cursor.close()
        conn.close()
    except Exception as e:
        print('Startup DB check error:', e)
    finally:
        db.close()

app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(tickets.router, prefix="/api/v1/tickets")

# Yeni ana sayfa rotası, index.html dosyasını döndürecek
@app.get("/")
def serve_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
def read_api_root():
    return {"message": "CampuSupport Backend calisiyor!"}