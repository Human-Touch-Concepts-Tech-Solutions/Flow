import uuid
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File,HTTPException
from app.core.security import TokenSecurity
from typing import Optional,List

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
async def handle_chat(
    message: str = Form(None),
    files: Optional[List[UploadFile]] = File(None), # Changed to List
    request: Request = None,
    current_email: str = Depends(TokenSecurity.get_current_user)
):
    ai_service = request.app.state.ai
    supabase = request.app.state.supabase
    files_info = [] # Store a list of file info objects

    if files:
        user_folder = current_email.replace("@", "_").replace(".", "_")
        
        for file in files: # Loop through all uploaded files
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
                    # This header forces the browser to treat it as an attachment
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
                raise HTTPException(status_code=500, detail=f"File upload failed for {file.filename}: {str(e)}")

    result = await ai_service.generate_response(message)
    
    return {
        "status": "success",
        "reply": result.get("response", "No response content received."),
        "files_received": files_info # Return the list
    }