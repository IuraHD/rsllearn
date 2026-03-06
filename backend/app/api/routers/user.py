from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db import crud, database, models
from ...schemas import schemas
from ...core import auth as auth_utils

router = APIRouter()

@router.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(auth_utils.get_current_user)):
    return {
        "success": True,
        "data": {
            "user": current_user
        }
    }

@router.put("/profile", response_model=schemas.UserResponse)
def update_profile(
    user_update: schemas.UserUpdate,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(database.get_db)
):
    updated_user = crud.update_user(db, current_user.id, user_update)
    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "user": updated_user
        }
    }

@router.post("/complete-lesson", response_model=schemas.CompleteLessonResponse)
def complete_lesson(
    lesson_data: schemas.CompleteLessonRequest,
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(database.get_db)
):
    updated_user, new_badges = crud.record_progress(db, current_user.id, lesson_data)
    return {
        "success": True,
        "message": "Lesson completed successfully",
        "data": {
            "user": updated_user,
            "new_badges": new_badges
        }
    }

@router.get("/progress", response_model=schemas.ProgressResponse)
def get_progress(
    current_user: models.User = Depends(auth_utils.get_current_user),
    db: Session = Depends(database.get_db)
):
    progress = crud.get_user_progress(db, current_user.id)
    return {
        "success": True,
        "data": {
            "progress": progress
        }
    }

@router.get("/leaderboard", response_model=schemas.LeaderboardResponse)
def get_leaderboard(
    db: Session = Depends(database.get_db),
    limit: int = 10
):
    users = db.query(models.User).order_by(models.User.xp.desc()).limit(limit).all()
    
    leaderboard_data = []
    for user in users:
        leaderboard_data.append({
            "user_id": user.id,
            "name": user.name,
            "xp": user.xp,
            "level": user.level
        })
        
    return {
        "success": True,
        "data": {
            "leaderboard": leaderboard_data
        }
    }
