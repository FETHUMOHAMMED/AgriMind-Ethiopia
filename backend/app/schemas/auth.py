from pydantic import BaseModel, ConfigDict, EmailStr

class UserRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    email: EmailStr          # automatically validates email format
    password: str
    phone: str | None = None
    language: str = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
