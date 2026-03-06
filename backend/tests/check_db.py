import sqlite3
from pathlib import Path

def check_schema():
    try:
        db_path = Path(__file__).resolve().parents[1] / "database" / "sql_app.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("--- Lessons Table Info ---")
        cursor.execute("PRAGMA table_info(lessons)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        print("\n--- Achievements Table Info ---")
        cursor.execute("PRAGMA table_info(achievements)")
        columns = cursor.fetchall()
        for col in columns:
            print(col)
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
