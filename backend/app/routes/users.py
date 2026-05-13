from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me")
async def read_users_me(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        return {"error": "User not found"}

    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "language": user.language,
        "role": user.role
    }