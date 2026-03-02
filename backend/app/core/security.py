from passlib.context import CryptContext
import random
import jwt
import os
from datetime import datetime, timedelta
from fastapi import HTTPException,status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BCRYPT_MAX_BYTES = 72

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Security utilities for password hashing and verification
class PasswordSecurity:
    @staticmethod
    def hash_password(password: str) -> str:
        if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
            raise ValueError(f"Password too long: max {BCRYPT_MAX_BYTES} bytes")
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return pwd_context.verify(password, hashed_password)
    
    



# One-time password (OTP) management for email-based authentication


class OneTimeAuth:
    def __init__(self, email_conn):
        self.email_conn = email_conn
        self._otp_store = {} # In-memory store (Email -> {otp, expires})

    async def generate_and_send(self, email: str, is_admin: bool = False):
        # Admin gets the secret from .env, users get random 6 digits
        otp = os.getenv("ADMIN_SECRET") if is_admin else "".join(str(random.randint(0, 9)) for _ in range(6))
        
        self._otp_store[email] = {
            "otp": otp,
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        # Send the email
        return self.email_conn.send_otp_email(email, otp, is_admin)

    def verify(self, email: str, code: str):
        record = self._otp_store.get(email)
        if not record or datetime.utcnow() > record["expires_at"]:
            return False
        
        if record["otp"] == code:
            del self._otp_store[email]
            return True
        return False



# JWT token management for authentication and authorization


class TokenSecurity:
    SECRET_KEY = os.getenv("JWT_SECRET", "super-secret")
    ALGORITHM = "HS256"
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")

    @classmethod
    def create_tokens(cls, email: str):
        # Determine if the user is the admin
        # We use .lower() to ensure "Admin@gmail.com" matches "admin@gmail.com"
        is_admin = False
        if cls.ADMIN_EMAIL and email:
            is_admin = (email.lower() == cls.ADMIN_EMAIL.lower())

        # Access token: short-lived (Increased to 60m as per previous suggestion, or keep 30)
        access_payload = {
            "sub": email,
            "is_admin": is_admin,  # This is the "Stamp" the frontend will read
            "exp": datetime.utcnow() + timedelta(minutes=60),
            "iat": datetime.utcnow()
        }

        # Refresh token: long-lived
        refresh_payload = {
            "sub": email,
            "exp": datetime.utcnow() + timedelta(days=7),
            "iat": datetime.utcnow()
        }
            
        access = jwt.encode(access_payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        refresh = jwt.encode(refresh_payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
            
        return access, refresh