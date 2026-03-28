import json
import os
from pathlib import Path
import sys
import traceback

# Add backend root to sys.path to resolve imports
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.db.database import SessionLocal, engine, Base
from app.db import crud
from app.db.models import Unit, Lesson, Task, Achievement, User

# Seed fixture is intentionally colocated under tests/
DATA_PATH = Path(__file__).resolve().parent / "fixtures" / "contentSeed.json"

def load_data():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def _dedupe_keep_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _build_unit_sign_pools(lessons):
    pools = {}
    for lesson in lessons:
        unit_id = lesson["unitId"]
        pools.setdefault(unit_id, [])
        pools[unit_id].extend(lesson.get("signs", []))

    return {unit_id: _dedupe_keep_order(signs) for unit_id, signs in pools.items()}


def _pick_distractors(unit_pool, lesson_signs, target_sign, count=3):
    ordered = [sign for sign in lesson_signs if sign != target_sign]
    ordered.extend(sign for sign in unit_pool if sign != target_sign and sign not in ordered)
    return ordered[:count]


def _rotate_options(options, seed):
    if not options:
        return options
    offset = seed % len(options)
    return options[offset:] + options[:offset]


def _build_text_options(lesson_id, task_id, target_sign, distractor_signs, seed):
    option_signs = _rotate_options([target_sign, *distractor_signs], seed)
    return [
        {
            "id": f"{task_id}-opt-{index + 1}",
            "text": sign,
            "isCorrect": sign == target_sign,
        }
        for index, sign in enumerate(option_signs)
    ]


def _build_video_options(task_id, target_sign, distractor_signs, seed):
    option_signs = _rotate_options([target_sign, *distractor_signs], seed)
    return [
        {
            "id": f"{task_id}-opt-{index + 1}",
            "videoUrl": f"{sign}.mp4",
            "isCorrect": sign == target_sign,
        }
        for index, sign in enumerate(option_signs)
    ]


def generate_tasks_from_lessons(lessons):
    tasks = []
    unit_sign_pools = _build_unit_sign_pools(lessons)

    for lesson in lessons:
        lesson_id = lesson["id"]
        unit_id = lesson["unitId"]
        lesson_signs = lesson.get("signs", [])
        task_index = 1

        for sign in lesson_signs:
            tasks.append({
                "id": f"{lesson_id}-repeat-{task_index}",
                "lessonId": lesson_id,
                "type": "REPEAT_SIGN",
                "orderIndex": task_index,
                "promptText": f"Invata semnul: {sign}",
                "expectedLabel": sign,
                "minConfidence": 0.7,
                "signVideoUrl": f"{sign}.mp4",
            })
            task_index += 1

            tasks.append({
                "id": f"{lesson_id}-text-{task_index}",
                "lessonId": lesson_id,
                "type": "TEXT_TO_SIGN",
                "orderIndex": task_index,
                "promptText": f"Arata semnul pentru '{sign}'",
                "expectedLabel": sign,
                "minConfidence": 0.75,
                "signVideoUrl": f"{sign}.mp4",
            })
            task_index += 1

        for sign_index, sign in enumerate(lesson_signs):
            distractors = _pick_distractors(unit_sign_pools[unit_id], lesson_signs, sign)
            task_id = f"{lesson_id}-quiz-text-{task_index}"
            tasks.append({
                "id": task_id,
                "lessonId": lesson_id,
                "type": "SIGN_TO_TEXT",
                "orderIndex": task_index,
                "promptText": "Ce semn este acesta?",
                "videoUrl": f"{sign}.mp4",
                "options": _build_text_options(
                    lesson_id=lesson_id,
                    task_id=task_id,
                    target_sign=sign,
                    distractor_signs=distractors,
                    seed=sign_index + 1,
                ),
            })
            task_index += 1

        for sign_index, sign in enumerate(lesson_signs):
            distractors = _pick_distractors(unit_sign_pools[unit_id], lesson_signs, sign)
            task_id = f"{lesson_id}-quiz-video-{task_index}"
            tasks.append({
                "id": task_id,
                "lessonId": lesson_id,
                "type": "VIDEO_MULTIPLE_CHOICE",
                "orderIndex": task_index,
                "promptText": f"Care videoclip arata semnul '{sign}'?",
                "options": _build_video_options(
                    task_id=task_id,
                    target_sign=sign,
                    distractor_signs=distractors,
                    seed=sign_index + 2,
                ),
            })
            task_index += 1

    return tasks


