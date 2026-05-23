from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class SourceBase(BaseModel):
    name: str
    url: Optional[str] = None
    type: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None

class SourceOut(SourceBase):
    id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    category: Optional[str] = None
    external_id: Optional[str] = None

class ItemCreate(ItemBase):
    source_id: int

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None

class ItemOut(ItemBase):
    id: int
    source_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ItemWithSource(ItemOut):
    source: SourceOut

class ItemEventOut(BaseModel):
    id: int
    item_id: int
    event_type: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
