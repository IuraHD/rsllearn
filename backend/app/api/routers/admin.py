from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

import uuid
import os
from ...db import database, models
from ...schemas import schemas
from ...core import auth as auth_utils

router = APIRouter()

# --- Request Models Moved to schemas.py ---

# --- Helpers ---
def generate_id(prefix: str) -> str:
    return f"{prefix}_{str(uuid.uuid4()).split('-')[0]}"

def get_or_404(db: Session, model, item_id: str, item_name: str = "Item"):
    item = db.query(model).filter(model.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{item_name} not found")
    return item

# --- Admin Dependency ---
def get_current_admin(current_user: models.User = Depends(auth_utils.get_current_user)):
    admin_email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    if not admin_email:
        # Fallback or secure default: if no admin email configured, no one is admin
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access not configured")
    
    if (current_user.email or "").strip().lower() != admin_email:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return current_user

# --- Endpoints ---

@router.get("/content", response_model=schemas.AdminContentResponse)
def get_admin_content(db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    units = db.query(models.Unit).options(
        joinedload(models.Unit.lessons).joinedload(models.Lesson.tasks)
    ).order_by(models.Unit.order).all()
    
    # Sort in-memory because joinedload doesn't guarantee nested order without complex queries
    for u in units:
        u.lessons.sort(key=lambda x: x.order)
        for l in u.lessons:
            l.tasks.sort(key=lambda x: x.order_index)

    return {"success": True, "data": units}

@router.post("/units")
def create_unit(unit: schemas.AdminUnitCreate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    new_unit = models.Unit(
        id=generate_id("unit"),
        title=unit.title,
        description=unit.description,
        order=unit.order_index,
        is_published=unit.is_published
    )
    db.add(new_unit)
    db.commit()
    db.refresh(new_unit)
    return {"success": True, "data": {"id": new_unit.id}}

@router.put("/units/{unit_id}")
def update_unit(unit_id: str, unit: schemas.AdminUnitUpdate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_unit = get_or_404(db, models.Unit, unit_id, "Unit")
    
    db_unit.title = unit.title
    db_unit.description = unit.description
    db_unit.order = unit.order_index
    db_unit.is_published = unit.is_published
    
    db.commit()
    return {"success": True}

@router.delete("/units/{unit_id}")
def delete_unit(unit_id: str, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    print(f"Attempting to delete unit: {unit_id}")
    db_unit = get_or_404(db, models.Unit, unit_id, "Unit")
    
    try:
        db.delete(db_unit)
        db.commit()
        print(f"Unit {unit_id} deleted successfully")
        return {"success": True}
    except Exception as e:
        print(f"Error deleting unit {unit_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/lessons")
def create_lesson(lesson: schemas.AdminLessonCreate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    new_lesson = models.Lesson(
        id=generate_id("lesson"),
        unit_id=lesson.unit_id,
        title=lesson.title,
        description=lesson.description,
        xp=lesson.xp_reward,
        order=lesson.order_index,
        is_published=lesson.is_published,
        achievement_id=lesson.achievement_id
    )
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return {"success": True, "data": {"id": new_lesson.id}}

@router.put("/lessons/{lesson_id}")
def update_lesson(lesson_id: str, lesson: schemas.AdminLessonUpdate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_lesson = get_or_404(db, models.Lesson, lesson_id, "Lesson")
    
    db_lesson.title = lesson.title
    db_lesson.description = lesson.description
    db_lesson.xp = lesson.xp_reward
    db_lesson.order = lesson.order_index
    db_lesson.is_published = lesson.is_published
    db_lesson.achievement_id = lesson.achievement_id
    
    db.commit()
    return {"success": True}

@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: str, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_lesson = get_or_404(db, models.Lesson, lesson_id, "Lesson")
    
    db.delete(db_lesson)
    db.commit()
    return {"success": True}

@router.post("/tasks")
def create_task(task: schemas.AdminTaskCreate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    # Ensure options is a list if it's a string
    options_data = task.options
    if isinstance(options_data, str):
        import json
        try:
            options_data = json.loads(options_data)
        except:
            options_data = []

    expected_label = (task.expected_label or "").strip() or None
    new_task = models.Task(
        id=generate_id("task"),
        lesson_id=task.lesson_id,
        type=task.type,
        prompt=task.prompt_text,
        order_index=task.order_index,
        video_url=task.sign_video_url,
        options=options_data,

        expected_label=expected_label,
        min_confidence=task.min_confidence
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"success": True, "data": {"id": new_task.id}}

@router.put("/tasks/{task_id}")
def update_task(task_id: str, task: schemas.AdminTaskUpdate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_task = get_or_404(db, models.Task, task_id, "Task")
    
    options_data = task.options
    if isinstance(options_data, str):
        import json
        try:
            options_data = json.loads(options_data)
        except:
            pass # Keep as is or handle error

    db_task.prompt = task.prompt_text
    db_task.order_index = task.order_index
    db_task.type = task.type
    if options_data is not None:
        db_task.options = options_data
    if task.sign_video_url is not None:
        db_task.video_url = task.sign_video_url


    # Only update these if explicitly provided by the client.
    if "expected_label" in task.model_fields_set:
        db_task.expected_label = (task.expected_label or "").strip() or None
    if "min_confidence" in task.model_fields_set:
        db_task.min_confidence = task.min_confidence
    
    db.commit()
    return {"success": True}

@router.delete("/tasks/{task_id}")
def delete_task(task_id: str, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_task = get_or_404(db, models.Task, task_id, "Task")
    
    db.delete(db_task)
    db.commit()
    return {"success": True}

# --- Achievements Endpoints ---
@router.get("/achievements", response_model=schemas.AdminAchievementsResponse)
def get_achievements(db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    achievements = db.query(models.Achievement).all()
    return {"success": True, "data": achievements}

@router.post("/achievements")
def create_achievement(ach: schemas.AdminAchievementCreate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    new_ach = models.Achievement(
        id=generate_id("ach"),
        title=ach.title,
        description=ach.description,
        icon=ach.icon,
        condition_type=ach.condition_type,
        condition_value=ach.condition_value
    )
    db.add(new_ach)
    db.commit()
    db.refresh(new_ach)
    return {"success": True, "data": new_ach}

@router.put("/achievements/{ach_id}")
def update_achievement(ach_id: str, ach: schemas.AdminAchievementUpdate, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_ach = get_or_404(db, models.Achievement, ach_id, "Achievement")
    
    db_ach.title = ach.title
    db_ach.description = ach.description
    db_ach.icon = ach.icon
    db_ach.condition_type = ach.condition_type
    db_ach.condition_value = ach.condition_value
    
    db.commit()
    return {"success": True}

@router.delete("/achievements/{ach_id}")
def delete_achievement(ach_id: str, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    db_ach = get_or_404(db, models.Achievement, ach_id, "Achievement")
    
    db.delete(db_ach)
    db.commit()
    return {"success": True}

# --- Reorder Endpoints ---

# Reorder Models Moved to schemas.py

@router.post("/units/reorder")
def reorder_units(request: schemas.ReorderRequest, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    for item in request.items:
        db_unit = db.query(models.Unit).filter(models.Unit.id == item.id).first()
        if db_unit:
            db_unit.order = item.orderIndex
    db.commit()
    return {"success": True}

@router.post("/lessons/reorder")
def reorder_lessons(request: schemas.ReorderRequest, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    for item in request.items:
        db_lesson = db.query(models.Lesson).filter(models.Lesson.id == item.id).first()
        if db_lesson:
            db_lesson.order = item.orderIndex
    db.commit()
    return {"success": True}

@router.post("/tasks/reorder")
def reorder_tasks(request: schemas.ReorderRequest, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    for item in request.items:
        db_task = db.query(models.Task).filter(models.Task.id == item.id).first()
        if db_task:
            db_task.order_index = item.orderIndex
    db.commit()
    return {"success": True}

@router.post("/reorder")
def reorder_content(req: schemas.SmartReorderRequest, db: Session = Depends(database.get_db), admin: models.User = Depends(get_current_admin)):
    model = None
    parent_field = None
    order_field = 'order'
    
    if req.type == 'unit':
        model = models.Unit
    elif req.type == 'lesson':
        model = models.Lesson
        parent_field = 'unit_id'
    elif req.type == 'task':
        model = models.Task
        parent_field = 'lesson_id'
        order_field = 'order_index'
        
    if not model:
        raise HTTPException(400, "Invalid type")
        
    query = db.query(model)
    if parent_field:
        if not req.parent_id:
             raise HTTPException(400, "Parent ID required")
        query = query.filter(getattr(model, parent_field) == req.parent_id)
        
    items = query.all()
    # Sort items by current order
    items.sort(key=lambda x: getattr(x, order_field))
    
    # Find item to move
    # Note: req.id is from frontend, which sends `id` (db id)
    item_to_move = next((i for i in items if str(i.id) == req.id), None)
    
    if not item_to_move:
        raise HTTPException(404, "Item not found")
        
    items.remove(item_to_move)
    
    # Clamp new_index
    new_index = max(0, min(req.new_index, len(items)))
    
    items.insert(new_index, item_to_move)
    
    # Update order
    for idx, item in enumerate(items):
        setattr(item, order_field, idx) # 0-based index
        
    db.commit()
    return {"success": True}
