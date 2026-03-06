from pathlib import Path
from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
ENV_PATH = PROJECT_DIR / ".env"

# Load environment variables from project root .env
load_dotenv(ENV_PATH)

DATABASE_DIR = BACKEND_DIR / "database"
DEFAULT_SQLITE_DB_PATH = DATABASE_DIR / "sql_app.db"

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
]
