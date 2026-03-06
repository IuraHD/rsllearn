from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models
from ..schemas import schemas
from passlib.context import CryptContext
import uuid
import os
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    normalized_email = email.strip().lower()
    return db.query(models.User).filter(func.lower(models.User.email) == normalized_email).first()

def is_admin_email(email: str | None) -> bool:
    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    user_email = (email or "").strip().lower()
    return bool(admin_email and user_email and user_email == admin_email)

def sync_admin_flag(db: Session, db_user: models.User) -> models.User:
    should_be_admin = is_admin_email(db_user.email)
    if db_user.is_admin != should_be_admin:
        db_user.is_admin = should_be_admin
        db.commit()
        db.refresh(db_user)
    return db_user

def create_user(db: Session, user: schemas.UserCreate):
    normalized_email = user.email.strip().lower()

    db_user = models.User(
        id=str(uuid.uuid4()), 
        email=normalized_email,
        name=user.name,
        hashed_password=get_password_hash(user.password),
        xp=0,
        daily_streak=0,
        level=1,
        level_progress=0,
        badges=[],
        is_admin=is_admin_email(normalized_email),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    if user_update.name:
        db_user.name = user_update.name
    db.commit()
    db.refresh(db_user)
    return db_user

def record_progress(db: Session, user_id: str, data: schemas.CompleteLessonRequest):
    db_user = get_user(db, user_id)
    if not db_user:
        return None, []

    # Update User Stats
    db_user.xp += data.xp_earned
    
    # Update Streak
    now = datetime.now()
    today = now.date()
    
    if db_user.last_practice_date:
        last_practice = db_user.last_practice_date.date()
        if last_practice == today:
            pass # Already practiced today
        elif last_practice == today - timedelta(days=1):
            db_user.daily_streak += 1
        else:
            db_user.daily_streak = 1 # Reset streak
    else:
        db_user.daily_streak = 1 # First time
        
    db_user.last_practice_date = now
    
    # Simple level logic (example: 1000 XP per level)
    # This should probably match the frontend logic or be more complex
    current_level_xp = (db_user.level - 1) * 1000
    xp_in_level = db_user.xp - current_level_xp
    if xp_in_level >= 1000:
        db_user.level += 1
        db_user.level_progress = 0
    else:
        db_user.level_progress = int((xp_in_level / 1000) * 100)

    # Create Progress Record
    progress_record = models.Progress(
        user_id=user_id,
        lesson_id=data.lesson_id,
        unit_id=data.unit_id,
        xp_earned=data.xp_earned,
        tasks_completed=data.tasks_completed,
        total_tasks=data.total_tasks,
        mistakes=data.mistakes,
        is_perfect=(data.mistakes == 0)
    )
    db.add(progress_record)

    # Calculate Achievements using Service
    from ..services.achievement_service import check_achievements
    new_badges, updated_badges_list = check_achievements(db, db_user, data.lesson_id, data.unit_id)
    
    # 3. Built-in achievements specific to this function (Perfect Lesson)
    # We keep "ach_perfect" here because it depends on `data.mistakes` which is only available in this scope
    if data.mistakes == 0 and "ach_perfect" not in updated_badges_list:
        updated_badges_list.append("ach_perfect")
        new_badges.append("ach_perfect")
        
    db_user.badges = updated_badges_list
    
    db.commit()
    db.refresh(db_user)
    
    return db_user, new_badges

def get_user_progress(db: Session, user_id: str):
    return db.query(models.Progress).filter(models.Progress.user_id == user_id).all()

