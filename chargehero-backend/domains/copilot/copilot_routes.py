"""FastAPI routes for copilot domain."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from domains.copilot.copilot_models import (
    CopilotQueryRequest, CopilotQueryResponse, CopilotHistoryResponse,
    KnowledgeBaseCreateRequest, KnowledgeBaseItem, CopilotResponseRequest
)
from domains.copilot.copilot_service import CopilotService
from domains.copilot.embedding_service import EmbeddingService
from domains.auth.dependencies import get_current_user
from shared.database import get_db
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_copilot_service(db=Depends(get_db)) -> CopilotService:
    """Dependency to get copilot service instance."""
    return CopilotService(db, settings.anthropic_api_key)


def get_embedding_service(db=Depends(get_db)) -> EmbeddingService:
    """Dependency to get embedding service instance."""
    return EmbeddingService(db, settings.anthropic_api_key)


@router.post("/copilot/query", response_model=CopilotQueryResponse, status_code=status.HTTP_201_CREATED)
async def ask_copilot(
    request: CopilotQueryRequest,
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service)
):
    """
    Ask copilot for troubleshooting assistance.
    Engineers can ask questions about chargers and get AI-powered responses.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can use copilot")

    try:
        result = service.query_copilot(current_user['user_id'], request.model_dump())

        if not result:
            raise HTTPException(status_code=500, detail="Failed to generate copilot response")

        return {
            'id': result['id'],
            'query': request.query,
            'query_type': request.query_type,
            'response': result['response'],
            'sources': result['sources'],
            'confidence_score': result['confidence_score'],
            'usage_credits': 10,
            'created_at': datetime.now()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing copilot query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")


@router.get("/copilot/history", response_model=list[CopilotHistoryResponse])
async def get_copilot_history(
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service),
    limit: int = 50
):
    """Get copilot query history for current engineer."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can access their history")

    try:
        history = service.get_query_history(current_user['user_id'], limit)
        return history
    except Exception as e:
        logger.error(f"Error fetching copilot history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.post("/copilot/feedback/{query_id}")
async def provide_feedback(
    query_id: str,
    request: CopilotResponseRequest,
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service)
):
    """Provide feedback on copilot response."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can provide feedback")

    try:
        success = service.store_feedback(query_id, request.is_helpful, request.feedback)

        if not success:
            raise HTTPException(status_code=404, detail="Query not found")

        return {'status': 'feedback recorded'}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to store feedback")


@router.post("/knowledge-base", response_model=KnowledgeBaseItem, status_code=status.HTTP_201_CREATED)
async def create_knowledge_item(
    request: KnowledgeBaseCreateRequest,
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service)
):
    """
    Create a new knowledge base item.
    Only admins can add to knowledge base.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create knowledge base items")

    try:
        item = service.add_knowledge_base_item(request.model_dump())

        if not item:
            raise HTTPException(status_code=500, detail="Failed to create knowledge base item")

        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating knowledge base item: {e}")
        raise HTTPException(status_code=500, detail="Failed to create item")


@router.get("/knowledge-base", response_model=list[KnowledgeBaseItem])
async def get_knowledge_base(
    category: str = None,
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service)
):
    """Get knowledge base items, optionally filtered by category."""
    try:
        items = service.get_knowledge_base_items(category)
        return items
    except Exception as e:
        logger.error(f"Error fetching knowledge base: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch knowledge base")


@router.get("/copilot/statistics")
async def get_copilot_statistics(
    current_user = Depends(get_current_user),
    service = Depends(get_copilot_service)
):
    """Get copilot usage statistics for current user."""
    try:
        stats = service.get_statistics(current_user['user_id'])
        return stats
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.post("/embeddings/generate/{item_id}")
async def generate_item_embedding(
    item_id: str,
    current_user = Depends(get_current_user),
    service = Depends(get_embedding_service)
):
    """
    Generate and store embedding for a knowledge base item.
    Only admins can manage embeddings.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can manage embeddings")

    try:
        # Get the knowledge base item
        db = Depends(get_db)
        response = db.table('copilot_knowledge_base').select('*').eq('id', item_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Knowledge base item not found")

        item = response.data[0]
        content = f"{item.get('title', '')} {item.get('content', '')}"

        success = service.embed_knowledge_item(item_id, content)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to generate embedding")

        return {'status': 'embedding generated', 'item_id': item_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding")


@router.post("/embeddings/bulk-generate")
async def bulk_generate_embeddings(
    current_user = Depends(get_current_user),
    service = Depends(get_embedding_service)
):
    """
    Generate embeddings for all knowledge base items without embeddings.
    Only admins can trigger this.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can manage embeddings")

    try:
        result = service.bulk_embed_knowledge_base()
        return result
    except Exception as e:
        logger.error(f"Error in bulk embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embeddings")


@router.get("/embeddings/stats")
async def get_embedding_stats(
    current_user = Depends(get_current_user),
    service = Depends(get_embedding_service)
):
    """Get statistics about knowledge base embeddings."""
    try:
        stats = service.get_embedding_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching embedding stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")
