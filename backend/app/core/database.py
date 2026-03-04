from typing import Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
import os



# Local Imports
from app.core.security import PasswordSecurity




load_dotenv()

#database models and utilities for MongoDB interactions, including user management, task management, and session handling. This module abstracts the database operations and provides a clean interface for the rest of the application to interact with MongoDB.


class DatabaseProcess:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db["users"]
        self.self_collection = db["self"]

    

    # User Account Creation with Automatic Role Assignment and Data Formatting
    async def create_user(self, user_data: Dict, api_version: str = "v1"):
        # 1. Automatic Role Selection
        target_admin = os.getenv("ADMIN_EMAIL")
        
        # Check if this user matches your admin email
        email = user_data["email"].lower()
        if target_admin and email == target_admin.lower():
            role = "admin"
            access_level = 5
        else:
            role = "user"
            access_level = 1

        # 2. Data Formatting
        password = user_data.get("password")
        hashed_pw = PasswordSecurity.hash_password(password) if password else None
        
        dob = user_data.get("date_of_birth")
        dob_datetime = datetime.combine(dob, time.min) if dob else None

        # Determine if this is an OAuth signup
        is_oauth = user_data.get("auth_type") == "google"

        user_doc = {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "email": email,
            "phone": user_data.get("phone"),
            "date_of_birth": dob_datetime,
            # FIXED: Using .get() ensures it won't crash if Google doesn't provide these
            "gender": user_data.get("gender", "Not Specified"),
            "profession": user_data.get("profession", "Other"),
            "hashed_password": hashed_pw,
            "role": role,
            "access_level": access_level,
            "api_version": api_version,
            "is_active": True,
            "is_oauth": is_oauth, # Dynamically set based on signup type
            "created_at": datetime.utcnow(),
            "is_verified": user_data.get("is_verified", False),
            "subscription": {
                "plan": "free",
                "status": "active"
            },
            "credits": {
                "balance": 10,
                "total_used": 0,
                "total_bought": 0
            }
        }
        
        result = await self.users_collection.insert_one(user_doc)
        
        # Profession Validation
        clean_profession = user_doc["profession"].strip().title()
        await self.manage_self_content(action="add", category="professions", data=clean_profession)
        
        user_doc["_id"] = str(result.inserted_id)
        user_doc.pop("hashed_password", None)
        return user_doc
    

    #self content management for professions, interests, and goals
    async def manage_self_content(self, action: str, category: str, data: any = None):
        """
        Dynamic manager for the 'self' collection.
        action: 'read', 'add', 'delete', 'set'
        category: The field name (e.g., 'professions', 'api_keys', 'app_version')
        data: The value to add/remove/set
        """
        
        # We keep all app settings in one document for easy fetching
        query = {"type": "app_config"}

        # 1. READ
        if action == "read":
            doc = await self.self_collection.find_one(query)
            if not doc:
                # Seed default professions if the whole DB is empty
                if category == "professions":
                    default_profs = ["Engineer", "Doctor", "Artist"] # Your 50 items here
                    await self.self_collection.update_one(
                        query, {"$set": {category: default_profs}}, upsert=True
                    )
                    return default_profs
                return None
            return doc.get(category)

        # 2. ADD (For Lists/Arrays - like adding one more profession)
        elif action == "add":
            await self.self_collection.update_one(
                query, 
                {"$addToSet": {category: data}}, 
                upsert=True
            )
            return True

        # 3. DELETE (For Lists/Arrays - like removing one profession)
        elif action == "delete":
            await self.self_collection.update_one(
                query, 
                {"$pull": {category: data}}
            )
            return True

        # 4. SET (For single values - like updating app_version: "2.1.0")
        elif action == "set":
            await self.self_collection.update_one(
                query, 
                {"$set": {category: data}}, 
                upsert=True
            )
            return True

        return None
    


    # Additional database methods for user retrieval, updates, task management, and session handling can be implemented here to support the application's functionality.
    async def store_refresh_token(self, email: str, refresh_token: str):
        # Calculate expiry internally
        expiry = datetime.utcnow() + timedelta(days=7)
        
        # Use the collection variable defined in __init__
        await self.users_collection.update_one(
            {"email": email.lower()},
            {
                "$set": {
                    "refresh_token": refresh_token,
                    "token_expires": expiry
                }
            },
            upsert=True
        )

    async def get_user_by_email(self, email: str):
        return await self.db.users.find_one({"email": email})
    


    async def update_user_password(self, email: str, hashed_password: str):
        """Updates the user's password in MongoDB."""
        await self.users_collection.update_one(
            {"email": email.lower()},
            {"$set": {"hashed_password": hashed_password}}
        )

    async def revoke_all_user_tokens(self, email: str):
        """
        SECURITY: Clears the stored refresh token inside the user document.
        """
        await self.users_collection.update_one(
            {"email": email.lower()},
            {"$set": {
                "refresh_token": None,
                "token_expires": None
            }}
        )