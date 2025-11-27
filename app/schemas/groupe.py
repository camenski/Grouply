from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel


class GroupeBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: Optional[int] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None

class GroupeRead(GroupeBase):
    id: int
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    owner: Optional[int] = None             
    members: List[int] = []                 
    tasks: List[int] = []                   

    class Config:
        orm_mode = True
