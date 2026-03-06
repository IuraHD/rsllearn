from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...core.config import BACKEND_DIR
from ...db import crud, database
from ...schemas import schemas

router = APIRouter()

@router.post("/register", response_model=schemas.AuthResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    try:
        db_user = crud.get_user_by_email(db, email=user.email)
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
        new_user = crud.create_user(db=db, user=user)
        
        # Prototype: return user directly (no auth token issued).
        return {
            "success": True,
            "message": "User registered successfully",
            "data": new_user
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        (BACKEND_DIR / "last_error.txt").write_text(error_msg, encoding="utf-8")
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=schemas.AuthResponse)
def login(user_credentials: schemas.UserLogin, db: Session = Depends(database.get_db)):
    user = crud.get_user_by_email(db, email=user_credentials.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not crud.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Keep admin flag in sync with ADMIN_EMAIL for existing users.
    user = crud.sync_admin_flag(db, user)
    
    # Prototype: return user directly (no auth token issued).
    return {
        "success": True,
        "message": "Login successful",
        "data": user
    }
