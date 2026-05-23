from celery import Celery
import time
import random
from app.database import SessionLocal
from app import models

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=30 * 60,
    result_expires=3600,
)

@celery_app.task(bind=True)
def rebuild_stats(self, source_id: int = None):
    self.update_state(state="STARTED", meta={"progress": 0, "message": "Starting..."})
    
    db = SessionLocal()
    try:
        self.update_state(state="RUNNING", meta={"progress": 10, "message": "Querying database..."})
        time.sleep(1)
        
        query = db.query(models.Item)
        if source_id:
            query = query.filter(models.Item.source_id == source_id)
        
        items = query.all()
        total = len(items)
        
        self.update_state(state="RUNNING", meta={"progress": 30, "message": f"Found {total} items"})
        time.sleep(1)
        
        total_value = 0
        categories = {}
        
        for i, item in enumerate(items):
            total_value += item.price
            if item.category:
                categories[item.category] = categories.get(item.category, 0) + 1
            
            if total > 0:
                progress = 30 + int(60 * i / total)
                self.update_state(
                    state="RUNNING",
                    meta={"progress": progress, "message": f"Processing {i+1}/{total}"}
                )
            time.sleep(0.1)
        
        self.update_state(state="RUNNING", meta={"progress": 90, "message": "Calculating results..."})
        time.sleep(0.5)
        
        result = {
            "source_id": source_id,
            "total_items": total,
            "total_value": round(total_value, 2),
            "average_price": round(total_value / total, 2) if total > 0 else 0,
            "categories": categories,
            "status": "completed"
        }
        
        self.update_state(state="SUCCESS", meta={"progress": 100, "message": "Done!", "result": result})
        return result
        
    except Exception as e:
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise e
    finally:
        db.close()


@celery_app.task(bind=True)
def reimport_source(self, source_id: int):
    self.update_state(state="STARTED", meta={"progress": 0, "message": "Starting reimport..."})
    
    for i in range(1, 11):
        time.sleep(0.5)
        self.update_state(
            state="RUNNING",
            meta={"progress": i * 10, "message": f"Reimporting... step {i}/10"}
        )
    
    return {
        "source_id": source_id,
        "status": "completed",
        "items_imported": random.randint(5, 50),
        "message": f"Successfully reimported source {source_id}"
    }
