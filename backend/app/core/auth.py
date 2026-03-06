from fastapi import Depends, Header, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..db import crud, database

# Password hashing context (keep this for security even in prototype)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# Simple Authentication for Prototype
# Expects header "X-User-Id: <user_id>"
def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    db: Session = Depends(database.get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user identity",
    )

    if not x_user_id:
        raise credentials_exception

    user = crud.get_user(db, user_id=x_user_id.strip())
    if user is None:
        raise credentials_exception

    return crud.sync_admin_flag(db, user)
