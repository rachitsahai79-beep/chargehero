"""Embedding service for semantic search using Claude API."""

import logging
from typing import Optional, List, Dict, Any
import anthropic
import json

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings for knowledge base items."""

    def __init__(self, db, api_key: str):
        """Initialize with database and Claude API key."""
        self.db = db
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Claude API."""
        try:
            # For now, use a simple hash-based embedding
            # In production, use proper embedding API
            embedding = self._simple_embedding(text)
            logger.info(f"Generated embedding for text of length {len(text)}")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def embed_knowledge_item(self, item_id: str, content: str) -> bool:
        """Generate and store embedding for a knowledge base item."""
        try:
            embedding = self.generate_embedding(content)
            if not embedding:
                raise Exception("Failed to generate embedding")

            # Store embedding as JSON string
            embedding_json = json.dumps(embedding)

            updated = self.db.table('copilot_knowledge_base').update({
                'embedding': embedding_json,
                'embedding_model': 'claude-semantic-v1'
            }).eq('id', item_id).execute()

            logger.info(f"Stored embedding for knowledge item {item_id}")
            return bool(updated.data)

        except Exception as e:
            logger.error(f"Error embedding knowledge item: {e}")
            return False

    def semantic_search(
        self,
        query: str,
        charger_brand: Optional[str] = None,
        charger_model: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using semantic similarity."""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                logger.warning("Failed to generate query embedding, falling back to keyword search")
                return self._keyword_search(query, charger_brand, charger_model, limit)

            # Get all knowledge base items with embeddings
            kb_query = self.db.table('copilot_knowledge_base').select('*')
            response = kb_query.execute()
            items = response.data or []

            # Filter by charger type if provided
            if charger_brand:
                items = [i for i in items if i.get('charger_brand') == charger_brand or i.get('charger_brand') is None]
            if charger_model:
                items = [i for i in items if i.get('charger_model') == charger_model or i.get('charger_model') is None]

            # Score items by embedding similarity
            scored_items = []
            for item in items:
                if not item.get('embedding'):
                    # Use keyword similarity for items without embeddings
                    score = self._keyword_similarity(query, item)
                else:
                    try:
                        item_embedding = json.loads(item['embedding'])
                        score = self._cosine_similarity(query_embedding, item_embedding)
                    except (json.JSONDecodeError, TypeError):
                        score = self._keyword_similarity(query, item)

                scored_items.append((item, score))

            # Sort by score and return top results
            scored_items.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in scored_items[:limit]]

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return self._keyword_search(query, charger_brand, charger_model, limit)

    def _keyword_search(
        self,
        query: str,
        charger_brand: Optional[str] = None,
        charger_model: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        try:
            kb_query = self.db.table('copilot_knowledge_base').select('*')
            response = kb_query.execute()
            items = response.data or []

            if charger_brand:
                items = [i for i in items if i.get('charger_brand') == charger_brand or i.get('charger_brand') is None]
            if charger_model:
                items = [i for i in items if i.get('charger_model') == charger_model or i.get('charger_model') is None]

            scored_items = []
            for item in items:
                score = self._keyword_similarity(query, item)
                if score > 0:
                    scored_items.append((item, score))

            scored_items.sort(key=lambda x: x[1], reverse=True)
            return [item for item, _ in scored_items[:limit]]

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []

    def _keyword_similarity(self, query: str, item: Dict[str, Any]) -> float:
        """Calculate keyword similarity between query and item."""
        query_words = set(query.lower().split())
        title_words = set(item.get('title', '').lower().split())
        content_words = set(item.get('content', '').lower().split())

        title_score = len(query_words & title_words) * 3
        content_score = len(query_words & content_words) * 1

        return title_score + content_score

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
        magnitude2 = sum(b ** 2 for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _simple_embedding(self, text: str) -> List[float]:
        """Generate a simple embedding for testing."""
        # This is a placeholder - in production use proper embedding
        # For now, create a deterministic embedding based on text content
        import hashlib

        # Create a hash of the text
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert hash bytes to floats in range [-1, 1]
        embedding = []
        for byte in hash_bytes:
            # Normalize byte (0-255) to float (-1 to 1)
            value = (byte / 127.5) - 1.0
            embedding.append(value)

        return embedding

    def bulk_embed_knowledge_base(self) -> Dict[str, Any]:
        """Generate embeddings for all knowledge base items without embeddings."""
        try:
            response = self.db.table('copilot_knowledge_base').select('*').execute()
            items = response.data or []

            processed = 0
            failed = 0

            for item in items:
                if not item.get('embedding'):
                    content = f"{item.get('title', '')} {item.get('content', '')}"
                    if self.embed_knowledge_item(item['id'], content):
                        processed += 1
                    else:
                        failed += 1

            logger.info(f"Bulk embedding: {processed} processed, {failed} failed")
            return {
                'processed': processed,
                'failed': failed,
                'total_items': len(items)
            }

        except Exception as e:
            logger.error(f"Error in bulk embedding: {e}")
            return {'error': str(e)}

    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about knowledge base embeddings."""
        try:
            response = self.db.table('copilot_knowledge_base').select('id', 'embedding').execute()
            items = response.data or []

            total_items = len(items)
            embedded_items = sum(1 for item in items if item.get('embedding'))
            unembedded_items = total_items - embedded_items

            return {
                'total_items': total_items,
                'embedded_items': embedded_items,
                'unembedded_items': unembedded_items,
                'coverage_percentage': round((embedded_items / total_items * 100), 1) if total_items > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {}
