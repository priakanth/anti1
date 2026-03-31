"""
schemas.py — Pydantic schemas for input validation and response shaping.

Pydantic is FastAPI's built-in validation library.
When a user sends JSON to our API, Pydantic:
  1. Checks that required fields are present
  2. Validates types (e.g., due_date must be a string)
  3. Rejects bad requests automatically with a clear error message

We use 3 schemas:
  - TaskCreate  → for creating a new task (POST body)
  - TaskUpdate  → for editing a task (PUT body) — all fields optional
  - TaskOut     → what the API sends back (response shape)
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


# -----------------------------------------------------------------------
# Shared base with common validation logic
# -----------------------------------------------------------------------
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200,
                       description="Task title (required)")
    description: Optional[str] = Field(None, max_length=500,
                                       description="Optional details")
    priority: Optional[str] = Field("medium",
                                    description="Priority: low | medium | high")
    due_date: Optional[str] = Field(None,
                                    description="Due date in YYYY-MM-DD format")

    # Validate priority — only allow "low", "medium", or "high"
    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {', '.join(allowed)}")
        return v

    # Validate due_date format
    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("due_date must be in YYYY-MM-DD format")
        return v


# -----------------------------------------------------------------------
# Schema for creating a new task (POST /tasks)
# -----------------------------------------------------------------------
class TaskCreate(TaskBase):
    pass  # Inherits everything from TaskBase


# -----------------------------------------------------------------------
# Schema for updating an existing task (PUT /tasks/{id})
# All fields are optional — the user can update just what they want
# -----------------------------------------------------------------------
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is None:
            return v
        allowed = {"low", "medium", "high"}
        if v not in allowed:
            raise ValueError(f"Priority must be one of: {', '.join(allowed)}")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        if v is None:
            return v
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("due_date must be in YYYY-MM-DD format")
        return v


# -----------------------------------------------------------------------
# Schema for API responses (GET /tasks, POST /tasks, etc.)
# This controls exactly what data we send back to the frontend
# -----------------------------------------------------------------------
class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    # orm_mode (now called from_attributes in Pydantic v2) lets Pydantic
    # read data from SQLAlchemy model objects (not just plain dicts)
    model_config = {"from_attributes": True}
