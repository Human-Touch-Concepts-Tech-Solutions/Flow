import asyncio
import time
import httpx
import logging
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Any
from app.agent.Accessibility.vectordatabase import VectorManager
from app.agent.Accessibility.database import DatabaseAccess  # Preserved original import path

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
        and high-speed non-blocking external search fallbacks.
        """
        self.vector_db = vector_db
        self.db = db_access
        self.queries = queries or []
        self.max_results = max_results
        self.bypass_cache = bypass_cache
        
        # Calibrated semantic overlap match distance threshold (0.0 to 0.7)
        self.CACHE_THRESHOLD = 0.7

    async def fetch_wikipedia_markdown(self, query: str) -> List[Dict[str, Any]]:
        """
        Queries Wikipedia via OpenSearch, filters targets, and pulls massive, 
        complete page text structures using the full Action Parse engine.
        """
        results = []
        search_url = "https://en.wikipedia.org/w/api.php"
        
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
                    # 🛠️ Defensive Validation Filter: Stop unrelated semantic drift (e.g., 'Fast & Furious')
                    clean_query = query.lower()
                    if "fastapi" in clean_query and "fastapi" not in title.lower():
                        print(f"⏩ Skipping irrelevant Wikipedia match: '{title}' found for query '{query}'")
                        continue
                    
                    # Step 2: Fetch the HUGE complete wikitext layout using the official Parse engine
                    parse_url = "https://en.wikipedia.org/w/api.php"
                    parse_params = {
                        "action": "parse",
                        "page": title,
                        "prop": "wikitext",
                        "format": "json"
                    }
                    
                    parse_res = await client.get(parse_url, params=parse_params, timeout=8.0)
                    if parse_res.status_code != 200:
                        continue
                        
                    raw_wikitext = parse_res.json().get("parse", {}).get("wikitext", {}).get("*", "")
                    if not raw_wikitext.strip():
                        continue
                    
                    # Step 3: Parse macro layout string directly into clean structural Markdown
                    markdown_content = f"# {title}\n\n"
                    lines = raw_wikitext.split("\n")
                    
                    for line in lines:
                        line = line.strip()
                        # Discard raw categories, metadata macros, and template definitions
                        if not line or line.startswith("[[Category:") or line.startswith("{{") or line.endswith("}}"):
                            continue
                        
                        # Translate heading layers cleanly
                        if line.startswith("==") and line.endswith("=="):
                            heading_level = line.count("=") // 2
                            heading_name = line.replace("=", "").strip()
                            markdown_content += f"\n{'#' * (heading_level + 1)} {heading_name}\n"
                        else:
                            # Strip nested MediaWiki citation syntax blocks for cleaner context parsing
                            clean_line = re.sub(r'\{\{[Cc]ite.*?\}\}', '', line)
                            clean_line = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', clean_line)
                            if clean_line.strip():
                                markdown_content += f"{clean_line.strip()}\n"
                    
                    response_time = int((time.perf_counter() - start_time) * 1000)
                    
                    scraped_document = {
                        "url": url,
                        "domain": "en.wikipedia.org",
                        "title": title,
                        "raw_content": markdown_content[:50000].strip(),  # Context ceiling buffer protection
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
                if hit.get("score", 2.0) <= self.CACHE_THRESHOLD:
                    meta = hit.get("metadata", {})
                    valid_results.append({
                        "url": meta.get("source_url"),
                        "domain": meta.get("domain"),
                        "title": meta.get("title"),
                        "raw_content": hit.get("content"),
                        "metadata": {
                            "scraped_by": "internal_vector_cache",
                            "last_sync": meta.get("last_sync_utc")
                        },
                        "created_at_utc": meta.get("last_sync_utc"),
                        "last_accessed_utc": datetime.now(timezone.utc).isoformat()
                    })
            return valid_results
        except Exception as e:
            logger.warning(f"Vector Store lookup skipped: {e}")
            return []

    async def _background_db_commit(self, documents: List[Dict[str, Any]]):
        """Asynchronously writes freshly acquired content to MongoDB without halting request lifecycles."""
        for doc in documents:
            try:
                # Re-label origin tag so cache checks recognize it correctly later
                doc["metadata"]["scraped_by"] = "external_web_knowledge"
                await self.db.add_one(collection="external_knowledge", data=doc)
            except Exception as e:
                logger.error(f"Failed background commit for document {doc.get('title')}: {e}")
        print(f"⚡ Background Task: {len(documents)} documents successfully saved to MongoDB and syncing to Vector DB!")

    async def execute(self) -> List[Dict[str, Any]]:
        """
        Coordinates cache validation and triggers instant concurrent web retrieval 
        on cache misses with write-through tracking.
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

        # Step 2: Fetch Missing Queries externally and instantly append to return payloads
        if pending_external_searches:
            newly_scraped_payloads = []
            
            # Gather search inputs concurrently across the live network
            search_tasks = [self.fetch_wikipedia_markdown(q) for q in pending_external_searches]
            completed_searches = await asyncio.gather(*search_tasks)
            
            for results_list in completed_searches:
                newly_scraped_payloads.extend(results_list)

            if newly_scraped_payloads:
                # Write directly to the output array so the user receives the data instantly
                final_aggregated_results.extend(newly_scraped_payloads)
                
                # Hand data over to the non-blocking fire-and-forget background task
                asyncio.create_task(self._background_db_commit(newly_scraped_payloads))

        # Step 3: Deduplicate elements by URL
        seen_urls = set()
        deduplicated_results = []
        for doc in final_aggregated_results:
            url = doc.get("url")
            if url not in seen_urls:
                seen_urls.add(url)
                deduplicated_results.append(doc)

        # Step 4: Sort Pass: Newest entries bubble to top using 'created_at_utc' timestamps
        try:
            deduplicated_results.sort(
                key=lambda x: x.get("created_at_utc", "1970-01-01T00:00:00Z"), 
                reverse=True
            )
        except Exception as e:
            logger.error(f"Failed to apply timestamp sorting operation: {e}")

        return deduplicated_results