import asyncio
from typing import Any, Dict, List, Optional


class DatabaseAccess:
    def __init__(self, db_instance: Any):
        """
        db_instance: This is the database object from request.app.state.db
        """
        self.db = db_instance

    async def get_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch a single document (e.g., getting a system prompt or user profile)"""
        try:
            return await self.db[collection].find_one(query)
        except Exception as e:
            print(f"DB Read Error (get_one): {e}")
            return None

    async def get_many(self, collection: str, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch multiple documents (e.g., getting the last 10 chat messages)"""
        try:
            cursor = self.db[collection].find(query).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            print(f"DB Read Error (get_many): {e}")
            return []

    async def add_one(self, collection: str, data: Dict[str, Any]) -> bool:
        """Insert a document (e.g., saving a new chat message or user preference)"""
        try:
            result = await self.db[collection].insert_one(data)
            return result.acknowledged
        except Exception as e:
            print(f"DB Write Error (add_one): {e}")
            return False

    async def update_one(self, collection: str, query: Dict[str, Any], update_data: Dict[str, Any]) -> bool:
        """Update existing data (e.g., changing a user's profession)"""
        try:
            result = await self.db[collection].update_one(query, {"$set": update_data})
            return result.modified_count > 0
        except Exception as e:
            print(f"DB Update Error (update_one): {e}")
            return False