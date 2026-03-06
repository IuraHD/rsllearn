from sqlalchemy import inspect
from backend.app.db.database import engine

def inspect_db():
    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    for column in columns:
        print(f"Column: {column['name']} - {column['type']}")

if __name__ == "__main__":
    inspect_db()
