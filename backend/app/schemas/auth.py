from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    full_name: str
    email: EmailStr          # automatically validates email format
    password: str
    phone: str | None = None
    language: str = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str