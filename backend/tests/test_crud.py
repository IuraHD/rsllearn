from backend.app.db.database import SessionLocal, engine, Base
from backend.app.db import crud, models
from backend.app.schemas import schemas

def test_crud():
    db = SessionLocal()
    try:
        # Create tables if not exist (reset_db did it, but just in case)
        Base.metadata.create_all(bind=engine)
        
        email = "test@example.com"
        user = crud.get_user_by_email(db, email)
        print(f"User found: {user}")
        
        if not user:
            print("Creating user...")
            new_user = schemas.UserCreate(displayName="Test", email=email, password="pw")
            created = crud.create_user(db, new_user)
            print(f"Created user: {created.id}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_crud()
