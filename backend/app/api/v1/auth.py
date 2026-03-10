from fastapi import APIRouter, status, HTTPException, Request, Depends
import os
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse, RedirectResponse
from bson import ObjectId
#local imports 
from app.core.schemas import(
     UserCreate, 
     UserResponse,
     SendOtpRequest,
     VerifyOtpRequest,
     LoginRequest,
     LoginResponse,
     RefreshRequest,
     ForgotPasswordRequest,
     VerifyResetOTPRequest,
     ResetPasswordFinalRequest)
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


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request
):
    db: DatabaseProcess = request.app.state.db_process
    
    # 1. Find user
    user = await db.get_user_by_email(body.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 2. Check Password using the Class method
    if not PasswordSecurity.verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 3. Check Verification Status
    if not user.get("is_verified", False):
        otp_service = request.app.state.otp_service
        await otp_service.generate_and_send(body.email)
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="VERIFY_REQUIRED"
        )

    # 4. Generate tokens using your NEW combined method
    # This returns a tuple: (access, refresh)
    access_token, refresh_token = TokenSecurity.create_tokens(body.email)

    # 5. Store refresh token in DB
    await db.store_refresh_token(body.email, refresh_token)
    

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "role": user.get("role", "user") # This can help frontend distinguish Admin vs User
    }




# Route for refreshing tokens, which validates the old refresh token, generates new tokens, and updates the database with the new refresh token to ensure secure token rotation and management in the authentication flow.

@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(body: RefreshRequest, request: Request):
    db: DatabaseProcess = request.app.state.db_process

    # 1. Validate the old refresh token against the DB
    email = await db.validate_refresh_token(body.refresh_token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or expired refresh token"
        )

    # 2. Generate a fresh pair (Rotation)
    new_access, new_refresh = TokenSecurity.create_tokens(email)

    # 3. Update the database with the new refresh token
    # This invalidates the old one and stores the new one
    await db.store_refresh_token(email, new_refresh)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }




# recover password flow, which includes sending a reset OTP, verifying the OTP, and allowing the user to set a new password. This flow ensures that only verified users can reset their passwords and that all necessary security measures are in place to protect user accounts during the password reset process.
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, request: Request):
    db = request.app.state.db_process
    otp_service = request.app.state.otp_service
    admin_email = os.getenv("ADMIN_EMAIL", "").lower()

    # 1. Block Admin Recovery via Public Route
    if body.email.lower() == admin_email:
        print(f"SECURITY ALERT: Recovery attempt on ADMIN account: {body.email}")
        return {"message": "If an account exists, a reset code has been sent."}

    user = await db.get_user_by_email(body.email)
    
    # 2. Logic for existing user
    if user:
        await otp_service.generate_and_send(body.email, purpose="reset")
    else:
        # We don't tell the frontend, but we log it for debugging
        print(f"INFO: Recovery requested for non-existent email: {body.email}")

    return {"message": "If an account exists, a reset code has been sent."}

@router.post("/verify-reset-otp")
async def verify_reset_otp(body: VerifyResetOTPRequest, request: Request):
    otp_service = request.app.state.otp_service
    
    # REMOVED 'await' because verify is a regular def, not async def
    is_valid = otp_service.verify(body.email, body.otp, purpose="reset")
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    reset_token = TokenSecurity.create_temporary_token(body.email, purpose="password_reset")
    return {"reset_token": reset_token}

@router.post("/reset-password")
async def reset_password(body: ResetPasswordFinalRequest, request: Request):
    db = request.app.state.db_process
    
    # 1. Verify the temporary reset token
    email = await TokenSecurity.verify_temporary_token(body.reset_token, purpose="password_reset")
    if not email:
        raise HTTPException(status_code=400, detail="Reset session expired. Please start over.")

    # 2. Hash and Update
    hashed_password = PasswordSecurity.hash_password(body.new_password)
    await db.update_user_password(email, hashed_password)

    # 3. SECURITY BOOST: Revoke all refresh tokens for this user
    # This kicks out any hackers currently logged in
    await db.revoke_all_user_tokens(email)

    return {"message": "Password updated successfully."}




@router.get("/oauth/google")
async def google_login(request: Request):
    oauth = request.app.state.oauth
    # Ensure this URI is registered in Google Cloud Console!
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") 
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/oauth/google/callback")
async def google_callback(request: Request):
    oauth = request.app.state.oauth
    db = request.app.state.db_process

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")
    except Exception:
        raise HTTPException(status_code=400, detail="Google authentication failed")

    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to fetch user info")

    email = user_info["email"].lower()
    admin_email = os.getenv("ADMIN_EMAIL", "").lower()
    if admin_email and email == admin_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin accounts must login using the secure Admin Portal."
        )
    # Check if user exists
    user = await db.get_user_by_email(email)

    if not user:
        # Create new OAuth user
        user_data = {
            "first_name": user_info.get("given_name", "User"),
            "last_name": user_info.get("family_name", ""),
            "email": email,
            "auth_type": "google", # Good to track how they signed up
            "is_verified": True,   # Google already verified them
            "password": None       # Explicitly no password
        }
        await db.create_user(user_data)

    # Generate tokens using our standard security class
    access_token, refresh_token = TokenSecurity.create_tokens(email)

    # Store refresh token in DB
    
    await db.store_refresh_token(email, refresh_token)
    # Redirect to frontend with tokens
    frontend_redirect = os.getenv("FRONTEND_OAUTH_REDIRECT")
    return RedirectResponse(
        url=f"{frontend_redirect}?access_token={access_token}&refresh_token={refresh_token}"
    )




# ChatInterface routes will be protected by the TokenSecurity.get_current_user dependency in the route definitions, ensuring that only authenticated users can access the chat functionalities. The get_current_user method will validate the JWT access token, extract the user's email and admin status, and allow access to the chat routes accordingly, providing a secure authentication mechanism for both regular users and admins accessing their respective chat interfaces.
#route example for fetching user-specific greeting configuration, which can be used to personalize the chat interface based on user preferences or roles. This route is protected by the TokenSecurity.get_current_user dependency, ensuring that only authenticated users can access their personalized settings, and it demonstrates how to return dynamic content that can enhance the user experience in the chat interface.
@router.get("/user-info")
async def get_user_info(
    request: Request,
    current_email: str = Depends(TokenSecurity.get_current_user)
):
    db = request.app.state.db_process
    user = await db.get_user_by_email(current_email)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return everything the frontend needs to identify and authorize the user
    return {
        "first_name": user.get("first_name"),
        "last_name": user.get("last_name"),
        "email": user.get("email"),
        "role": user.get("role"), # This helps us distinguish Admin vs User
        "credits": user.get("credits"),
        "subscription": user.get("subscription"),
        "is_verified": user.get("is_verified", False)
    }









# logging out a user by deleting their refresh token(s) from the database, which effectively invalidates their session and requires them to re-authenticate to obtain new tokens for continued access. This route is protected by the TokenSecurity.get_current_user dependency, ensuring that only authenticated users can log out of their own sessions, and it provides a secure way to manage user sessions and enhance account security.
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    # This retrieves the email (or user identifier) from the token
    user_email: str = Depends(TokenSecurity.get_current_user) 
):
    db_process = request.app.state.db_process
    
    # Use the method you already defined in DatabaseProcess
    await db_process.revoke_all_user_tokens(user_email)
    
    print(f"User {user_email} logged out successfully.")
    
    return {"status": "success", "message": "Logged out successfully"}