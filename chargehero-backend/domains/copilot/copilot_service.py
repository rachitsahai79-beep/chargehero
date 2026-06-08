"""Business logic for copilot domain - AI-powered troubleshooting assistance."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import anthropic
from domains.copilot.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class CopilotService:
    """Service for AI-powered troubleshooting assistance using Claude API."""

    def __init__(self, db, api_key: str):
        """Initialize with database and Claude API key."""
        self.db = db
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.embedding_service = EmbeddingService(db, api_key)

    def query_copilot(self, engineer_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a copilot query and return AI-generated response."""
        try:
            # Search knowledge base for relevant information
            knowledge_items = self._search_knowledge_base(
                data.get('query'),
                data.get('charger_brand'),
                data.get('charger_model')
            )

            # Build context from knowledge base
            context = self._build_context(knowledge_items)

            # Generate response using Claude
            response = self._generate_response(
                query=data['query'],
                query_type=data.get('query_type'),
                context=context
            )

            # Store query and response
            stored = self.db.table('copilot_queries').insert({
                'engineer_id': engineer_id,
                'query': data['query'],
                'query_type': data.get('query_type'),
                'response': response['text'],
                'sources': ','.join([item['id'] for item in knowledge_items]),
                'confidence_score': response.get('confidence', 0.85),
                'usage_credits': response.get('credits', 10),
                'created_at': datetime.utcnow().isoformat()
            }).execute()

            if stored.data:
                logger.info(f"Stored copilot query {stored.data[0]['id']} for engineer {engineer_id}")
                return {
                    'id': stored.data[0]['id'],
                    'response': response['text'],
                    'sources': [item['title'] for item in knowledge_items],
                    'confidence_score': response.get('confidence', 0.85)
                }

            raise Exception("Failed to store copilot query")

        except Exception as e:
            logger.error(f"Error processing copilot query: {e}")
            raise

    def get_query_history(self, engineer_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get copilot query history for an engineer."""
        try:
            response = self.db.table('copilot_queries').select('*').eq(
                'engineer_id', engineer_id
            ).order('created_at', desc=True).limit(limit).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching query history: {e}")
            return []

    def store_feedback(self, query_id: str, is_helpful: bool, feedback: Optional[str] = None) -> bool:
        """Store user feedback on copilot response."""
        try:
            updated = self.db.table('copilot_queries').update({
                'is_helpful': is_helpful,
                'feedback': feedback
            }).eq('id', query_id).execute()

            logger.info(f"Stored feedback for query {query_id}")
            return bool(updated.data)

        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False

    def add_knowledge_base_item(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new item to the knowledge base."""
        try:
            response = self.db.table('copilot_knowledge_base').insert({
                'title': data['title'],
                'content': data['content'],
                'charger_brand': data.get('charger_brand'),
                'charger_model': data.get('charger_model'),
                'category': data['category'],
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()

            if response.data:
                logger.info(f"Added knowledge base item {response.data[0]['id']}")
                return response.data[0]

            raise Exception("Failed to add knowledge base item")

        except Exception as e:
            logger.error(f"Error adding knowledge base item: {e}")
            raise

    def get_knowledge_base_items(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get knowledge base items, optionally filtered by category."""
        try:
            query = self.db.table('copilot_knowledge_base').select('*')

            if category:
                query = query.eq('category', category)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching knowledge base items: {e}")
            return []

    def _search_knowledge_base(
        self,
        query: str,
        charger_brand: Optional[str] = None,
        charger_model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant items using semantic search."""
        try:
            # Use semantic search with embeddings
            results = self.embedding_service.semantic_search(
                query,
                charger_brand=charger_brand,
                charger_model=charger_model,
                limit=3
            )

            return results

        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []

    def _build_context(self, knowledge_items: List[Dict[str, Any]]) -> str:
        """Build context string from knowledge base items."""
        if not knowledge_items:
            return "No relevant knowledge base items found."

        context_parts = ["Here are relevant knowledge base articles:\n"]
        for i, item in enumerate(knowledge_items, 1):
            context_parts.append(f"\n{i}. {item['title']}")
            context_parts.append(f"Category: {item['category']}")
            if item.get('charger_brand'):
                context_parts.append(f"Brand: {item['charger_brand']}")
            if item.get('charger_model'):
                context_parts.append(f"Model: {item['charger_model']}")
            context_parts.append(f"\n{item['content']}\n")

        return "\n".join(context_parts)

    def _generate_response(
        self,
        query: str,
        query_type: str,
        context: str
    ) -> Dict[str, Any]:
        """Generate response using Claude API."""
        try:
            system_prompt = """You are ChargeHero Copilot, an expert troubleshooting assistant for EV charging equipment.

Your role is to help field engineers diagnose and resolve issues with EV chargers.

Guidelines:
1. Be concise but thorough in your explanations
2. Always prioritize safety - flag any safety concerns
3. Reference the knowledge base when available
4. Suggest next steps or when to escalate to support
5. Use clear, step-by-step instructions for procedures"""

            user_message = f"""Query Type: {query_type}

Engineer Question: {query}

{context}

Please provide a helpful response that:
1. Directly addresses the question
2. References relevant knowledge base articles if applicable
3. Suggests next steps for resolution"""

            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            response_text = message.content[0].text if message.content else ""

            return {
                'text': response_text,
                'confidence': 0.85,
                'credits': message.usage.input_tokens // 100
            }

        except Exception as e:
            logger.error(f"Error generating response from Claude: {e}")
            raise

    def get_statistics(self, engineer_id: Optional[str] = None) -> Dict[str, Any]:
        """Get copilot usage statistics."""
        try:
            query = self.db.table('copilot_queries').select('*')

            if engineer_id:
                query = query.eq('engineer_id', engineer_id)

            response = query.execute()
            queries = response.data or []

            total_queries = len(queries)
            helpful_count = sum(1 for q in queries if q.get('is_helpful') is True)
            unhelpful_count = sum(1 for q in queries if q.get('is_helpful') is False)
            avg_confidence = sum(q.get('confidence_score', 0) for q in queries) / total_queries if total_queries > 0 else 0

            return {
                'total_queries': total_queries,
                'helpful_responses': helpful_count,
                'unhelpful_responses': unhelpful_count,
                'average_confidence': round(avg_confidence, 2),
                'helpful_ratio': round(helpful_count / total_queries, 2) if total_queries > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
