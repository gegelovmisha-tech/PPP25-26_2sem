from fastapi import FastAPI
from app.routes import items, sources, events, tasks, websocket

app = FastAPI(title="ETL Web Service", description="API for managing ETL data", version="1.0.0")

app.include_router(items.router)
app.include_router(sources.router)
app.include_router(events.router)
app.include_router(tasks.router)
app.include_router(websocket.router)

@app.get("/")
def root():
    return {"message": "ETL Web Service", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
