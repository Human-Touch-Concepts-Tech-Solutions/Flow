from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from app.core.security import TokenSecurity

router = APIRouter()
@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str, session_id: str = None):
    manager = websocket.app.state.connection_manager
    
    # Accept once here
    await websocket.accept() 
    
    email = await TokenSecurity.verify_token(token)
    if not email:
        await websocket.close(code=1008)
        return

    # Pass the already-accepted socket to the manager
    await manager.connect(email, websocket)
    print(f"✅ WebSocket Connected | User: {email} | Session: {session_id}")
    
    
    try:
        while True:
            await websocket.receive_json() # Keep the pipe open
    except WebSocketDisconnect:
        manager.disconnect(email)