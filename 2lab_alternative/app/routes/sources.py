from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/", response_model=List[schemas.SourceOut])
def get_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Source).offset(skip).limit(limit).all()

@router.get("/{source_id}", response_model=schemas.SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not source:
        raise HTTPException(404, "Source not found")
    return source

@router.get("/{source_id}/items", response_model=List[schemas.ItemOut])
def get_source_items(source_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Item).filter(models.Item.source_id == source_id).offset(skip).limit(limit).all()

@router.post("/", response_model=schemas.SourceOut, status_code=201)
def create_source(source: schemas.SourceCreate, db: Session = Depends(get_db)):
    db_source = models.Source(**source.model_dump())
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.put("/{source_id}", response_model=schemas.SourceOut)
def update_source(source_id: int, source: schemas.SourceCreate, db: Session = Depends(get_db)):
    db_source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not db_source:
        raise HTTPException(404, "Source not found")
    for key, value in source.model_dump().items():
        setattr(db_source, key, value)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.patch("/{source_id}", response_model=schemas.SourceOut)
def patch_source(source_id: int, source: schemas.SourceUpdate, db: Session = Depends(get_db)):
    db_source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not db_source:
        raise HTTPException(404, "Source not found")
    for key, value in source.model_dump(exclude_unset=True).items():
        setattr(db_source, key, value)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    db_source = db.query(models.Source).filter(models.Source.id == source_id).first()
    if not db_source:
        raise HTTPException(404, "Source not found")
    db.delete(db_source)
    db.commit()
    return None
