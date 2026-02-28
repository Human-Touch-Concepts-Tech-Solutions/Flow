from passlib.context import CryptContext



# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BCRYPT_MAX_BYTES = 72



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