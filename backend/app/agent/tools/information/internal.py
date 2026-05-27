import asyncio
from typing import List, Dict, Any, Optional
import logging
from app.agent.Accessibility.vectordatabase import VectorManager

logger = logging.getLogger(__name__)

class Aquire:
    def __init__(
        self, 
        vector_db: VectorManager, 
        email: str, 
        queries: List[str],
        target_scope: Optional[str] = "all",
        limit_per_query: int = 3
    ):
        """
        Initializes the Acquisition Tool with stateful user session context and targets.
        """
        self.vector_db = vector_db
        self.email = email
        self.queries = queries or []
        self.target_scope = target_scope.lower() if target_scope else "all"
        self.limit_per_query = limit_per_query
        
        # Distance threshold: 1.0 means highly inclusive for l2/cosine distance spaces.
        self.DISTANCE_THRESHOLD = 1.0

    async def search_platform_documentation(self) -> List[Dict[str, Any]]:
        """
        Executes a multi-query concurrent search across the platform knowledge base.
        Filters out low-relevance results and removes duplicates across queries.
        """
        try:
            if not self.queries:
                return []

            # 1. Create asynchronous tasks using the instance level query config
            tasks = [
                self.vector_db.query(
                    collection_name="platform_knowledge",
                    query_text=query,
                    limit=self.limit_per_query,
                    filters={"type": "platform_documentation"}
                )
                for query in self.queries
            ]

            # 2. Fire all queries simultaneously
            results_lists = await asyncio.gather(*tasks)

            # 3. Process, clean, deduplicate, and score-filter results
            seen_ids = set()
            unified_results = []

            for raw_results in results_lists:
                for item in raw_results:
                    doc_id = item["id"]
                    score = item["score"]

                    # Skip if we already captured this piece from a previous query variant
                    if doc_id in seen_ids:
                        continue

                    # ChromaDB distance filter check
                    if score > self.DISTANCE_THRESHOLD:
                        logger.info(f"[Aquire] Dropped chunk {doc_id} due to weak relevance score: {score}")
                        continue

                    seen_ids.add(doc_id)
                    unified_results.append({
                        "id": doc_id,
                        "title": item["metadata"].get("title", "Global Guide"),
                        "category": item["metadata"].get("category", "General"),
                        "content": item["content"],
                        "score": score
                    })

            # Sort combined hits so the most relevant pieces sit right at the top
            unified_results.sort(key=lambda x: x["score"])
            return unified_results

        except Exception as e:
            logger.error(f"❌ Error in Aquire platform search: {e}")
            return []

    async def search_user_assets(self) -> List[Dict[str, Any]]:
        """
        Executes a multi-query concurrent search across user file descriptions and properties.
        Strictly isolated by user_email metadata filters to prevent overlap leakage.
        """
        try:
            if not self.queries:
                return []

            tasks = [
                self.vector_db.query(
                    collection_name="user_assets",
                    query_text=query,
                    limit=self.limit_per_query,
                    filters={"user_email": self.email}  # Strict runtime isolation lock
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

                    if doc_id in seen_ids:
                        continue

                    if score > self.DISTANCE_THRESHOLD:
                        logger.info(f"[Aquire] Dropped user asset {doc_id} due to score: {score}")
                        continue

                    seen_ids.add(doc_id)
                    unified_results.append({
                        "id": doc_id,
                        "file_name": item["metadata"].get("file_name", "unknown_file"),
                        "file_type": item["metadata"].get("file_type", "unknown_type"),
                        "session_id": item["metadata"].get("session_id"),
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
        Queries the user_history collection. Can filter for 'chat_session_summary' or 'system_log_event'.
        Uses combined dictionary filter matches to isolate account boundaries safely.
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

                    if doc_id in seen_ids:
                        continue

                    if score > self.DISTANCE_THRESHOLD:
                        continue

                    seen_ids.add(doc_id)
                    
                    # Construct generic payload mapping info
                    payload = {
                        "id": doc_id,
                        "session_id": item["metadata"].get("session_id"),
                        "content": item["content"],
                        "score": score
                    }
                    
                    # Include event-specific metadata if tracing system log metrics
                    if target_type == "system_log_event":
                        payload["event_type"] = item["metadata"].get("event_type")
                        payload["logged_at"] = item["metadata"].get("logged_at")

                    unified_results.append(payload)

            unified_results.sort(key=lambda x: x["score"])
            return unified_results

        except Exception as e:
            logger.error(f"❌ Error in Aquire history search for {target_type}: {e}")
            return []

    async def execute(self) -> Dict[str, Any]:
        """
        Main execution entry point for data collection.
        Directs query flows based on the class-level target scope.
        """
        results = {}

        # 1. Evaluate Global Platform Guidelines Request
        if self.target_scope in ["platform", "all"]:
            results["platform_docs"] = await self.search_platform_documentation()
            
        # 2. Evaluate Personal Upload Asset Request
        if self.target_scope in ["files", "user_files", "all"]:
            results["user_files"] = await self.search_user_assets()
            
        # 3. Evaluate Session Chat Summaries and Audit Logs Request
        if self.target_scope in ["logs", "user_logs", "chats", "all"]:
            # Route execution logic down the shared user_history vector container space
            results["chat_sessions"] = await self.search_user_history("chat_session_summary")
            results["system_logs"] = await self.search_user_history("system_log_event")

        return results