"""
models.py — Defines the database table(s) as Python classes (ORM Models).

Each class = one table.
Each class attribute = one column.

SQLAlchemy reads these models and creates the actual SQL table for us.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base


class Task(Base):
    """
    The Task model maps to the 'tasks' table in SQLite.

    Columns:
        id          — Auto-incrementing primary key (unique ID per task)
        title       — The task's main text (required, max 200 chars)
        description — Optional extra details about the task
        completed   — True if the task is done, False if pending
        priority    — "low", "medium", or "high"
        due_date    — Optional deadline (stored as a string "YYYY-MM-DD")
        created_at  — Automatically set to the current time when task is created
        updated_at  — Automatically updated whenever the task is modified
    """

    __tablename__ = "tasks"  # Name of the table in SQLite

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)                # required
    description = Column(String(500), nullable=True)           # optional
    completed = Column(Boolean, default=False)                 # default: pending
    priority = Column(String(10), default="medium")            # low/medium/high
    due_date = Column(String(10), nullable=True)               # "YYYY-MM-DD"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
