"""
database.py — Sets up the SQLite database connection using SQLAlchemy.

SQLAlchemy is an ORM (Object Relational Mapper) — it lets us work with
the database using Python classes instead of raw SQL queries.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# -----------------------------------------------------------------------
# 1. Database URL
#    Reads from DATABASE_URL environment variable if set (useful for
#    Railway volumes: set DATABASE_URL=sqlite:////data/todo.db).
#    Falls back to a local file for development.
# -----------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo.db")

# -----------------------------------------------------------------------
# 2. Engine — the core connection to the database
#    check_same_thread=False is required for SQLite when used with FastAPI
#    because FastAPI uses multiple threads.
# -----------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# -----------------------------------------------------------------------
# 3. SessionLocal — a factory for creating database sessions.
#    Each request gets its own session (like a short-lived database connection).
#    autocommit=False → we manually commit changes
#    autoflush=False  → we control when changes are flushed to the DB
# -----------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -----------------------------------------------------------------------
# 4. Base — all our ORM models will inherit from this class.
#    SQLAlchemy uses it to track table definitions.
# -----------------------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------------------
# 5. Dependency — get_db()
#    FastAPI injects this into route functions via Depends(get_db).
#    It opens a session, yields it for use, then closes it automatically.
# -----------------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
