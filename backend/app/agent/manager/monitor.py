import asyncio
import os
import shutil
from pathlib import Path
from fastapi import UploadFile

from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, List
from .data import DataState
from app.agent.Accessibility.vectordatabase import VectorManager

class Monitor:
    # Fields that should be ignored in logs for security/privacy
    IGNORE_FIELDS = {
        "refresh_token", 
        "token_expires", 
        "hashed_password", 
        "last_ip", 
        "password"
    }

    def __init__(self, db_client: AsyncIOMotorClient, state: DataState,vector_db: VectorManager):
        self.db = db_client
        self.state = state
        self.vector_db = vector_db
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
        """Initial load of 'self' collection into DataState and Vector DB."""
        try:
            cursor = self.db["self"].find({}) 
            count = 0
            async for doc in cursor:
                doc_type = doc.get("type")
                
                if doc_type == "tool_definition":
                    # Sync tools to Vector DB and DataState
                    await self._sync_tool_to_vector_db(doc)
                else:
                    # Sync general configs to DataState
                    category = doc.get("type", "general")
                    await self.state.update_system_config(category, doc)
                count += 1
            print(f"[Monitor] Initial 'self' preload complete. {count} items processed.")
        except Exception as e:
            print(f"[Monitor] Preload Error: {e}")

    async def _sync_tool_to_vector_db(self, tool_doc: Dict):
        """
        Refined Sync: Embeds only intent-focused data (Name, Purpose, Actions, Terms)
        to reduce vector noise and improve matching accuracy.
        """
        try:
            tool_name = tool_doc.get("tool_name", "unknown_tool")
            tool_id = tool_doc.get("_id")
            
            # 1. Extract the clean logic components
            details = tool_doc.get("details", "")
            actions = ", ".join(tool_doc.get("action", []))
            keywords = ", ".join(tool_doc.get("keywords", []))

            # 2. Construct the Intent-Focused Narrative
            # Using the specific headers you requested for cleaner embedding separation
            full_searchable_text = (
                f"Tool: {tool_name}\n"
                f"[PURPOSE]: {details}\n"
                f"[ACTIONS]: {actions}\n"
                f"[TERMS]: {keywords}"
            )

            # 3. Upsert into Vector DB
            success = await self.vector_db.upsert(
                collection_name="system_tools",
                content=full_searchable_text,
                doc_id=str(tool_id),
                metadata={
                    "tool_name": tool_name,
                    "type": "tool_definition",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            )

            if success:
                print(f"✅ Vector Sync (Intent-Only): {tool_name}")
                # Update RAM cache for full technical details access
                await self.state.update_system_config(f"tool_{tool_name}", tool_doc)
            
        except Exception as e:
            print(f"❌ Error during Tool Intent Sync: {e}")

    
    async def watch_system_config(self):
        """Watches the 'self' collection for configuration changes."""
        try:
            async with self.db["self"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["update", "replace", "insert"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = await self.db["self"].find_one({"_id": doc_id})
                        
                        if updated_doc:
                            doc_type = updated_doc.get("type")
                            
                            # If it's a tool, sync it to Vector DB
                            if doc_type == "tool_definition":
                                await self._sync_tool_to_vector_db(updated_doc)
                            else:
                                # Normal config update for other types
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
    
  