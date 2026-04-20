import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict
from .data import DataState

class Monitor:
    # Fields that should be ignored in logs for security/privacy
    IGNORE_FIELDS = {
        "refresh_token", 
        "token_expires", 
        "hashed_password", 
        "last_ip", 
        "password"
    }

    def __init__(self, db_client: AsyncIOMotorClient, state: DataState):
        self.db = db_client
        self.state = state
        self.is_running = True
        self._ready = asyncio.Event()


    def _get_event_meta(self, updated_fields: Dict) -> tuple[str, str]:
        """Translates technical DB keys into a Human Story for the AI."""
        keys = updated_fields.keys()
        if "first_name" in keys or "last_name" in keys:
            return "IDENTITY_UPDATE", "User changed their legal name."
        if "profession" in keys:
            return "PROFILE_UPDATE", f"User updated profession to: {updated_fields.get('profession')}"
        return "SYSTEM_SYNC", f"Updated: {', '.join(keys)}"



    async def preload_system_config(self):
        """Initial load of 'self' collection into DataState."""
        try:
            # Explicitly target the collection
            cursor = self.db["self"].find({}) 
            count = 0
            async for doc in cursor:
                category = doc.get("type", "general")
                await self.state.update_system_config(category, doc)
                count += 1
            print(f"[Monitor] Initial 'self' config preload complete. {count} docs loaded.")
        except Exception as e:
            print(f"[Monitor] Preload Error: {e}")

    

    
    async def watch_system_config(self):
        """Watches the 'self' collection for configuration changes."""
        try:
            # Use string access ["self"] to avoid Python's self keyword conflict
            async with self.db["self"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["update", "replace", "insert"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = await self.db["self"].find_one({"_id": doc_id})
                        
                        if updated_doc:
                            category = updated_doc.get("type", "general")
                            await self.state.update_system_config(category, updated_doc)
        except Exception as e:
            print(f"❌ Monitor Config Watcher Error: {e}")


    async def watch_database(self):
        """Live watch for user profile changes."""
        try:
            # FIX: Change ["self"] to ["users"]
            async with self.db["users"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["update", "replace"]:
                        # Get the technical diff
                        updated_fields = change["updateDescription"]["updatedFields"]
                        
                        # Filter out sensitive stuff (passwords, etc.)
                        filtered = {k: v for k, v in updated_fields.items() if k not in self.IGNORE_FIELDS}
                        if not filtered: 
                            continue

                        # Find the owner of this document
                        user_id = change["documentKey"]["_id"]
                        user_doc = await self.db["users"].find_one({"_id": user_id})
                        
                        if user_doc:
                            email = user_doc.get("email")
                            event, desc = self._get_event_meta(filtered)
                            
                            # Push to the memory bank
                            await self.state.deposit_log(email, event, filtered, desc)
                            print(f"[Monitor] ⚡ Live Update: {event} for {email}")
        except Exception as e:
            print(f"❌ Monitor Database Watcher Error: {e}")
          


    async def internal_event_hook(self, email: str, category: str, details: Dict, description: str):
        """
        Manual entry point for things like 'FILE_UPLOADED' or 'SECURITY_ALERT'.
        Always logs in UTC.
        """
        # Ensure UTC is added to the details for history tracking
        details["logged_at_utc"] = datetime.now(timezone.utc).isoformat()
        await self.state.deposit_log(email, category, details, description)
        print(f"[Monitor] Manual Hook: {category} for {email}")


        
    async def start(self):
        """Launch the monitor loops."""
        # 1. AWAIT this. Don't move forward until the data is in DataState.
        print("[Monitor] Forced preloading started...")
        await self.preload_system_config()
        
        # 2. Start the watchers in the background
        asyncio.create_task(self.watch_database())
        asyncio.create_task(self.watch_system_config())
        
        self._ready.set() # Signal that we are ready
        print("Monitor is alive and watching all collections...")
    
  