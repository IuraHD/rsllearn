from sqlalchemy.orm import Session
from typing import List, Tuple

from ..db import models


def check_achievements(
    db: Session, user: models.User, completed_lesson_id: str, unit_id: str
) -> Tuple[List[str], List[str]]:
    """
    Checks for new achievements after a lesson is completed.
    Returns a list of new achievement IDs earned.
    """
    new_badges = []
    current_badges = list(user.badges)
    completed_lessons = list(user.completed_lessons)

    # 1. Lesson-specific achievement
    lesson = db.query(models.Lesson).filter(models.Lesson.id == completed_lesson_id).first()
    if lesson and lesson.achievement_id:
        if lesson.achievement_id not in current_badges:
            current_badges.append(lesson.achievement_id)
            new_badges.append(lesson.achievement_id)

    # 2. First lesson completed
    if len(completed_lessons) == 1 and "ach_start" not in current_badges:
        current_badges.append("ach_start")
        new_badges.append("ach_start")

    # 3. Check all other achievements
    all_achievements = db.query(models.Achievement).all()
    
    # Pre-fetch unit lessons to avoid N+1 in loop if possible, 
    # but for now we just filter what we need.
    
    # Check Unit Completion if unit_id is provided
    if unit_id:
        unit_lessons = db.query(models.Lesson).filter(models.Lesson.unit_id == unit_id).all()
        if unit_lessons:
            unit_lesson_ids = [l.id for l in unit_lessons]
            is_unit_complete = all(lid in completed_lessons for lid in unit_lesson_ids)
            
            if is_unit_complete:
                for ach in all_achievements:
                    if ach.id in current_badges: continue
                    if ach.condition_type == "unit_completed" and ach.condition_value == unit_id:
                        current_badges.append(ach.id)
                        new_badges.append(ach.id)

    # General condition checks
    for ach in all_achievements:
        if ach.id in current_badges: continue
        
        if ach.condition_type == "xp_threshold":
            try:
                if user.xp >= int(ach.condition_value):
                    current_badges.append(ach.id)
                    new_badges.append(ach.id)
            except (ValueError, TypeError): pass
            
        elif ach.condition_type == "lessons_completed":
            try:
                if len(completed_lessons) >= int(ach.condition_value):
                    current_badges.append(ach.id)
                    new_badges.append(ach.id)
            except (ValueError, TypeError): pass
            
        elif ach.condition_type == "streak":
            try:
                if user.daily_streak >= int(ach.condition_value):
                    current_badges.append(ach.id)
                    new_badges.append(ach.id)
            except (ValueError, TypeError): pass

    return new_badges, current_badges
