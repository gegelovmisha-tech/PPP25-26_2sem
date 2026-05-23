from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/events", tags=["events"])

@router.get("/", response_model=List[schemas.ItemEventOut])
def get_events(skip: int = 0, limit: int = 100, event_type: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.ItemEvent)
    if event_type:
        query = query.filter(models.ItemEvent.event_type == event_type)
    return query.order_by(models.ItemEvent.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/stats")
def get_event_stats(db: Session = Depends(get_db)):
    stats = db.query(models.ItemEvent.event_type, func.count(models.ItemEvent.id).label("count")).group_by(models.ItemEvent.event_type).all()
    return {"stats": [{"type": s[0], "count": s[1]} for s in stats]}
