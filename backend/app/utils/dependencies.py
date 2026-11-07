from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.user import User
from app.utils.jwt import SECRET_KEY, ALGORITHM

security = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    # Role and contact data come from the current database record. JWT claims
    # are intentionally not used for authorization, so role changes take
    # effect without waiting for an old token to expire.
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return {"user_id": user.id, "email": user.email, "role": user.role}


def require_role(*allowed_roles: str):
    """Create a dependency that authorizes against the current DB user role."""
    normalized_roles = {role.strip().lower() for role in allowed_roles}

    async def role_dependency(current_user: dict = Depends(get_current_user)):
        current_role = str(current_user.get("role") or "").strip().lower()
        if current_role not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return role_dependency
