from fastapi import APIRouter, status, HTTPException, Request
import os

#local imports 
from app.core.schemas import(
     UserCreate, 
     UserResponse,
     SendOtpRequest,
     VerifyOtpRequest)
from app.core.database import DatabaseProcess
from app.core.security import PasswordSecurity, OneTimeAuth, TokenSecurity


router = APIRouter(tags=["Auth"])





#Registration Route for new users 

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



# professions end point to provide suggestions for registration form (can be expanded to include more dynamic content in the future)

@router.get("/professions")
async def get_professions(request: Request):
    db_process = request.app.state.db_process
    professions = await db_process.manage_self_content(action="read", category="professions")
    
    if professions is None:
        raise HTTPException(status_code=404, detail="Professions list not found")
        
    return {"professions": professions}




#otp generation route that checks if the email is the admin email and sends the appropriate OTP type (admin or user)
@router.post("/send-otp")
async def send_otp(body: SendOtpRequest, request: Request):
    otp_service: OneTimeAuth = request.app.state.otp_service
    
    # Get Admin details from Env
    admin_email = os.getenv("ADMIN_EMAIL", "").lower()
    
    # Check if the requesting email is the admin
    is_admin = (body.email.lower() == admin_email)

    if is_admin:
        # Admin doesn't get an email; they use the Master Key
        return {
            "message": "Admin login detected. Use Master Key.", 
            "is_admin": True,
            "next_step": "admin_verify" 
        }

    # For normal users, proceed with OTP generation
    success = await otp_service.generate_and_send(body.email, is_admin=False)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send verification email")

    return {
        "message": "OTP sent successfully", 
        "is_admin": False,
        "next_step": "user_verify"
    }

@router.post("/verify-otp")
async def verify_otp(body: VerifyOtpRequest, request: Request):
    otp_service = request.app.state.otp_service
    db = request.app.state.db_process
    
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_secret = os.getenv("ADMIN_SECRET_KEY")
    is_admin = (body.email.lower() == admin_email.lower())

    if is_admin:
        if body.code != admin_secret:
            raise HTTPException(status_code=401, detail="Invalid Master Key")
    else:
        if not otp_service.verify(body.email, body.code):
            raise HTTPException(status_code=400, detail="Invalid or expired code")

    await db.db.users.update_one(
        {"email": body.email},
        {"$set": {"is_verified": True}}
    )

    # TokenSecurity.create_tokens now includes the 'is_admin' claim
    access, refresh = TokenSecurity.create_tokens(body.email)
    await db.store_refresh_token(body.email, refresh)
    
    return {
        "access_token": access,
        "refresh_token": refresh,
        "is_admin": is_admin,
        "token_type": "bearer"
    }