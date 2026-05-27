import asyncio
import time
import httpx
import logging
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.agent.Accessibility.vectordatabase import VectorManager
from app.agent.Accessibility.database import DatabaseAccess  # Importing your provided database helper

logger = logging.getLogger(__name__)

class ExternalAquire:
    def __init__(self, 
                 vector_db: VectorManager, 
                 db_access: DatabaseAccess, 
                 queries: List[str], 
                 max_results: int = 4, 
                 bypass_cache: bool = False):
        """
        Orchestrates semantic data retrieval with a localized vector cache 
        and external search fallbacks.
        """
        self.vector_db = vector_db
        self.db = db_access
        self.queries = queries or []
        self.max_results = max_results
        self.bypass_cache = bypass_cache
        
        # Calibrated semantic overlap match distance threshold (0.0 to 0.7)
        self.CACHE_THRESHOLD = 0.7

    async def fetch_wikipedia_markdown(self, query: str) -> List[Dict[str, Any]]:
        results = []
        search_url = "https://en.wikipedia.org/w/api.php"
        
        # 1. Correctly define parameters used for the initial keyword search query phase
        search_params = {
            "action": "opensearch",
            "search": query,
            "limit": self.max_results,
            "format": "json"
        }
        
        headers = {
            "User-Agent": "CustomKnowledgeBot/1.0 (contact: humantouchconcept@gmail.com) Python-Httpx/0.27"
        }
        
        try:
            start_time = time.perf_counter()
            async with httpx.AsyncClient(headers=headers) as client:
                # Step 1: Perform the search to get candidate URLs
                search_res = await client.get(search_url, params=search_params, timeout=6.0)
                if search_res.status_code != 200:
                    print(f"⚠️ Wikipedia Search API Error: {search_res.status_code}")
                    return []
                
                search_data = search_res.json()
                titles, links = search_data[1], search_data[3]
                
                for title, url in zip(titles, links):
                    # Step 2: Fetch the plain-text layout data with optimized max-length targets
                    content_url = "https://en.wikipedia.org/w/api.php"
                    content_params = {
                        "action": "query",
                        "prop": "extracts",
                        "exintro": False,      # Pull comprehensive article body context
                        "explaintext": True,   # Convert HTML output layout to clean raw strings
                        "exlimit": "max",      # Pull maximum allowed paragraph data sections
                        "titles": title,
                        "format": "json"
                    }
                    
                    content_res = await client.get(content_url, params=content_params, timeout=6.0)
                    if content_res.status_code != 200:
                        continue
                        
                    pages = content_res.json().get("query", {}).get("pages", {})
                    raw_text = ""
                    for page_id, page_data in pages.items():
                        if "extract" in page_data:
                            raw_text = page_data["extract"]
                            break
                    
                    if not raw_text.strip():
                        continue
                    
                    # Step 3: Refine standard output into readable Markdown sections
                    markdown_content = f"# {title}\n\n"
                    lines = raw_text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("==") and line.endswith("=="):
                            heading_level = line.count("=") // 2
                            heading_name = line.replace("=", "").strip()
                            markdown_content += f"\n{'#' * (heading_level + 1)} {heading_name}\n"
                        else:
                            markdown_content += f"{line}\n"
                    
                    response_time = int((time.perf_counter() - start_time) * 1000)
                    
                    scraped_document = {
                        "url": url,
                        "domain": "en.wikipedia.org",
                        "title": title,
                        "raw_content": markdown_content.strip(),
                        "metadata": {
                            "scraped_by": "custom_scraper",
                            "response_time_ms": response_time,
                            "content_type": "text/html"
                        },
                        "created_at_utc": datetime.now(timezone.utc).isoformat(),
                        "last_accessed_utc": datetime.now(timezone.utc).isoformat()
                    }
                    results.append(scraped_document)
                    
        except Exception as e:
            logger.error(f"❌ Wikipedia Parsing Error for target '{query}': {e}")
            
        return results
    
    async def _query_vector_store(self, query: str) -> List[Dict[str, Any]]:
        """Queries the internal vector engine cache using the calibrated semantic distance score."""
        try:
            hits = await self.vector_db.query(
                collection_name="internet_knowledge",
                query_text=query,
                limit=self.max_results
            )
            
            valid_results = []
            for hit in hits:
                # Strict distance verification pass (0.0 to 0.7 check)
                if hit.get("score", 2.0) <= self.CACHE_THRESHOLD:
                    meta = hit.get("metadata", {})
                    valid_results.append({
                        "url": meta.get("source_url"),
                        "domain": meta.get("domain"),
                        "title": meta.get("title"),
                        "raw_content": hit.get("content"),
                        "metadata": {
                            "scraped_by": meta.get("type", "external_web_knowledge"),
                            "last_sync": meta.get("last_sync_utc")
                        },
                        "created_at_utc": meta.get("last_sync_utc"),
                        "last_accessed_utc": datetime.now(timezone.utc).isoformat()
                    })
            return valid_results
        except Exception as e:
            logger.warning(f"Vector Store lookup skipped: {e}")
            return []

    async def execute(self) -> List[Dict[str, Any]]:
        """
        Controls coordination loop across local caches, handles write fallbacks to MongoDB,
        waits out streaming updates, and ensures results are aggregated by timestamp.
        """
        if not self.queries:
            return []

        pending_external_searches = []
        final_aggregated_results = []

        # Step 1: Evaluate Cache Status for all target components
        if self.bypass_cache:
            print("🔄 Bypass Cache Flag Active: Forcing dynamic live lookup across queries.")
            pending_external_searches = list(self.queries)
        else:
            for query in self.queries:
                cached_hits = await self._query_vector_store(query)
                if cached_hits:
                    print(f"🎯 Vector Cache Hit [Score <= 0.7] for query: '{query}'.")
                    final_aggregated_results.extend(cached_hits)
                else:
                    print(f"🔍 Vector Cache Miss for query: '{query}'. Appending to web search queue.")
                    pending_external_searches.append(query)

        # Step 2: Fetch Missing Queries externally and commit them to MongoDB
        if pending_external_searches:
            newly_scraped_payloads = []
            
            # Gather search inputs concurrently
            search_tasks = [self.fetch_wikipedia_markdown(q) for q in pending_external_searches]
            completed_searches = await asyncio.gather(*search_tasks)
            
            for results_list in completed_searches:
                newly_scraped_payloads.extend(results_list)

            if newly_scraped_payloads:
                print(f"💾 Inserting {len(newly_scraped_payloads)} fresh scraped documents into MongoDB...")
                for doc in newly_scraped_payloads:
                    # Write to collection, triggering background streaming tasks in Monitor automatically
                    await self.db.add_one(collection="external_knowledge", data=doc)
                
                # Step 3: Wait window loop to ensure change stream processing loops finish updates
                wait_seconds = 3.5
                print(f"⏳ Sleeping for {wait_seconds}s to allow background Monitor Vector synchronization to complete...")
                await asyncio.sleep(wait_seconds)

                # Step 4: Final Vector pass loop targeting queries that missed previously
                for query in pending_external_searches:
                    fresh_vector_hits = await self._query_vector_store(query)
                    final_aggregated_results.extend(fresh_vector_hits)

        # Step 5: Deduplicate elements by URL
        seen_urls = set()
        deduplicated_results = []
        for doc in final_aggregated_results:
            url = doc.get("url")
            if url not in seen_urls:
                seen_urls.add(url)
                deduplicated_results.append(doc)

        # Step 6: Final Sort Pass: Bubble newest entries to top using 'created_at_utc' timestamps
        try:
            deduplicated_results.sort(
                key=lambda x: x.get("created_at_utc", "1970-01-01T00:00:00Z"), 
                reverse=True
            )
        except Exception as e:
            logger.error(f"Failed to apply timestamp sorting operation: {e}")

        return deduplicated_results