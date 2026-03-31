"""
main.py — FastAPI Application Entry Point

This is the heart of the backend.
All HTTP routes (endpoints) are defined here.
FastAPI automatically:
  - Validates request bodies using our Pydantic schemas
  - Generates interactive API docs at http://localhost:8000/docs
  - Handles JSON serialization/deserialization
"""

import os
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional

import crud
import models
import schemas
from database import engine, get_db

# Resolve the frontend directory regardless of where the process is launched from
# In Docker: /app/backend/../frontend = /app/frontend
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# -----------------------------------------------------------------------
# 1. Create all database tables on startup
#    This reads our models.py and creates the 'tasks' table in todo.db
#    if it doesn't already exist. Safe to run multiple times.
# -----------------------------------------------------------------------
models.Base.metadata.create_all(bind=engine)

# -----------------------------------------------------------------------
# 2. Create the FastAPI application instance
# -----------------------------------------------------------------------
app = FastAPI(
    title="To-Do List API",
    description="A RESTful API for managing tasks — built with FastAPI + SQLite",
    version="1.0.0",
)

# -----------------------------------------------------------------------
# 3. CORS Middleware
#    CORS = Cross-Origin Resource Sharing.
#    Without this, the browser would block our frontend (served on a different
#    port) from calling this API. We allow all origins for development.
# -----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production, replace * with your domain
    allow_credentials=True,
    allow_methods=["*"],        # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


# -----------------------------------------------------------------------
# ROUTE 1: Health Check (moved to /health so "/" stays free for the frontend)
# GET /health
# -----------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health():
    """Health check — useful for Railway's health probe."""
    return {"status": "ok", "message": "To-Do API is running 🚀"}


# -----------------------------------------------------------------------
# ROUTE 2: Get All Tasks
# GET /tasks?status=pending&search=groceries
#
# Query parameters (optional):
#   status  → "all" | "completed" | "pending"
#   search  → text to search in title or description
# -----------------------------------------------------------------------
@app.get("/tasks", response_model=list[schemas.TaskOut], tags=["Tasks"])
def get_tasks(
    status: Optional[str] = Query(None, description="Filter: all|completed|pending"),
    search: Optional[str] = Query(None, description="Search term for title/description"),
    db: Session = Depends(get_db),
):
    """Returns a list of all tasks, with optional filtering and search."""
    return crud.get_tasks(db, status=status, search=search)


# -----------------------------------------------------------------------
# ROUTE 3: Create a New Task
# POST /tasks
# Body: { "title": "Buy groceries", "priority": "high", "due_date": "2025-04-01" }
# -----------------------------------------------------------------------
@app.post("/tasks", response_model=schemas.TaskOut, status_code=201, tags=["Tasks"])
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """
    Creates a new task.
    Returns HTTP 201 (Created) with the newly created task.
    """
    return crud.create_task(db, task)


# -----------------------------------------------------------------------
# ROUTE 4: Get a Single Task by ID
# GET /tasks/5
# -----------------------------------------------------------------------
@app.get("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["Tasks"])
def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    Returns a single task by its ID.
    Raises HTTP 404 if the task doesn't exist.
    """
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# -----------------------------------------------------------------------
# ROUTE 5: Update a Task
# PUT /tasks/5
# Body: { "title": "Buy groceries and milk", "completed": true }
#
# Only send the fields you want to change — the rest stay the same.
# -----------------------------------------------------------------------
@app.put("/tasks/{task_id}", response_model=schemas.TaskOut, tags=["Tasks"])
def update_task(task_id: int, updates: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """
    Updates an existing task with partial data.
    Raises HTTP 404 if the task doesn't exist.
    """
    task = crud.update_task(db, task_id, updates)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


# -----------------------------------------------------------------------
# ROUTE 6: Delete a Task
# DELETE /tasks/5
# -----------------------------------------------------------------------
@app.delete("/tasks/{task_id}", tags=["Tasks"])
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Permanently deletes a task.
    Returns HTTP 404 if the task doesn't exist.
    Returns a success message if deleted.
    """
    deleted = crud.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return {"message": f"Task {task_id} deleted successfully"}


# -----------------------------------------------------------------------
# STATIC FILE SERVING — Frontend (HTML / CSS / JS)
#
# IMPORTANT: This MUST come LAST — FastAPI matches routes top-to-bottom.
# All /tasks routes above are matched first; everything else falls through
# to the static file handler, which serves index.html for "/".
# -----------------------------------------------------------------------
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    # Railway provides the PORT environment variable. Fallback to 8000 locally.
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)

