from fastapi import WebSocket, WebSocketDisconnect, APIRouter
import json
from app.websocket_manager import ws_manager

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await ws_manager.connect(client_id, websocket)
    
    try:
        await ws_manager.send_to_client(client_id, {
            "type": "connected",
            "message": f"Connected as {client_id}"
        })
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "subscribe_task":
                task_id = message.get("task_id")
                if task_id:
                    await ws_manager.subscribe_to_task(client_id, task_id)
            
            elif message.get("type") == "ping":
                await ws_manager.send_to_client(client_id, {"type": "pong"})
    
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