def seed_default_admin(db):
    admin_email = (os.getenv("ADMIN_EMAIL") or "admin@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD") or "admin123"
    admin_name = (os.getenv("ADMIN_DISPLAY_NAME") or "Admin").strip() or "Admin"

    admin_user = User(
        id="admin-user",
        email=admin_email,
        name=admin_name,
        hashed_password=crud.get_password_hash(admin_password),
        xp=0,
        daily_streak=0,
        level=1,
        level_progress=0,
        badges=[],
        is_admin=True,
    )
    db.add(admin_user)
    db.commit()
    print(f"Seeded default admin user: {admin_email}")

def seed_database():
    print("Seeding database...")
    # Re-create tables to ensure schema matches
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        data = load_data()
        
        # Seed Units
        for u_data in data["units"]:
            unit = Unit(
                id=u_data["id"],
                title=u_data["title"],
                description=u_data["description"],
                order=u_data.get("orderIndex", 0),
                is_published=True, # Default to published for seed data
            )
            db.add(unit)
        db.commit()
        print(f"Seeded {len(data['units'])} units")

        # Seed Lessons
        for l_data in data["lessons"]:
            base_xp = l_data.get("xpRewardBase", 20)
                
            lesson = Lesson(
                id=l_data["id"],
                unit_id=l_data["unitId"],
                title=l_data["title"],
                description=l_data.get("description", ""),
                xp=base_xp,
                order=l_data.get("orderIndex", 0),
                is_published=True
            )
            db.add(lesson)
        db.commit()
        print(f"Seeded {len(data['lessons'])} lessons")
        
        # Seed Tasks
        task_count = 0
        task_seed_data = data.get("tasks") or generate_tasks_from_lessons(data["lessons"])
        for t_data in task_seed_data:
            task = Task(
                id=t_data["id"],
                lesson_id=t_data["lessonId"],
                type=t_data["type"],
                prompt=t_data.get("promptText", ""),
                order_index=t_data.get("orderIndex", 0),
                video_url=t_data.get("signVideoUrl") or t_data.get("videoUrl"),
                options=t_data.get("options"),

                expected_label=t_data.get("expectedLabel"),
                min_confidence=t_data.get("minConfidence")
            )
            db.add(task)
            task_count += 1
            
        db.commit()
        print(f"Seeded {task_count} tasks")
        
        # Seed Achievements
        achievements_data = [
            {
                "id": "ach_start",
                "title": "Primii Pași",
                "description": "Ai completat prima ta lecție. Felicitări!",
                "icon": "badge-start",
                "condition_type": "lessons_completed",
                "condition_value": "1"
            },
            {
                "id": "ach_streak_3",
                "title": "În Flăcări",
                "description": "Ai menținut un streak de 3 zile.",
                "icon": "fire",
                "condition_type": "streak",
                "condition_value": "3"
            },
            {
                "id": "ach_xp_100",
                "title": "Colecționar de XP",
                "description": "Ai câștigat 100 XP.",
                "icon": "badge-xp",
                "condition_type": "xp_threshold",
                "condition_value": "100"
            },
            {
                "id": "ach_unit_1",
                "title": "Absolvent Unit 1",
                "description": "Ai completat toate lecțiile din Unit 1.",
                "icon": "target",
                "condition_type": "unit_completed",
                "condition_value": "u1"
            },
            {
                "id": "ach_unit_2",
                "title": "Absolvent Unit 2",
                "description": "Ai completat toate lecțiile din Unit 2.",
                "icon": "medal",
                "condition_type": "unit_completed",
                "condition_value": "u2"
            },
            {
                "id": "ach_unit_3",
                "title": "Absolvent Unit 3",
                "description": "Ai completat toate lecțiile din Unit 3.",
                "icon": "badge-streak",
                "condition_type": "unit_completed",
                "condition_value": "u3"
            },
            {
                "id": "ach_perfect",
                "title": "Fara Greseli",
                "description": "Ai completat o lectie fara nicio greseala.",
                "icon": "badge-perfect",
                "condition_type": "manual",
                "condition_value": "perfect_lesson"
            },
            # Difficulty-based achievements removed (difficulty system no longer used).
        ]
        
        for ach_data in achievements_data:
            ach = Achievement(
                id=ach_data["id"],
                title=ach_data["title"],
                description=ach_data["description"],
                icon=ach_data["icon"],
                condition_type=ach_data["condition_type"],
                condition_value=ach_data["condition_value"]
            )
            db.add(ach)
        db.commit()
        print(f"Seeded {len(achievements_data)} achievements")

        seed_default_admin(db)
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
