from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime
import re




# Account creation and authentication schemas, including user registration, login, and token management. These schemas ensure data validation and consistency for user-related operations across the application.

class UserCreate(BaseModel):
    first_name: str = Field (..., min_length= 2, max_length= 50)
    last_name: str = Field (..., min_length= 2, max_length= 50)
    email: EmailStr
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{7,15}$")
    date_of_birth: date
    gender: str = Field(..., pattern=r"^(male|female)$")
    profession: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    is_verified: bool = False

    class Config:
        extra = "forbid"
    
    @validator("password")
    def strong_password(cls, v):
        """
        Password must be at least 8 characters and include:
        - Uppercase
        - Lowercase
        - Number
        - Symbol
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must include at least one number")
        if not re.search(r"[^\w\s]", v):
            raise ValueError("Password must include at least one symbol")
        return v




# user response schema for API responses, excluding sensitive information like hashed passwords. This schema is used to return user details in a secure manner without exposing critical data.

class UserResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    date_of_birth: datetime | None
    gender: str
    profession: str
    is_active: bool
    is_oauth: bool
    created_at: datetime
    

    class Config:
        from_attributes = True



# Additional schemas for OTP requests and responses, token management, and other authentication-related data structures can be defined here to support the authentication flow in the application.
class SendOtpRequest(BaseModel):
    email: EmailStr


# Schema for OTP verification requests, containing the user's email and the OTP code they received. This schema is used to validate the data when users attempt to verify their email addresses during the authentication process.
class VerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


# for login request and response, including access token generation and token type specification. These schemas facilitate the login process and ensure that the correct data is provided and returned during authentication.
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str  
    token_type: str = "bearer"
    role: str           


# Schema for token refresh requests, containing the refresh token that users provide to obtain new access tokens. This schema is essential for implementing secure token rotation and management in the authentication flow.
class RefreshRequest(BaseModel):
    refresh_token: str


# schemas for password reset functionality, including requests for initiating a password reset, verifying OTPs for password resets, and finalizing the password reset process with a new password. These schemas ensure that the password reset flow is secure and that all necessary data is validated properly.
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyResetOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordFinalRequest(BaseModel):
    reset_token: str  # The "Handshake" token
    new_password: str = Field(..., min_length=8)