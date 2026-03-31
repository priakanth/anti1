"""
crud.py — Database CRUD Operations (Create, Read, Update, Delete)

This file contains all the logic for interacting with the database.
By separating DB logic into crud.py, we keep routes in main.py clean
and follow the "separation of concerns" principle.

Each function receives a SQLAlchemy session (db) and does one job.
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

import models
import schemas


# -----------------------------------------------------------------------
# CREATE — Add a new task to the database
# -----------------------------------------------------------------------
def create_task(db: Session, task: schemas.TaskCreate) -> models.Task:
    """
    Converts the Pydantic schema into a SQLAlchemy model object,
    saves it to the DB, and returns the saved object (with its new ID).
    """
    db_task = models.Task(
        title=task.title,
        description=task.description,
        priority=task.priority or "medium",
        due_date=task.due_date,
        completed=False,  # New tasks are always pending
    )
    db.add(db_task)       # Stage the new record
    db.commit()           # Write to database
    db.refresh(db_task)   # Reload to get auto-generated fields (id, created_at)
    return db_task


# -----------------------------------------------------------------------
# READ — Get all tasks (with optional filtering and search)
# -----------------------------------------------------------------------
def get_tasks(
    db: Session,
    status: Optional[str] = None,   # "all" | "completed" | "pending"
    search: Optional[str] = None,   # search term for title/description
) -> list[models.Task]:
    """
    Queries all tasks. Supports:
    - Filtering by completion status
    - Searching by title or description (case-insensitive)
    """
    query = db.query(models.Task)

    # Filter by status
    if status == "completed":
        query = query.filter(models.Task.completed == True)
    elif status == "pending":
        query = query.filter(models.Task.completed == False)

    # Search in title or description
    if search:
        search_term = f"%{search}%"   # SQL LIKE wildcard
        query = query.filter(
            or_(
                models.Task.title.ilike(search_term),
                models.Task.description.ilike(search_term),
            )
        )

    # Sort: incomplete tasks first, then by creation date (newest first)
    query = query.order_by(
        models.Task.completed.asc(),
        models.Task.created_at.desc()
    )
    return query.all()


# -----------------------------------------------------------------------
# READ — Get a single task by ID
# -----------------------------------------------------------------------
def get_task(db: Session, task_id: int) -> Optional[models.Task]:
    """Returns a single task by its primary key, or None if not found."""
    return db.query(models.Task).filter(models.Task.id == task_id).first()


# -----------------------------------------------------------------------
# UPDATE — Edit an existing task
# -----------------------------------------------------------------------
def update_task(
    db: Session,
    task_id: int,
    updates: schemas.TaskUpdate
) -> Optional[models.Task]:
    """
    Applies only the provided fields to the task.
    If a field is None in the update schema, it is left unchanged.
    """
    db_task = get_task(db, task_id)
    if not db_task:
        return None  # Task not found — caller handles the 404

    # model_dump(exclude_unset=True) returns only fields the user actually sent
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)  # Dynamically set each field

    db.commit()
    db.refresh(db_task)
    return db_task


# -----------------------------------------------------------------------
# DELETE — Remove a task permanently
# -----------------------------------------------------------------------
def delete_task(db: Session, task_id: int) -> bool:
    """
    Deletes a task by ID.
    Returns True if deleted, False if task was not found.
    """
    db_task = get_task(db, task_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True
