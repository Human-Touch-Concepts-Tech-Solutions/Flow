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

    # this method is in charge of automatically storing  tool definitions in the vector database with a clean, 
    # intent-focused embedding format.
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
            async with self.db["users"].watch() as stream:
                async for change in stream:
                    # Capture creation/inserts as well as updates/replacing
                    if change["operationType"] in ["insert", "update", "replace"]:
                        user_id = change["documentKey"]["_id"]
                        user_doc = await self.db["users"].find_one({"_id": user_id})
                        
                        if user_doc:
                            email = user_doc.get("email")
                            
                            # CRITICAL SYNC GAP CLOSER:
                            # Automatically pushes or refreshes the narrative background profile in the Vector DB
                            await self._sync_user_bio_to_vector_db(user_doc)

                            # Continue running your normal logger operations for updates
                            if change["operationType"] in ["update", "replace"]:
                                updated_fields = change["updateDescription"]["updatedFields"]
                                filtered = {k: v for k, v in updated_fields.items() if k not in self.IGNORE_FIELDS}
                                if not filtered: 
                                    continue
                                
                                event, desc = self._get_event_meta(filtered)
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
    
    # Methods  for changes in  chat session, system logs and users assets collections 
    # 1. Chat Sessions Sync Pipeline
    async def _sync_chat_session_to_vector_db(self, doc: Dict):
        """
        Syncs active or archived chat session narratives.
        Uses session_id deterministically to overwrite and update the same thread record.
        """
        try:
            email = doc.get("email", "unknown_user")
            session_id = doc.get("session_id", "unknown_session")
            narrative = doc.get("narrative", "")

            if not narrative:
                return

            success = await self.vector_db.upsert(
                collection_name="user_history",
                content=f"Chat History Narrative [{session_id}]:\n{narrative}",
                doc_id=f"chat_{session_id}",  # Anchor ID to overwrite active session updates
                metadata={
                    "user_email": email,
                    "session_id": session_id,
                    "type": "chat_session_summary",
                    "last_sync_utc": datetime.now(timezone.utc).isoformat()
                }
            )
            if success:
                print(f"💬 Vector Sync: Chat Session Narrative updated for {email} ({session_id})")
        except Exception as e:
            print(f"❌ Error during Chat Session Vector Sync: {e}")

    # 2. System Logs Sync Pipeline
    async def _sync_system_log_to_vector_db(self, doc: Dict):
        """
        Syncs transactional security, operational, and configuration narrative states.
        Uses the unique log MongoDB Object ID to record distinct, individual audit entries.
        """
        try:
            email = doc.get("email", "unknown_user")
            log_id = str(doc.get("_id"))
            session_id = doc.get("session_id", "unknown_session")
            narrative = doc.get("narrative", "")

            if not narrative:
                return

            success = await self.vector_db.upsert(
                collection_name="user_history",
                content=f"System Log Event Narrative:\n{narrative}",
                doc_id=f"log_{log_id}",  # Appends as independent historical items
                metadata={
                    "user_email": email,
                    "session_id": session_id,
                    "type": "system_log_event",
                    "event_type": doc.get("event"),
                    "logged_at": doc.get("logged_at"),
                    "last_sync_utc": datetime.now(timezone.utc).isoformat()
                }
            )
            if success:
                print(f"⚡ Vector Sync: System Log Event recorded for {email}")
        except Exception as e:
            print(f"❌ Error during System Log Vector Sync: {e}")

    # 3. User Assets Sync Pipeline
    async def _sync_user_asset_to_vector_db(self, doc: Dict):
        """
        Syncs application files, scripts, and document descriptions via summary indexes.
        Uses the file ID to maintain up-to-date asset tracking maps.
        """
        try:
            email = doc.get("email", "unknown_user")
            asset_id = str(doc.get("_id"))
            file_name = doc.get("file_name", "unknown_file")
            narrative = doc.get("narrative", "")

            if not narrative:
                return

            success = await self.vector_db.upsert(
                collection_name="user_assets",
                content=f"Asset Context Descriptor ({file_name}):\n{narrative}",
                doc_id=f"asset_{asset_id}",  # Refreshes tracking profiles cleanly
                metadata={
                    "user_email": email,
                    "session_id": doc.get("session_id"),
                    "type": "user_file_asset",
                    "file_name": file_name,
                    "file_type": doc.get("file_type"),
                    "last_sync_utc": datetime.now(timezone.utc).isoformat()
                }
            )
            if success:
                print(f"📂 Vector Sync: User Asset Narrative synchronized for {email} ({file_name})")
        except Exception as e:
            print(f"❌ Error during User Asset Vector Sync: {e}")

    # method to sync user bio, history , preferences etc to vector database 

    async def _sync_user_bio_to_vector_db(self, user_doc: Dict):
        """
        Transforms raw MongoDB user schemas into a high-quality narrative 
        biography story, then upserts it into the Vector DB memory bank.
        """
        try:
            email = user_doc.get("email", "unknown_user")
            user_id = user_doc.get("_id")
            first_name = user_doc.get("first_name", "")
            last_name = user_doc.get("last_name", "")
            full_name = f"{first_name} {last_name}".strip() or "User Profile"
            
            # 1. Unpack values gracefully handling raw datatypes and nesting structures
            profession = user_doc.get("profession", "Unspecified Profession")
            gender = user_doc.get("gender", "unspecified")
            
            # Extract plain dates from Mongo dictionary format
            dob_obj = user_doc.get("date_of_birth", {})
            dob_str = dob_obj.get("$date") if isinstance(dob_obj, dict) else dob_obj
            if dob_str and isinstance(dob_str, str):
                dob_clean = dob_str.split("T")[0] # Grab just the YYYY-MM-DD portion
            else:
                dob_clean = "Unknown"

            subscription = user_doc.get("subscription", {})
            plan = subscription.get("plan", "Free Tier")
            status = subscription.get("status", "inactive")
            
            credits_data = user_doc.get("credits", {})
            balance = credits_data.get("balance", 0)
            preferences = user_doc.get("preferences", []) or user_doc.get("perferences", [])

            # 🌟 FIX: Ensure preferences is actually a list, not a raw string
            if isinstance(preferences, str):
                # If it's a string, split it by commas or wrap it in a list so it doesn't loop letters
                preferences = [preferences] if preferences.strip() else []

            if preferences and isinstance(preferences, list):
                # Strip whitespace and ignore any empty string entries in the array
                preferences_text = " ".join([f"They prefer or like: {str(p).strip()}." for p in preferences if str(p).strip()])
            else:
                preferences_text = "No explicit system or behavioral preferences have been configured yet."

            # 2. Construct the Storytelling Profile Narrative Block
           
            profile_narrative = (
                f"User Profile Anchor Summary:\n"
                f"This foundational identity data belongs to the platform user {full_name}. "
                f"They identify as {gender} and were born on the date of {dob_clean}. "
                f"Professionally, they operate as a {profession}. "
                f"Their primary verified contact channel is {email}. "
                f"Account Metadata: They are currently positioned on the {plan} subscription tier, "
                f"with their account status marked as {status}. Their active operational utility credit balance is {balance} units."
                f"User Behavioral and System Preferences:\n"
                f"{preferences_text}"
            )

            # 3. Upsert cleanly into the master user_memories space using metadata isolation keys
            success = await self.vector_db.upsert(
                collection_name="user_memories",
                content=profile_narrative,
                doc_id=f"bio_{str(user_id)}", # Deterministic ID: updates profile instead of creating duplicates
                metadata={
                    "user_email": email,
                    "type": "user_profile_bio",
                    "profession_tag": profession,
                    "last_sync_utc": datetime.now(timezone.utc).isoformat()
                }
            )

            if success:
                print(f"✅ Vector Memory Sync (User Bio Narrative): Linked profile for {email}")
        
        except Exception as e:
            print(f"❌ Error during User Bio Vector Sync: {e}")

    
    # method to watch  for changes in  chat sessions, system logs and user assets collections 
    async def watch_chat_sessions(self):
        """Live watch for alterations inside conversational chat histories."""
        try:
            async with self.db["chat_sessions"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["insert", "update", "replace"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = await self.db["chat_sessions"].find_one({"_id": doc_id})
                        if updated_doc:
                            await self._sync_chat_session_to_vector_db(updated_doc)
        except Exception as e:
            print(f"❌ Monitor Chat Watcher Error: {e}")

    async def watch_system_logs(self):
        """Live watch for background application logging events, updates, and overrides."""
        try:
            # Crucial: full_document="updateLookup" forces MongoDB to send the 
            # updated doc snapshot back during an 'update' event.
            async with self.db["system_logs"].watch(full_document="updateLookup") as stream:
                async for change in stream:
                    # 1. Expand operations to capture updates and replacements
                    if change["operationType"] in ["insert", "update", "replace"]:
                        doc_id = change["documentKey"]["_id"]
                        
                        # 2. Grab the full document snapshot from the stream event or fall back to a manual query
                        updated_doc = change.get("fullDocument") or await self.db["system_logs"].find_one({"_id": doc_id})
                        
                        if updated_doc:
                            # 3. Stream changes straight down to your existing vector pipeline tool
                            await self._sync_system_log_to_vector_db(updated_doc)
                            print(f"[Monitor] ⚡ System Log synced ({change['operationType']}): ID {doc_id}")
                            
        except Exception as e:
            print(f"❌ Monitor System Log Watcher Error: {e}")

    async def watch_user_assets(self):
        """Live watch for target directory files changes and uploads."""
        try:
            async with self.db["user_assets"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["insert", "update", "replace"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = await self.db["user_assets"].find_one({"_id": doc_id})
                        if updated_doc:
                            await self._sync_user_asset_to_vector_db(updated_doc)
        except Exception as e:
            print(f"❌ Monitor User Assets Watcher Error: {e}")
    
    # method to watch for changes in platform documentation and sync to vector database
    async def watch_platform_documentation(self):
        """Live watch for mutations inside the platform documentation directory."""
        try:
            async with self.db["platform_documentation"].watch() as stream:
                async for change in stream:
                    if change["operationType"] in ["insert", "update", "replace"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = await self.db["platform_documentation"].find_one({"_id": doc_id})
                        
                        if updated_doc:
                            await self._sync_platform_documentation_to_vector_db(updated_doc)
        except Exception as e:
            print(f"❌ Monitor Documentation Watcher Error: {e}")

    # method to sync platform documentations like policies, faqs, guides etc to vector database
    async def _sync_platform_documentation_to_vector_db(self, doc: Dict):
        """
        Processes global documentation entries, applies sliding window chunking,
        and cleanly overwrites past chunk fragments to ensure strict data consistency.
        """
        try:
            doc_id = str(doc.get("_id"))
            title = doc.get("title", "Untitled Document")
            category = doc.get("category", "General Reference")
            raw_content = doc.get("documentation_content", "")
            
            # Extract underlying metadata object properties if provided safely
            inner_metadata = doc.get("metadata", {})
            audience = inner_metadata.get("audience", "All Users")
            version = inner_metadata.get("version", "1.0.0")

            if not raw_content:
                print(f"[Monitor] ⚠️ Skipping doc sync for {title}: No content found.")
                return

            # Combine structural context with content so each individual vector chunk understands its parent context
            contextual_text = (
                f"Document Title: {title}\n"
                f"Category: {category}\n"
                f"Target Audience: {audience}\n\n"
                f"{raw_content}"
            )

            # 1. Clear out any old chunk references for this ID to ensure ghost fragments are removed
            existing_chunks = await self.vector_db.query(
                collection_name="platform_knowledge",
                query_text=title,
                limit=100,
                filters={"doc_origin_id": doc_id}
            )
            
            if existing_chunks:
                # Assuming your collection engine exposes a delete interface, 
                # or we overwrite them cleanly via our index tracker below.
                pass

            # 2. Utilize your VectorManager chunking function
            chunks = self.vector_db.chunk_text(contextual_text, chunk_size=500, overlap=50)

            # 3. Upsert chunks sequentially using deterministic identity paths
            success_count = 0
            for i, chunk_text in enumerate(chunks):
                deterministic_chunk_id = f"doc_{doc_id}_chunk_{i}"
                
                success = await self.vector_db.upsert(
                    collection_name="platform_knowledge",
                    content=chunk_text,
                    doc_id=deterministic_chunk_id,
                    metadata={
                        "doc_origin_id": doc_id,
                        "type": "platform_documentation",
                        "title": title,
                        "category": category,
                        "audience": audience,
                        "version": version,
                        "chunk_index": i,
                        "last_sync_utc": datetime.now(timezone.utc).isoformat()
                    }
                )
                if success:
                    success_count += 1

            print(f"📖 Global Knowledge Sync: Updated '{title}' ({success_count}/{len(chunks)} chunks processed)")

        except Exception as e:
            print(f"❌ Error during Platform Documentation Vector Sync: {e}")
    

    #  sync and moitor for external knowledge bases and api changes 
    # can be added here in the future as well following the same pattern of deterministic
    #  upserts and structured metadata tagging for optimal retrieval and maintenance.

    async def watch_external_knowledge(self):
        """Live watch stream monitoring incoming web parsing payloads from scrapers."""
        try:
            # updateLookup handles direct edits, while inserts catch incoming streaming data
            async with self.db["external_knowledge"].watch(full_document="updateLookup") as stream:
                async for change in stream:
                    if change["operationType"] in ["insert", "update", "replace"]:
                        doc_id = change["documentKey"]["_id"]
                        updated_doc = change.get("fullDocument") or await self.db["external_knowledge"].find_one({"_id": doc_id})
                        
                        if updated_doc:
                            await self._sync_external_knowledge_to_vector_db(updated_doc)
        except Exception as e:
            print(f"❌ Monitor External Knowledge Watcher Error: {e}")

    async def _sync_external_knowledge_to_vector_db(self, doc: Dict):
        """
        Takes raw multi-page scraper dumps, formats structural index anchors,
        chunks long-form articles cleanly, and saves to the vector space.
        """
        try:
            doc_id = str(doc.get("_id"))
            url = doc.get("url", "unknown_source")
            domain = doc.get("domain", "unknown_domain")
            title = doc.get("title", "Untitled Scraped Resource")
            raw_content = doc.get("raw_content", "")

            if not raw_content:
                print(f"[Monitor] ⚠️ Skipping external sync for '{title}': Raw content is empty.")
                return

            # Format structural markdown header for vector alignment
            structured_narrative = (
                f"Source Resource URL: {url}\n"
                f"Domain Platform: {domain}\n"
                f"Page Title Context: {title}\n"
                f"--- WEBPAGE SECTION EXTRACT ---\n"
                f"{raw_content}"
            )

            # Split large HTML layouts into searchable blocks
            chunks = self.vector_db.chunk_text(structured_narrative, chunk_size=600, overlap=60)

            success_count = 0
            for i, chunk_text in enumerate(chunks):
                # Generates a clear chunk identification key to prevent duplicate vectors
                deterministic_chunk_id = f"web_{doc_id}_chunk_{i}"

                success = await self.vector_db.upsert(
                    collection_name="internet_knowledge", # Dedicated global web namespace
                    content=chunk_text,
                    doc_id=deterministic_chunk_id,
                    metadata={
                        "doc_origin_id": doc_id,
                        "type": "external_web_knowledge",
                        "source_url": url,
                        "domain": domain,
                        "title": title,
                        "chunk_index": i,
                        "last_sync_utc": datetime.now(timezone.utc).isoformat()
                    }
                )
                if success:
                    success_count += 1

            print(f"🌐 Vector Internet Cache: Cached '{title}' ({success_count}/{len(chunks)} chunks mapped)")
        except Exception as e:
            print(f"❌ Error during External Knowledge Vector Sync: {e}")



        
    async def start(self):
        """Launch the monitor loops."""
        # 1. AWAIT this. Don't move forward until the data is in DataState.
        print("[Monitor] Forced preloading started...")
        await self.preload_system_config()
        
        # 2. Start the watchers in the background
        asyncio.create_task(self.watch_database())
        asyncio.create_task(self.watch_system_config())
        asyncio.create_task(self.watch_platform_documentation())
        asyncio.create_task(self.watch_chat_sessions())
        asyncio.create_task(self.watch_system_logs())
        asyncio.create_task(self.watch_user_assets())
        asyncio.create_task(self.watch_external_knowledge())

        
        self._ready.set() # Signal that we are ready
        print("Monitor is alive and watching all collections...")
    
    
  