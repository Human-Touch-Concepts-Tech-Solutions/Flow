import json
import asyncio
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Any, Union

# Import newly structured crawler core modules
from app.agent.tools.web.crawler.query import SearchApi
from app.agent.tools.web.crawler.crawl import Scraper

from app.agent.Accessibility.vectordatabase import VectorManager
from app.agent.Accessibility.database import DatabaseAccess

################==============================================================
# Import ecosystem unified exception components
################==============================================================
from error.codes import ErrorClassification
from error.exceptions import ToolBaseException


class ExternalAquire:
    COMPONENT_ID = "TOOL_0000::external"

    def __init__(
        self, 
        user_email: str,
        vector_db: VectorManager, 
        db_access: DatabaseAccess, 
        query: str, 
        cache_queries: List[str] = None, 
        max_results: int = 4, 
        bypass_cache: bool = False
    ):
        """
        Orchestrates semantic web data retrieval using an optimized 
        SearchEngine -> DeepCrawler sequence alongside local vector caching.
        """
        self.user_email = user_email
        self.vector_db = vector_db
        self.db = db_access
        self.query = query.strip() if query else ""
        self.cache_queries = cache_queries if cache_queries else []
        self.max_results = max_results
        self.bypass_cache = bypass_cache

    def _generate_invoice(self, formatted_output_len: int, output_type: str) -> None:
        """
        Generates and prints the tool execution metrics invoice payload.
        """
        invoice = {
            "type": "invoice",
            "user_email": self.user_email,
            "tool_id": self.COMPONENT_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "output_text_characters": formatted_output_len,
                "output_type": output_type  # 🎯 "cache" or "internet" based on data sourcing origin
            }
        }
        print("\n🧾 [ExternalAquire Invoice Generated]")
        print(json.dumps(invoice, indent=4, ensure_ascii=False))
        print("--------------------------------------\n")

    async def _query_single_vector_string(self, query_string: str) -> List[Dict[str, Any]]:
        """Queries the internal vector engine for a single query string asset."""
        print(f"🔹 [Cache Sync] Querying Hybrid Vector Database for: '{query_string}'")
        try:
            # We fetch slightly more chunks (max_results * 2) because individual chunks 
            # will be unified and compiled into complete document views during final processing step.
            hits = await self.vector_db.query(
                collection_name="internet_knowledge",
                query_text=query_string,
                limit= self.max_results* 2  # self.max_results 
            )
        
            valid_results = []
            for hit in hits:
                score = hit.get("score", 0.0)
                print(f"   ↳ Match Candidate found. Hybrid RRF Score: {score}")
                
                # 🎯 RRF adjustment: A positive score (> 0.0) means it successfully qualified 
                # inside either our Keyword (BM25) matrix or Dense Semantic Vector matrix.
                if score > 0.0:
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
        except Exception as cache_err:
            raise ToolBaseException(
                classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                component_id=self.COMPONENT_ID,
                custom_context=f"Vector store sub-query execution dropped: {str(cache_err)}"
            )

    async def _query_vector_store(self) -> List[Dict[str, Any]]:
        """Queries the vector database using either the targeted cache arrays or fallback query string."""
        # 1. Determine our evaluation query array execution matrix
        queries_to_run = self.cache_queries if self.cache_queries else [self.query]
        queries_to_run = [q.strip() for q in queries_to_run if q and q.strip()]

        if not queries_to_run:
            return []

        print(f"🔹 [Cache System] Running multi-query cache lookup pass across {len(queries_to_run)} variations...")
        
        # 2. Execute all search queries concurrently to keep processing instantaneous
        tasks = [self._query_single_vector_string(q) for q in queries_to_run]
        nested_results = await asyncio.gather(*tasks)
        
        # 3. Unpack and deduplicate variations across separate lists by URL immediately
        aggregated_hits = []
        seen_urls = set()
        
        for result_list in nested_results:
            for hit in result_list:
                url = hit.get("url")
                if url not in seen_urls:
                    seen_urls.add(url)
                    aggregated_hits.append(hit)
                    
        print(f"🔹 [Cache Sync] Completed. Extracted {len(aggregated_hits)} distinct qualifying records matching thresholds.")
        return aggregated_hits

    async def _background_db_commit(self, documents: List[Dict[str, Any]]):
        """Asynchronously writes freshly acquired content to MongoDB without halting request lifecycles."""
        print(f"⚡ [Background worker] Dispatching background synchronization pass for {len(documents)} elements...")
        for doc in documents:
            try:
                if "metadata" not in doc:
                    doc["metadata"] = {}
                doc["metadata"]["scraped_by"] = "external_web_knowledge"
                await self.db.add_one(collection="external_knowledge", data=doc)
            except Exception as mongo_err:
                raise ToolBaseException(
                    classification=ErrorClassification.BAD_GATEWAY_RESPONSE,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"MongoDB background write failure for doc '{doc.get('title', 'Unknown')}': {str(mongo_err)}"
                )
        print(f" [Background Worker Complete] Thread finished committing live scraped documents!")

    async def _fetch_live_web_knowledge(self) -> List[Dict[str, Any]]:
        """
        Orchestrates SearchApi keyword matching and pumps targets into the Scraper
        to capture clean, Gemini-refined semantic Markdown structures.
        """
        if not self.query:
            return []

        try:
            print(f"🔍 [Live Fetch] Initializing SearchApi sweep for: '{self.query}' (Limit: {self.max_results})")
            search_engine = SearchApi(
                query=self.query,
                num_results= 8,  # We fetch more initial links than max_results because the Scraper will filter and unify them into complete documents.
                output_type="json"
            )
            
            search_payload = await search_engine.execute()
            if not isinstance(search_payload, dict) or search_payload.get("status") != "success":
                print(f"[Live Fetch Error] SearchApi failed to return valid execution payloads.")
                raise ToolBaseException(
                    classification=ErrorClassification.BAD_GATEWAY_RESPONSE,
                    component_id=self.COMPONENT_ID,
                    custom_context=f"Search Engine response rejected during live pipeline execution for query: '{self.query}'"
                )
            
            target_urls = search_payload.get("extracted_links", [])
            if not target_urls:
                print(f"[Live Fetch Notice] SearchApi execution completed but returned 0 target links.")
                return []

            print(f"🚀 [Live Fetch] Found {len(target_urls)} targets. Booting deep Scraper array engine...")
            scraper = Scraper(
                url=target_urls,
                output_type="md",
            )
            
            raw_crawl_results = await scraper.execute()
            print(f"✅ [Live Fetch] Scraper cluster finished tracking targets. Normalizing internal dictionary structures...")

            crawl_items: List[Dict[str, Any]] = []
            
            if isinstance(raw_crawl_results, list):
                crawl_items = raw_crawl_results
            elif isinstance(raw_crawl_results, dict):
                if "results" in raw_crawl_results and isinstance(raw_crawl_results["results"], list):
                    crawl_items = raw_crawl_results["results"]
                elif any(k.startswith(("http://", "https://")) for k in raw_crawl_results.keys()):
                    for url_key, inner_payload in raw_crawl_results.items():
                        if isinstance(inner_payload, dict):
                            if "url" not in inner_payload:
                                inner_payload["url"] = url_key
                            crawl_items.append(inner_payload)
                else:
                    crawl_items = [raw_crawl_results]

            processed_documents = []
            for item in crawl_items:
                if not isinstance(item, dict):
                    continue

                content_body = item.get("results", item.get("raw_content", "")).strip()
                if not content_body and item.get("status") == "error":
                    continue

                meta_in = item.get("metadata", {})
                url_scraped = meta_in.get("url_scraped", item.get("url", ""))
                if not url_scraped and len(target_urls) == 1:
                    url_scraped = target_urls[0]
                
                domain = ""
                if url_scraped:
                    try:
                        domain = urlparse(url_scraped).netloc
                    except Exception:
                        pass

                scraped_document = {
                    "url": url_scraped,
                    "domain": domain,
                    "title": meta_in.get("title", item.get("title", "Untitled Web Resource")),
                    "raw_content": content_body,
                    "metadata": {
                        "scraped_by": "custom_scraper",
                        "content_type": "text/md"
                    },
                    "created_at_utc": meta_in.get("scraped_at_utc", datetime.now(timezone.utc).isoformat()),
                    "last_accessed_utc": datetime.now(timezone.utc).isoformat()
                }
                processed_documents.append(scraped_document)

            print(f"[Live Fetch Complete] Unified records generation pass finalized. Emitting {len(processed_documents)} assets.")
            return processed_documents

        except ToolBaseException:
            raise
        except Exception as live_err:
            raise ToolBaseException(
                classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                component_id=self.COMPONENT_ID,
                custom_context=f"Deep real-time search extraction sequence crashed fully: {str(live_err)}"
            )

    async def execute(self) -> Dict[str, Any]:
        """
        Coordinates multi-query cache operations and fires deep search pipeline fallbacks.
        Returns unified formatting layouts expected by upstream runtime engines.
        """
        print(f"\n🧩 [Orchestrator Start] Running ExternalAquire sequence for query: '{self.query}'")
        if not self.query:
            raise ToolBaseException(
                classification=ErrorClassification.MISSING_ARGUMENT,
                component_id=self.COMPONENT_ID,
                custom_context="The outbound query evaluation block cannot be empty or null value."
            )

        final_aggregated_results = []
        is_cache_hit = False

        ################==================================================
        # Step 1: Evaluate Vector Cache Status (Using the target array)
        ################==================================================
        if self.bypass_cache:
            print(f"🔄 [Orchestrator Control] Cache bypass argument detected. Routing query directly to live networks.")
        else:
            cached_hits = await self._query_vector_store()
            if cached_hits:
                print(f"🎯 [Orchestrator Control] Memory hit confirmed. Extracting documents from cache index...")
                final_aggregated_results.extend(cached_hits)
                is_cache_hit = True
            else:
                print(f"🔍 [Orchestrator Control] Vector database missed for query variations. Preparing live search parameters...")

        ################==================================================
        # Step 2: Fetch Missing Data via Live Search Matrix
        ################==================================================
        if not is_cache_hit:
            print("🌐 [Orchestrator Network Out] Firing Search API and Deep Web Scrapers...")
            newly_scraped_payloads = await self._fetch_live_web_knowledge()
            
            if newly_scraped_payloads:
                final_aggregated_results.extend(newly_scraped_payloads)
                asyncio.create_task(self._background_db_commit(newly_scraped_payloads))

        ################==================================================
        # Step 3: Deduplicate overlapping data targets safely by URL
        ################################################################==
        print(f"⚙️ [Processing Pass] Deduplicating target matches. Initial count: {len(final_aggregated_results)}")
        seen_urls = set()
        deduplicated_results = []
        for doc in final_aggregated_results:
            url = doc.get("url")
            if url not in seen_urls:
                seen_urls.add(url)
                deduplicated_results.append(doc)

        ################==================================================
        # Step 4: Chronological sorting (newest records move forward)
        ################################################################==
        try:
            deduplicated_results.sort(
                key=lambda x: x.get("created_at_utc", "1970-01-01T00:00:00Z"), 
                reverse=True
            )
        except Exception as sort_err:
            raise ToolBaseException(
                classification=ErrorClassification.MALFORMED_PAYLOAD,
                component_id=self.COMPONENT_ID,
                custom_context=f"Error sorting metadata datetime arrays: {str(sort_err)}"
            )

        ################==================================================
        # Step 5: Format and restructure directly into unified markdown layout
        ################==================================================
        if not deduplicated_results:
            print("❌ [Orchestrator Final] Web harvesting extraction returned 0 accessible metrics.")
            return {
                "status": "error",
                "results": f"No definitive information could be harvested for query: '{self.query}'",
                "metadata": []
            }

        combined_markdown_content = ""
        metadata_urls = []

        for doc in deduplicated_results:
            title_banner = f"## Source: {doc.get('title', 'Web Resource')}\n"
            url_banner = f"**Link:** {doc.get('url')}\n\n"
            combined_markdown_content += f"{title_banner}{url_banner}{doc.get('raw_content', '')}\n\n---\n\n"
            metadata_urls.append(doc.get("url"))

        # Determine billing tracking status labels
        invoice_type = "cache" if is_cache_hit else "internet"
        
        # Fire structural invoice delivery telemetry
        self._generate_invoice(
            formatted_output_len=len(combined_markdown_content),
            output_type=invoice_type
        )

        print(f"🏁 [Orchestrator Complete] Output package compiled successfully. Payload Length: {len(combined_markdown_content)} characters.\n")
        return {
            "status": "success",
            "results": combined_markdown_content.strip(),
            "metadata": metadata_urls
        }