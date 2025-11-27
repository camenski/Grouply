
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TacheBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_id: Optional[int] = None
    due_date: Optional[str] = None


class TacheUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None


class TacheRead(TacheBase):
    id: int
    group_id: int
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    completed: bool = False

    class Config:
        orm_mode = True
