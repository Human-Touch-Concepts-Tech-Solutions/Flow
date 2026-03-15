import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from app.core.security import TokenSecurity

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
async def handle_chat(
    message: str = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    request: Request = None,
    current_email: str = Depends(TokenSecurity.get_current_user)
):
    # 1. Access services from the central App State
    # This ensures we use the SAME manager instance used by the WebSocket
    ai_service = request.app.state.ai
    supabase = request.app.state.supabase
    manager = request.app.state.connection_manager 
    
    files_info = []

    # 2. Handle File Uploads
    if files:
        user_folder = current_email.replace("@", "_").replace(".", "_")
        
        for file in files:
            try:
                file_ext = file.filename.split('.')[-1]
                unique_filename = f"{uuid.uuid4()}.{file_ext}"
                storage_path = f"uploads/{user_folder}/{unique_filename}"
                
                file_content = await file.read()
                
                supabase.storage.from_("chat-assets").upload(
                    path=storage_path,
                    file=file_content,
                    file_options={
                        "content-type": file.content_type,
                        "cache-control": "3600",
                        "upsert": "true",
                        "x-content-disposition": "attachment" 
                    }
                )
                
                public_url = supabase.storage.from_("chat-assets").get_public_url(storage_path)
                
                files_info.append({
                    "name": file.filename,
                    "url": public_url,
                    "type": file.content_type
                })
            except Exception as e:
                print(f"Upload error: {e}")
                raise HTTPException(status_code=500, detail=f"Upload failed for {file.filename}")

    # 3. Perform AI Generation
    try:
        result = await ai_service.generate_response(message)
        ai_reply = result.get("response", "No response content received.")
    except Exception as e:
        print(f"AI error: {e}")
        ai_reply = "I'm sorry, I encountered an error processing that."

    # 4. Trigger the Real-Time Popup
    # This is the "Easy Activation" you wanted. 
    # Just call this whenever you want to push UI to the user.
    await manager.push_ui_event(
        user_id=current_email,
        event_type="popup",
        title="Document Processing",
        content=f"""
            <div style="text-align: center; padding: 10px;">
                <h3 style="color: #0f172a; margin-bottom: 8px;">Success! ✅</h3>
                <p style="color: #64748b; font-size: 0.9rem;">
                    Your message was processed and <b>{len(files_info)}</b> file(s) 
                    were uploaded successfully.
                </p>
                <button 
    onclick="if(window.closeSystemPopup) window.closeSystemPopup()"
    style="margin-top: 15px; padding: 8px 16px; background: #10b981; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;"
>
    Got it!
</button>
            </div>
        """
    )
    
    # 5. Return standard HTTP response for the Chat Interface
    return {
        "status": "success",
        "reply": ai_reply,
        "files_received": files_info
    }