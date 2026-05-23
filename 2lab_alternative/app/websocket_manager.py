from fastapi import WebSocket
from typing import Dict, Set
import asyncio
from celery.result import AsyncResult
from app.tasks import celery_app

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.task_subscribers: Dict[str, Set[str]] = {}
    
    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        for task_id in list(self.task_subscribers.keys()):
            if client_id in self.task_subscribers.get(task_id, set()):
                self.task_subscribers[task_id].discard(client_id)
    
    async def subscribe_to_task(self, client_id: str, task_id: str):
        if task_id not in self.task_subscribers:
            self.task_subscribers[task_id] = set()
        self.task_subscribers[task_id].add(client_id)
        
        await self.send_to_client(client_id, {
            "type": "subscribed",
            "task_id": task_id,
            "message": f"Subscribed to task {task_id}"
        })
        
        asyncio.create_task(self.track_task(task_id))
    
    async def track_task(self, task_id: str):
        task_result = AsyncResult(task_id, app=celery_app)
        
        while task_result.state in ['PENDING', 'STARTED', 'RUNNING']:
            meta = task_result.info or {}
            for client_id in self.task_subscribers.get(task_id, set()):
                await self.send_to_client(client_id, {
                    "type": "task_update",
                    "task_id": task_id,
                    "status": task_result.state.lower(),
                    "progress": meta.get("progress", 0),
                    "message": meta.get("message", "Processing...")
                })
            await asyncio.sleep(1)
        
        for client_id in self.task_subscribers.get(task_id, set()):
            await self.send_to_client(client_id, {
                "type": "task_complete",
                "task_id": task_id,
                "status": task_result.state.lower(),
                "result": task_result.result if task_result.successful() else None,
                "error": str(task_result.info) if task_result.failed() else None
            })
    
    async def send_to_client(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except:
                self.disconnect(client_id)

ws_manager = WebSocketManager()
