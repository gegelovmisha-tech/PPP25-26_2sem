from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Source(Base):
    __tablename__ = "sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    url = Column(String(500))
    type = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("Item", back_populates="source", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String(100), index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Float, default=0.0)
    category = Column(String(100))
    source_id = Column(Integer, ForeignKey("sources.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    source = relationship("Source", back_populates="items")
    events = relationship("ItemEvent", back_populates="item", cascade="all, delete-orphan")

class ItemEvent(Base):
    __tablename__ = "item_events"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id"))
    event_type = Column(String(50))
    old_value = Column(String(500))
    new_value = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    item = relationship("Item", back_populates="events")
