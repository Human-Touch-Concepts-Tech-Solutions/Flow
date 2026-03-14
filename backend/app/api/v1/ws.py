from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Request
from app.core.connection import manager
# Assuming you have an auth function that validates the JWT
from app.core.security import TokenSecurity
from app.core.security import oauth2_scheme
router = APIRouter()

@router.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str):
    print(f"DEBUG: Connection attempt with token: {token[:10]}...")
    # 1. Use your existing TokenSecurity to get the email
    email = await TokenSecurity.verify_token(token)
    
    if not email:
        # If the token is invalid or expired, reject the connection
        
        print("DEBUG: Auth failed")
        await websocket.close(code=1008)
        return

    # 2. Connect using the email as the unique ID
    # (Since your tokens use 'sub': email, this is your user identifier)
    print(f"DEBUG: User {email} connected!")
    await manager.connect(email, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})
                print("DEBUG: Received PING, sent PONG")
    except WebSocketDisconnect:
        manager.disconnect(email)




@router.get("/test-notification")
async def trigger_test(request: Request, email: str):
    """
    Manually trigger the popup. 
    URL: http://localhost:8000/api/v1/test-notification?email=enesiadams11@gmail.com
    """
    manager = request.app.state.connection_manager
    
    test_payload = {
        "type": "popup",
        "htmlContent": """
            <div class="backend-html-root">
                <h2 style="color: #10b981;">Connection Verified! ✅</h2>
                <p>Your WebSocket is officially <b>Live</b>.</p>
                <p>This message was pushed from the server to your browser.</p>
                <button onclick="alert('Success!')" style="margin-top:10px; padding:8px; cursor:pointer;">
                    Dismiss Test
                </button>
            </div>
        """
    }

    if email in manager.active_connections:
        await manager.send_personal_message(email, test_payload)
        return {"status": "Message sent to " + email}
    
    return {
        "status": "error", 
        "reason": "User not connected", 
        "active_users": list(manager.active_connections.keys())
    }