import uuid
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

# Import ecosystem unified exception components
from error.codes import ErrorClassification
from error.exceptions import ToolBaseException

class VectorManager:
    COMPONENT_ID = "VectorManager"

    def __init__(self, vector_engine):
        self.engine = vector_engine
        self.client = vector_engine.client

    def _get_coll(self, collection_name: str):
        """
        Internal helper to ensure collection exists.
        Configures the collection space to use Cosine distance instead of L2 squared.
        """
        # [System Print] Monitoring collection initialization parameters
        print(f"📦 [VectorManager] Loading collection: '{collection_name}' with normalized Cosine Distance parameters.")
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # 🎯 Forces normalized Cosine Space (0.0 to 2.0)
        )
    
    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        """
        Breaks down long document markdown content into contextual slices.
        """
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            if i + chunk_size >= len(words):
                break
        return chunks

    async def upsert(
        self, 
        collection_name: str,
        content: str,
        doc_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Upgraded Batch Ingestion: Automatically slices content into chunks,
        creates deterministic chunk sub-IDs to avoid duplication, and builds embeddings.
        """
        print(f"\n📥 [VectorManager Ingestion] Initializing Upsert Matrix for Document ID: {doc_id}")
        try:
            # Check for standard parameter existence
            if not content or not doc_id:
                raise ToolBaseException(
                    classification=ErrorClassification.MISSING_ARGUMENT,
                    component_id=self.COMPONENT_ID,
                    custom_context="Ingestion content body or document identifier parameters cannot be empty."
                )

            collection = self._get_coll(collection_name)
            chunks = self.chunk_text(content)
            total_chunks = len(chunks)
            print(f"   ↳ Text slice calculation complete: Divided document into {total_chunks} chunk blocks.")

            ids_batch = []
            embeddings_batch = []
            metadatas_batch = []
            documents_batch = []

            for index, chunk in enumerate(chunks):
                # Deterministic child sub-ID formulation based on parent ID
                chunk_id = f"{doc_id}::chunk_{index}"
                
                # Enrich metadata with positional awareness fields
                chunk_meta = metadata.copy()
                chunk_meta["chunk_index"] = index
                chunk_meta["total_chunks"] = total_chunks
                if "last_sync_utc" not in chunk_meta:
                    chunk_meta["last_sync_utc"] = datetime.now(timezone.utc).isoformat()

                # Generate individual vector matrix
                vector = self.engine.get_embedding(chunk)

                ids_batch.append(chunk_id)
                embeddings_batch.append(vector)
                metadatas_batch.append(chunk_meta)
                documents_batch.append(chunk)

            # Push everything down to ChromaDB in a single batch call
            print(f"   ↳ Executing atomic ChromaDB batch update for {total_chunks} element arrays...")
            collection.upsert(
                ids=ids_batch,
                embeddings=embeddings_batch,
                metadatas=metadatas_batch,
                documents=documents_batch
            )
            print(f"✅ [VectorManager Ingestion] Successfully synced document '{doc_id}' across {total_chunks} chunks.")
            return True
        except ToolBaseException:
            # Propagate system unified error straight out to upstream routers
            raise
        except Exception as e:
            # Wrap unexpected raw native crashes into custom orchestration code tracking blocks
            raise ToolBaseException(
                classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                component_id=self.COMPONENT_ID,
                custom_context=f"ChromaDB batch ingestion pipeline crashed on collection '{collection_name}': {str(e)}"
            )

    async def query(
        self, 
        collection_name: str, 
        query_text: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid Search Architecture: Executes Dense Semantic Search and 
        Lexical BM25 Sparse matching side-by-side, unifying them via RRF.
        """
        print(f"\n🔍 [VectorManager Hybrid Query] Executing target lookup for text: '{query_text}'")
        try:
            # Validate input search criteria
            if not query_text or not query_text.strip():
                raise ToolBaseException(
                    classification=ErrorClassification.MISSING_ARGUMENT,
                    component_id=self.COMPONENT_ID,
                    custom_context="Search target query text string parameter cannot be left blank."
                )

            collection = self._get_coll(collection_name)
            total_elements = collection.count()
            print(f"   ↳ Current database index record count inside '{collection_name}': {total_elements}")

            if total_elements == 0:
                print("   ⚠️ [VectorManager Warning] Collection is empty. Returning blank candidate matrices.")
                return []

            # --- Engine A: Dense Semantic Vector Matching ---
            print("   ⚡ [Engine A] Extracting context vectors and matching dense cosine topologies...")
            query_vector = self.engine.get_embedding(query_text)
            
            # Fetch a wider candidate pool for re-ranking to maximize match quality
            candidate_pool_limit = min(limit * 3, total_elements)
            dense_raw = collection.query(
                query_embeddings=[query_vector],
                n_results=candidate_pool_limit,
                where=filters
            )

            dense_ranked_list = []
            if dense_raw.get("documents") and len(dense_raw["documents"]) > 0:
                for i in range(len(dense_raw["documents"][0])):
                    dense_ranked_list.append({
                        "id": dense_raw["ids"][0][i],
                        "content": dense_raw["documents"][0][i],
                        "metadata": dense_raw["metadatas"][0][i],
                        "distance_score": dense_raw["distances"][0][i]
                    })
            print(f"   ↳ Engine A complete. Found {len(dense_ranked_list)} semantic matches within constraints.")

            # --- Engine B: Lexical Sparse BM25 Matching ---
            print("   ⚡ [Engine B] Tokenizing corpus and parsing BM25 lexical relevance metrics...")
            all_records = collection.get(include=["documents", "metadatas"], where=filters)
            
            lexical_ranked_list = []
            if all_records.get("documents"):
                corpus = all_records["documents"]
                tokenized_corpus = [doc.lower().split() for doc in corpus]
                
                # Instantiating the BM25 system in memory for real-time document rank weighting
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = query_text.lower().split()
                scores = bm25.get_scores(tokenized_query)
                
                lexical_candidates = []
                for idx, score in enumerate(scores):
                    if score > 0.0:  # Filter out items with no keyword resonance
                        lexical_candidates.append({
                            "id": all_records["ids"][idx],
                            "content": corpus[idx],
                            "metadata": all_records["metadatas"][idx],
                            "bm25_score": score
                        })
                
                # Sort descending by text frequency prominence matches
                lexical_candidates.sort(key=lambda x: x["bm25_score"], reverse=True)
                lexical_ranked_list = lexical_candidates[:limit * 3]
            print(f"   ↳ Engine B complete. Captured {len(lexical_ranked_list)} structural term-match matches.")

            # --- Phase C: Reciprocal Rank Fusion (RRF) Blending ---
            print("   🔀 [Phase C] Fusing positional matrices via Reciprocal Rank Fusion (RRF)...")
            rrf_registry: Dict[str, Dict[str, Any]] = {}
            k_constant = 60 # Standard stabilization constant factor for positional equations

            # Rank Accumulator Loop for Dense Search Results
            for rank, item in enumerate(dense_ranked_list):
                doc_id = item["id"]
                if doc_id not in rrf_registry:
                    rrf_registry[doc_id] = {"item": item, "rrf_score": 0.0}
                rrf_registry[doc_id]["rrf_score"] += 1.0 / (k_constant + (rank + 1))

            # Rank Accumulator Loop for Lexical BM25 Results
            for rank, item in enumerate(lexical_ranked_list):
                doc_id = item["id"]
                if doc_id not in rrf_registry:
                    rrf_registry[doc_id] = {"item": item, "rrf_score": 0.0}
                rrf_registry[doc_id]["rrf_score"] += 1.0 / (k_constant + (rank + 1))

            # Compile entries and sort by RRF score descending
            unified_results = list(rrf_registry.values())
            unified_results.sort(key=lambda x: x["rrf_score"], reverse=True)

            # Structure response payload for upstream orchestrators
            formatted_output = []
            for entry in unified_results[:limit]:
                base_item = entry["item"]
                formatted_output.append({
                    "id": base_item["id"],
                    "content": base_item["content"],
                    "metadata": base_item["metadata"],
                    "score": entry["rrf_score"]  # High RRF score = strong positional agreement across both engines
                })

            print(f"🏁 [VectorManager Hybrid Query] Compilation complete. Emitting top {len(formatted_output)} consolidated chunks.\n")
            return formatted_output

        except ToolBaseException:
            raise
        except Exception as e:
            raise ToolBaseException(
                classification=ErrorClassification.ORCHESTRATION_EXHAUSTED,
                component_id=self.COMPONENT_ID,
                custom_context=f"Hybrid search sequence execution dropped on collection '{collection_name}': {str(e)}"
            )