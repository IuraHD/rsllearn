import json
from pathlib import Path
import sys
import traceback

# Add backend root to sys.path to resolve imports
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

from app.db.database import SessionLocal, engine, Base
from app.db.models import Unit, Lesson, Task, Achievement

# Seed fixture is intentionally colocated under tests/
DATA_PATH = Path(__file__).resolve().parent / "fixtures" / "contentSeed.json"

def load_data():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

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
        for t_data in data["tasks"]:
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
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
