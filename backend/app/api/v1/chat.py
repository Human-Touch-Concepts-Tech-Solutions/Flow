import uuid
import os
from pathlib import Path
import json
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from app.core.security import TokenSecurity, SessionManager
from app.agent.run import run_agent

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
    monitor = request.app.state.monitor
    data_state = request.app.state.data_state
    supabase = request.app.state.supabase
    manager = request.app.state.connection_manager 
    db_manager = request.app.state.db_process
    files_info = []
    
    # user infos from browser 
    env_context = {
        "timezone": request.headers.get("X-Client-Timezone", "UTC"),
        "client_time": request.headers.get("X-Client-Time"),
        "resolution": request.headers.get("X-Client-Resolution"), # Fixed key
        "platform": request.headers.get("X-Client-Platform"),     # Fixed key
        "viewport": request.headers.get("X-Client-Viewport"),     # Fixed key
        "is_touch": request.headers.get("X-Client-Is-Touch-Device"), # Fixed key
        "user_agent": request.headers.get("User-Agent"),
        "ip_address": request.client.host
    }


    # logic to just return files names only 
    

    # 2. Handle File Uploads
    # if files:
    #     user_folder = current_email.replace("@", "_").replace(".", "_")
        
    #     for file in files:
    #         try:
    #             file_ext = file.filename.split('.')[-1]
    #             unique_filename = f"{uuid.uuid4()}.{file_ext}"
    #             storage_path = f"uploads/{user_folder}/{unique_filename}"
                
    #             file_content = await file.read()
                
    #             supabase.storage.from_("chat-assets").upload(
    #                 path=storage_path,
    #                 file=file_content,
    #                 file_options={
    #                     "content-type": file.content_type,
    #                     "cache-control": "3600",
    #                     "upsert": "true",
    #                     "x-content-disposition": "attachment" 
    #                 }
    #             )
                
    #             public_url = supabase.storage.from_("chat-assets").get_public_url(storage_path)
                
    #             files_info.append({
    #                 "name": file.filename,
    #                 "url": public_url,
    #                 "type": file.content_type
    #             })
    #         except Exception as e:
    #             print(f"Upload error: {e}")
    #             raise HTTPException(status_code=500, detail=f"Upload failed for {file.filename}")

     # data satisfies the agent's expected input format, including the new 'files' and 'env_context' fields.
    
    

    # session logics
    session_id = await SessionManager.check_active_session(current_email)
    if not session_id:
        session_id = await SessionManager.create_session(current_email)


    # 1. Setup Paths
    user_dir = current_email.replace("@", "_").replace(".", "_")
    base_assets_path = Path(f"active_sessions/{user_dir}/assets")
    uploads_path = base_assets_path / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)

    files_for_agent = [] 
    
    # 2. Handle File Uploads & Registry Metadata
    if files:
        metadata_file = base_assets_path / "metadata.json"
        
        # Load existing metadata or initialize the Registry structure
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "registry": {
                    "files": {},
                    "total_stats": {"count": 0, "total_size_kb": 0.0}
                }
            }

        current_utc = datetime.now(timezone.utc).isoformat()

        for file in files:
            try:
                # Save the file physically
                file_path = uploads_path / file.filename
                content = await file.read()
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                # Calculate size
                size_kb = len(content) / 1024
                file_size_str = f"{size_kb:.2f} KB"

                # Update Registry: Using filename as the direct key
                metadata["registry"]["files"][file.filename] = {
                    "category": "uploads",
                    "mime_type": file.content_type,
                    "size": file_size_str,
                    "abs_path": str(file_path.absolute()),
                    "created_at": current_utc,
                    "metadata": {
                        "original_name": file.filename,
                        "last_accessed": current_utc
                    }
                }

                # Update running stats
                metadata["registry"]["total_stats"]["count"] = len(metadata["registry"]["files"])
                metadata["registry"]["total_stats"]["total_size_kb"] += size_kb
                metadata["registry"]["total_stats"]["last_update"] = current_utc

                # Add to the list for the Agent
                files_for_agent.append(file.filename)
                
            except Exception as e:
                print(f"File process error: {e}")
                continue

        # Save the updated registry
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=4)

    
    #logs for the agent to consume - this is the "Signal Box" concept you mentioned.
    pending_logs = await data_state.consume_logs(current_email)

    

    # 3. Perform AI Generation
    agent_response = await run_agent(
        email=current_email,
      
        text=message, 
        ai_service=ai_service,
        db=db_manager.db,
        vector_manager=request.app.state.vector_manager,
        files=files_for_agent,  # Just the file names for the agent
        env_context=env_context,
        pending_logs=pending_logs,
        session_id=session_id,
        data_state=data_state,
        
       
    )

    # 4. Trigger the Real-Time Popup
    # This is the "Easy Activation" you wanted. 
    # Just call this whenever you want to push UI to the user.
#     await manager.push_ui_event(
#     user_id=current_email,
#     event_type="popup",
#     title="🛡️ Security Protocol",
#     content="""
#         <div style="line-height: 1.5;">
#             <p>Your session is set to expire in <b>15 minutes</b>. Would you like to extend your current environment lease or finalize the current computations?</p>
#             <div style="display: flex; gap: 10px; margin-top: 20px;">
#                 <button onclick="window.closeSystemPopup()" style="flex: 1; padding: 10px; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 6px; cursor: pointer;">Ignore</button>
#                 <button onclick="alert('Lease Extended!'); window.closeSystemPopup();" style="flex: 1; padding: 10px; background: #0f172a; color: white; border: none; border-radius: 6px; cursor: pointer;">Extend Lease</button>
#             </div>
#         </div>
#     """
# )
    if not agent_response:
        return {"status": "error", "reply": "Agent failed to respond."}
    # 5. Return standard HTTP response for the Chat Interface
    return agent_response











#  ========== for presentation logic

# await manager.push_ui_event(
#     user_id=current_email,
#     event_type="presentation_prompt",
#     title="📽️ Visual Presentation",
#     content="""
#         <div style="text-align: center;">
#             <p style="margin-bottom:15px;">AI has prepared a dynamic animation for the big screen.</p>
#             <button onclick="window.initPresentation()" style="background: #6366f1; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; width: 100%;">
#                 Open Presentation Tab
#             </button>
#         </div>
#     """,
#     # This payload contains a simple CSS animation for the tab
#     payload="""
#         <div style="background: #0f172a; color: #38bdf8; height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif;">
#             <h1 style="font-size: 4rem; animation: pulse 2s infinite;">LIVE DATA</h1>
#             <div style="width: 100px; height: 100px; border: 5px solid #38bdf8; border-top: 5px solid white; border-radius: 50%; animation: spin 1s linear infinite;"></div>
#             <style>
#                 @keyframes pulse { 0% { opacity: 0.5; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1); } 100% { opacity: 0.5; transform: scale(0.9); } }
#                 @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
#             </style>
#         </div>
#     """
# )



# ======= for preview logic
# await manager.push_ui_event(
#     user_id=current_email,
#     event_type="preview",
#     title="🔍 Image Analysis",
#     content="""
#         <div style="padding: 10px;">
#             <h3 style="margin-top:0;">Source Image</h3>
#             <img src="https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=500" 
#                  style="width: 100%; border-radius: 8px; border: 1px solid #e2e8f0;" 
#                  alt="Satellite View" />
#             <p style="color: #64748b; font-size: 0.9rem; margin-top: 10px;">
#                 This image was retrieved based on your query about satellite networking.
#             </p>
#         </div>
#     """
# )



