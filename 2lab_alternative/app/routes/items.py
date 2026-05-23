from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=List[schemas.ItemOut])
def get_items(skip: int = 0, limit: int = 100, category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, db: Session = Depends(get_db)):
    query = db.query(models.Item)
    if category:
        query = query.filter(models.Item.category == category)
    if min_price:
        query = query.filter(models.Item.price >= min_price)
    if max_price:
        query = query.filter(models.Item.price <= max_price)
    return query.offset(skip).limit(limit).all()

@router.get("/{item_id}", response_model=schemas.ItemWithSource)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    return item

@router.get("/{item_id}/events", response_model=List[schemas.ItemEventOut])
def get_item_events(item_id: int, db: Session = Depends(get_db)):
    return db.query(models.ItemEvent).filter(models.ItemEvent.item_id == item_id).all()

@router.post("/", response_model=schemas.ItemOut, status_code=201)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == item.source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    event = models.ItemEvent(item_id=db_item.id, event_type="created", new_value=db_item.name)
    db.add(event)
    db.commit()
    return db_item

@router.put("/{item_id}", response_model=schemas.ItemOut)
def update_item(item_id: int, item: schemas.ItemCreate, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")
    for key, value in item.model_dump().items():
        setattr(db_item, key, value)
    db_item.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_item)
    return db_item

@router.patch("/{item_id}", response_model=schemas.ItemOut)
def patch_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")
    changes = []
    for key, value in item.model_dump(exclude_unset=True).items():
        old_val = getattr(db_item, key)
        if old_val != value:
            changes.append(f"{key}: {old_val} -> {value}")
            setattr(db_item, key, value)
    if changes:
        db_item.updated_at = datetime.utcnow()
        event = models.ItemEvent(item_id=item_id, event_type="updated", old_value=", ".join(changes), new_value=db_item.name)
        db.add(event)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item not found")
    event = models.ItemEvent(item_id=item_id, event_type="deleted", old_value=db_item.name)
    db.add(event)
    db.delete(db_item)
    db.commit()
    return None
