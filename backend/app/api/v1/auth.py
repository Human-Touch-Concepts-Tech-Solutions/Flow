from fastapi import APIRouter, status, HTTPException, Request


#local imports 
from app.core.schemas import UserCreate, UserResponse
from app.core.database import DatabaseProcess


router = APIRouter(tags=["Auth"])





#Registration Route for new users 
@router.post("/register", response_model=UserResponse, status_code= 201)
@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user_v1(user: UserCreate, request: Request):
    db_process: DatabaseProcess = request.app.state.db_process

    # 1. Check if user already exists
    existing_user = await db_process.users_collection.find_one({"email": user.email.lower()})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # 2. Global Beta Limit (Optional)
    user_count = await db_process.users_collection.count_documents({})
    if user_count >= 10: # Increased for your test
        raise HTTPException(status_code=429, detail="Beta testing registration limit reached")

    # 3. Create user (The database_process now handles roles/version)
    user_dict = user.model_dump()
    created_user = await db_process.create_user(user_dict, api_version="v1")

    return created_user



@router.get("/professions")
async def get_professions(request: Request):
    db_process = request.app.state.db_process
    professions = await db_process.manage_self_content(action="read", category="professions")
    
    if professions is None:
        raise HTTPException(status_code=404, detail="Professions list not found")
        
    return {"professions": professions}