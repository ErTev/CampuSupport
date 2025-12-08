from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.config import settings

# JWT Kimlik Doğrulama Şeması
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_token(token: str, credentials_exception):
    """Token'ı doğrular ve payload'dan e-posta adresini döndürür."""
    try:
        # JWT'yi çözmek için SECRET_KEY ve ALGORITHM ayarlarını settings'ten çeker.
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Mevcut kullanıcıyı token'dan alır."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    email = verify_token(token, credentials_exception)
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

def get_department(current_user: User = Depends(get_current_user)):
    """Departman yöneticisi veya admin yetkisi kontrolü."""
    if current_user.role.name not in ["department", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işleme yetkiniz yok (Yalnızca Departman Yöneticisi/Admin)."
        )
    return current_user

def get_support(current_user: User = Depends(get_current_user)):
    """Destek personeli, departman yöneticisi veya admin yetkisi kontrolü."""
    if current_user.role.name not in ["support", "department", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işleme yetkiniz yok (Yalnızca Destek/Departman Yöneticisi/Admin)."
        )
    return current_user