import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class VectorManager:
    def __init__(self, vector_engine):
        self.engine = vector_engine
        self.client = vector_engine.client

    def _get_coll(self, collection_name: str):
        """Internal helper to ensure collection exists"""
        return self.client.get_or_create_collection(name=collection_name)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Dynamically handles text. 
        If text is short, returns it as a single chunk.
        If long, breaks it into overlapping pieces to preserve context.
        """
        words = text.split()
        
        # If the text is shorter than the chunk size, don't split it
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        # Use a sliding window to create overlapping chunks
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            
            # Stop if we've reached the end of the text
            if i + chunk_size >= len(words):
                break
        return chunks

    async def upsert(
        self, 
        collection_name: str,
        content: str,
        doc_id: str,
        metadata: Dict[str, Any]
    ):
        """
        Dynamic Upsert: Works for Tools, Memories, and Web Data.
        Uses deterministic IDs to prevent duplicates.
        """
        try:
            collection = self._get_coll(collection_name)
            vector = self.engine.get_embedding(content)

            # Chroma 'upsert' replaces if ID exists, adds if it doesn't
            collection.upsert(
                ids=[doc_id],
                embeddings=[vector],
                metadatas=[metadata],
                documents=[content]
            )
            return True
        except Exception as e:
            logger.error(f"❌ Upsert Error in {collection_name}: {e}")
            return False

    async def query(
        self, 
        collection_name: str, 
        query_text: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generic search logic that returns raw results from the collection.
        Score filtering is deferred to the calling service.
        """
        try:
            collection = self._get_coll(collection_name)
            query_vector = self.engine.get_embedding(query_text)

            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=filters
            )

            formatted = []
            # ChromaDB returns a list of lists (e.g., results["documents"][0])
            if results.get("documents") and len(results["documents"]) > 0:
                for i in range(len(results["documents"][0])):
                    formatted.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i]  # Return distance for manual filtering
                    })
            
            return formatted

        except Exception as e:
            logger.error(f"❌ Query Error in {collection_name}: {e}")
            return []