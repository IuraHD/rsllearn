from sqlalchemy import text
from backend.app.db.database import engine, Base
from backend.app.db.models import User, Unit, Lesson, Achievement, Progress

def reset_database():
    print("Dropping all tables with CASCADE...")
    with engine.connect() as connection:
        # Drop tables that might exist from previous backend or current one
        # Using CASCADE to handle foreign keys
        tables_to_drop = [
            "tasks", 
            "lessons", 
            "units", 
            "users", 
            "achievements", 
            "progress", 
            "SequelizeMeta"
        ]
        
        for table in tables_to_drop:
            try:
                connection.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
                print(f"Dropped table {table}")
            except Exception as e:
                print(f"Error dropping {table}: {e}")
        
        connection.commit()
    
    print("Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")

if __name__ == "__main__":
    reset_database()
