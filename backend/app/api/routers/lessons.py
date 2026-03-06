from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...schemas import schemas
from ...db import database, models
from ...core import auth as auth_utils

router = APIRouter()

@router.get("/learning-path", response_model=schemas.LearningPathResponse)
def get_learning_path(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth_utils.get_current_user)
):
    # Fetch units sorted by order
    units = db.query(models.Unit).order_by(models.Unit.order).all()

    path = []
    for unit in units:
        # Fetch lessons for this unit sorted by order
        lessons = db.query(models.Lesson).filter(models.Lesson.unit_id == unit.id).order_by(models.Lesson.order).all()
        
        lessons_schema = []
        for l in lessons:
            lessons_schema.append({
                "id": l.id,
                "title": l.title,
                "xp": l.xp,
                "tasks": [] # Tasks not needed for path view
            })
        path.append({
            "id": unit.id,
            "title": unit.title,
            "lessons": lessons_schema
        })
        
    return {
        "success": True,
        "data": {
            "learning_path": path
        }
    }

@router.get("/lesson/{lesson_id}", response_model=schemas.LessonResponse)
def get_lesson(lesson_id: str, db: Session = Depends(database.get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
        
    unit = db.query(models.Unit).filter(models.Unit.id == lesson.unit_id).first()
    
    # Fetch tasks from Task table
    tasks = db.query(models.Task).filter(models.Task.lesson_id == lesson_id).order_by(models.Task.order_index).all()
    
    mapped_tasks = []
    for t in tasks:
        mapped_tasks.append({
            "id": t.id,
            "type": t.type,
            "prompt": t.prompt,
            "video_url": t.video_url,
            "options": t.options,

            "expected_label": t.expected_label,
            "min_confidence": t.min_confidence,
        })

    return {
        "success": True,
        "data": {
            "lesson": {
                "id": lesson.id,
                "title": lesson.title,
                "xp": lesson.xp,
                "tasks": mapped_tasks
            },
            "unit": {
                "id": unit.id,
                "title": unit.title
            }
        }
    }

@router.get("/achievements", response_model=schemas.AchievementsResponse)
def get_achievements(db: Session = Depends(database.get_db)):
    # Fetch from DB now
    achievements = db.query(models.Achievement).all()
    
    # If empty, return hardcoded fallback or empty list?
    # Let's return empty list if DB is empty, assuming seed will handle it.
    # But for now, let's keep the hardcoded fallback if DB is empty to avoid breaking UI immediately
    # Return empty list if no achievements found, or let frontend handle it
    if not achievements:
        achievements = []
    
    return {
        "success": True,
        "data": {
            "achievements": achievements
        }
    }
