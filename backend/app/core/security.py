from passlib.context import CryptContext
import random
from jose import JWTError, jwt
import os
import uuid
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException,status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv


# sessions  Directory
SESSIONS_DIR = Path("active_sessions")
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
        self._otp_store = {} # Email -> {otp, expires, purpose}

    async def generate_and_send(self, email: str, is_admin: bool = False, purpose: str = "verify"):
        # 1. Generate OTP
        otp = os.getenv("ADMIN_SECRET") if is_admin else "".join(str(random.randint(0, 9)) for _ in range(6))
        
        # 2. Store with purpose
        self._otp_store[email] = {
            "otp": otp,
            "purpose": purpose,
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
        
        # 3. Logic: If purpose is "reset", tell the email service this is a recovery
        is_recovery = (purpose == "reset")
        
        # 4. Send the email (Existing functions don't send is_recovery, so it defaults to False)
        return self.email_conn.send_otp_email(
            to_email=email, 
            otp=otp, 
            is_admin=is_admin, 
            is_recovery=is_recovery
        )

    def verify(self, email: str, code: str, purpose: str = "verify"):
        record = self._otp_store.get(email)
        
        if not record or datetime.utcnow() > record["expires_at"]:
            return False
        
        # Check both the code and the purpose to prevent "purpose jumping"
        if record["otp"] == code and record.get("purpose") == purpose:
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
    


    @classmethod
    async def verify_token(cls, token: str):
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                return None
            return email
        except JWTError:
            return None

    @classmethod
    async def get_current_user(cls, token: str = Depends(oauth2_scheme)):
        email = await cls.verify_token(token) 
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return email
    

    @classmethod
    def create_temporary_token(cls, email: str, purpose: str) -> str:
        """Creates a very short-lived token for specific actions like password reset."""
        payload = {
            "sub": email,
            "purpose": purpose,
            "exp": datetime.utcnow() + timedelta(minutes=10),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    async def verify_temporary_token(cls, token: str, purpose: str):
        """Verifies the token and ensures it was meant for the specific purpose."""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            if payload.get("purpose") != purpose:
                return None
            return payload.get("sub")
        except JWTError:
            return None




# session management for tracking active user sessions (optional, can be used for logout or session invalidation)
class SessionManager:
    # Dictionary to store locks for each user to prevent file corruption
    _locks = {}

    @classmethod
    async def _get_lock(cls, user_email: str):
        """Returns a locking mechanism unique to the user."""
        if user_email not in cls._locks:
            cls._locks[user_email] = asyncio.Lock()
        return cls._locks[user_email]

    @staticmethod
    def _get_user_path(user_email: str) -> Path:
        """Sanitizes email to create a safe directory path."""
        safe_email = user_email.replace("@", "_").replace(".", "_")
        path = SESSIONS_DIR / safe_email
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    async def check_active_session(cls, user_email: str):
        """
        Scans the user's directory for a session file created within 24 hours.
        Returns the session_id if valid, otherwise None.
        """
        user_path = cls._get_user_path(user_email)
        
        async with await cls._get_lock(user_email):
            now_utc = datetime.now(timezone.utc)
            for file in user_path.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        created_at = datetime.fromisoformat(data.get("created_at"))
                        
                        # Ensure created_at is aware (it should be if saved correctly)
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        # Check if the file is less than 24 hours old
                        if now_utc - created_at < timedelta(hours=24):
                            return data.get("session_id")
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue 
        return None

    @classmethod
    async def create_session(cls, user_email: str):
        """
        Creates a new session ID and initializes the JSON buffer file.
        Returns the new session_id.
        """
        user_path = cls._get_user_path(user_email)
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        file_path = user_path / f"{session_id}.json"
        
        session_data = {
        "session_id": session_id,
        "initialized": False,  # Agent will see this and trigger DB fetch
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_profile": {},    # To be filled by Agent from DB
        "events": [],          # Combined History + Logs
        "metadata": {
            "version": "1.0",
            "interaction_count": 0
        }
    }

        async with await cls._get_lock(user_email):
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=4)
        
        return session_id