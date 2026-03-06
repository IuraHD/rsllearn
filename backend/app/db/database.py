import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from ..core.config import BACKEND_DIR, DEFAULT_SQLITE_DB_PATH


# SQLite-only database setup for this prototype
DEFAULT_SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DEFAULT_SQLITE_URL = f"sqlite:///{DEFAULT_SQLITE_DB_PATH.as_posix()}"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

if not SQLALCHEMY_DATABASE_URL.startswith("sqlite:///"):
    raise ValueError("Only SQLite DATABASE_URL values are supported in this prototype.")

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Enable Foreign Keys for SQLite


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    try:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except Exception:
        import traceback

        (BACKEND_DIR / "db_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
