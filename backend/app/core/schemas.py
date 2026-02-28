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