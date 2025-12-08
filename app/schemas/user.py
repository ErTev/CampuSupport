from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    # Şifre kısıtlaması (6 ile 15 karakter arası) eklendi
    password: str = Field(min_length=6, max_length=15)
    role_name: str = "student" # Varsayılan: öğrenci

class UserLogin(BaseModel):
    username: str # E-posta olarak kullanılacak
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role_id: int
    department_id: Optional[int] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str