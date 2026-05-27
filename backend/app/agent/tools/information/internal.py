import asyncio
from typing import List, Dict, Any, Optional, Union
import logging
from app.agent.Accessibility.vectordatabase import VectorManager


logger = logging.getLogger(__name__)

class Aquire:
    def __init__(
        self, 
        vector_db: VectorManager, 
        email: str, 
        queries: List[str],
        target_scope: Optional[Union[str, List[str]]] = "all",
        limit_per_query: int = 3,
        start_timeframe: Optional[str] = None  # Expected Format: ISO Timestamp String
    ):
        """
        Initializes the Acquisition Tool with stateful user session context, multi-scope targets, and timeframe caps.
        """
        self.vector_db = vector_db
        self.email = email
        self.queries = queries or []
        self.limit_per_query = limit_per_query
        self.start_timeframe = start_timeframe
        
        # Parse flexible scope definitions (lists, comma strings, or default fallbacks)
        if not target_scope:
            self.scopes = ["all"]
        elif isinstance(target_scope, list):
            self.scopes = [s.lower().strip() for s in target_scope]
        else:
            self.scopes = [s.lower().strip() for s in target_scope.split(",")]

        if "all" in self.scopes:
            self.scopes = ["all"]

        # Distance threshold: 1.0 means highly inclusive for l2/cosine distance spaces.
        self.DISTANCE_THRESHOLD = 2.0

    def _is_within_timeframe(self, item_metadata: Dict[str, Any]) -> bool:
        """
        Validates if a returned vector chunk falls within the requested timeframe boundaries.
        """
        if not self.start_timeframe:
            return True
            
        # Inspect variations of timestamps placed by the sync trackers
        item_time_str = item_metadata.get("logged_at") or item_metadata.get("last_sync_utc")
        if not item_time_str:
            return True # If no time info exists, keep it to be safe
            
        try:
            # Basic ISO string string comparison works directly if formatted uniformly
            return item_time_str >= self.start_timeframe
        except Exception:
            return True

    async def search_platform_documentation(self) -> List[Dict[str, Any]]:
        """
        Executes a multi-query concurrent search across the platform knowledge base.
        """
        try:
            if not self.queries:
                return []

            tasks = [
                self.vector_db.query(
                    collection_name="platform_knowledge",
                    query_text=query,
                    limit=self.limit_per_query,
                    filters={"type": "platform_documentation"}
                )
                for query in self.queries
            ]

            results_lists = await asyncio.gather(*tasks)
            seen_ids = set()
            unified_results = []

            for raw_results in results_lists:
                for item in raw_results:
                    doc_id = item["id"]
                    score = item["score"]

                    if doc_id in seen_ids or score > self.DISTANCE_THRESHOLD:
                        continue

                    seen_ids.add(doc_id)
                    unified_results.append({
                        "id": doc_id,
                        "title": item["metadata"].get("title", "Global Guide"),
                        "category": item["metadata"].get("category", "General"),
                        "content": item["content"],
                        "score": score
                    })

            unified_results.sort(key=lambda x: x["score"])
            return unified_results
        except Exception as e:
            logger.error(f"❌ Error in Aquire platform search: {e}")
            return []

    async def search_user_bio(self) -> List[Dict[str, Any]]:
        """
        Retrieves identity summaries and profile background stories for the contextual user email.
        """
        try:
            if not self.queries:
                return []

            tasks = [
                self.vector_db.query(
                    collection_name="user_memories",
                    query_text=query,
                    limit=1,  # Biographies are unified singular profiles
                    filters={"user_email": self.email}
                )
                for query in self.queries
            ]

            results_lists = await asyncio.gather(*tasks)
            seen_ids = set()
            unified_results = []

            for raw_results in results_lists:
                for item in raw_results:
                    doc_id = item["id"]
                    if doc_id in seen_ids or item["score"] > self.DISTANCE_THRESHOLD:
                        continue

                    seen_ids.add(doc_id)
                    unified_results.append({
                        "id": doc_id,
                        "content": item["content"],
                        "profession": item["metadata"].get("profession_tag"),
                        "score": item["score"]
                    })
            return unified_results
        except Exception as e:
            logger.error(f"❌ Error in Aquire user bio search: {e}")
            return []

    async def search_user_assets(self) -> List[Dict[str, Any]]:
        """
        Executes a multi-query concurrent search across user file descriptions and properties.
        """
        try:
            if not self.queries:
                return []

            tasks = [
                self.vector_db.query(
                    collection_name="user_assets",
                    query_text=query,
                    limit=self.limit_per_query,
                    filters={"user_email": self.email}
                )
                for query in self.queries
            ]

            results_lists = await asyncio.gather(*tasks)
            seen_ids = set()
            unified_results = []

            for raw_results in results_lists:
                for item in raw_results:
                    doc_id = item["id"]
                    score = item["score"]
                    metadata = item["metadata"]

                    if doc_id in seen_ids or score > self.DISTANCE_THRESHOLD:
                        continue

                    # Apply optional timeline cutoff evaluation
                    if not self._is_within_timeframe(metadata):
                        continue

                    seen_ids.add(doc_id)
                    unified_results.append({
                        "id": doc_id,
                        "file_name": metadata.get("file_name", "unknown_file"),
                        "file_type": metadata.get("file_type", "unknown_type"),
                        "session_id": metadata.get("session_id"),
                        "content": item["content"],
                        "score": score
                    })

            unified_results.sort(key=lambda x: x["score"])
            return unified_results
        except Exception as e:
            logger.error(f"❌ Error in Aquire user assets search: {e}")
            return []

    async def search_user_history(self, target_type: str) -> List[Dict[str, Any]]:
        """
        Queries the user_history collection for explicit sub-types ('chat_session_summary' or 'system_log_event').
        """
        try:
            if not self.queries:
                return []

            tasks = [
                self.vector_db.query(
                    collection_name="user_history",
                    query_text=query,
                    limit=self.limit_per_query,
                    filters={
                        "$and": [
                            {"user_email": self.email},
                            {"type": target_type}
                        ]
                    }
                )
                for query in self.queries
            ]

            results_lists = await asyncio.gather(*tasks)
            seen_ids = set()
            unified_results = []

            for raw_results in results_lists:
                for item in raw_results:
                    doc_id = item["id"]
                    score = item["score"]
                    metadata = item["metadata"]

                    if doc_id in seen_ids or score > self.DISTANCE_THRESHOLD:
                        continue

                    # Apply optional timeline cutoff evaluation
                    if not self._is_within_timeframe(metadata):
                        continue

                    seen_ids.add(doc_id)
                    
                    payload = {
                        "id": doc_id,
                        "session_id": metadata.get("session_id"),
                        "content": item["content"],
                        "score": score
                    }
                    
                    if target_type == "system_log_event":
                        payload["event_type"] = metadata.get("event_type")
                        payload["logged_at"] = metadata.get("logged_at")

                    unified_results.append(payload)

            unified_results.sort(key=lambda x: x["score"])
            return unified_results
        except Exception as e:
            logger.error(f"❌ Error in Aquire history search for {target_type}: {e}")
            return []

    async def execute(self) -> Dict[str, Any]:
        """
        Main execution entry point for data collection.
        Routes lookups cleanly across multiple targets or all scopes.
        """
        results = {}
        s = self.scopes

        # 1. Global Platform System Docs
        if "all" in s or "platform" in s:
            results["platform_docs"] = await self.search_platform_documentation()

        # 2. User Bio & Preferences Narrative
        if "all" in s or "bio" in s or "user_bio" in s:
            results["user_bio"] = await self.search_user_bio()
            
        # 3. User Upload Code/File Assets
        if "all" in s or "files" in s or "user_files" in s:
            results["user_files"] = await self.search_user_assets()
            
        # 4. User System Configuration/Error Logs
        if "all" in s or "logs" in s or "user_logs" in s:
            results["system_logs"] = await self.search_user_history("system_log_event")

        # 5. User Historical Chats
        if "all" in s or "chats" in s or "chat_sessions" in s:
            results["chat_sessions"] = await self.search_user_history("chat_session_summary")

        return results