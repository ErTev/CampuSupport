from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.models.user import User, Role
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.auth import get_current_user
from datetime import timedelta
from app.core.config import settings

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Kullanıcı rolü var mı kontrol et
    role = db.query(Role).filter(Role.name == user_data.role_name).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Geçersiz kullanıcı rolü.")

    # E-posta zaten kullanılıyor mu kontrol et
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-posta zaten kayıtlı.")

    # Şifreyi hashle
    hashed_password = get_password_hash(user_data.password)

    # Yeni kullanıcıyı oluştur
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        role_id=role.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatalı kullanıcı adı veya şifre.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token oluştur
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.name}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=dict)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Oturum açmış kullanıcının bilgilerini döndür."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": {"id": current_user.role_id, "name": current_user.role.name},
        "department_id": current_user.department_id
    }