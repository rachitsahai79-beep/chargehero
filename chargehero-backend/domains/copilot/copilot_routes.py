"""FastAPI routes for copilot domain."""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from domains.copilot.copilot_models import (
    CopilotQueryRequest, CopilotQueryResponse, CopilotHistoryResponse,
    KnowledgeBaseCreateRequest, KnowledgeBaseItem, CopilotResponseRequest
)
from domains.copilot.copilot_service import CopilotService
from domains.auth.dependencies import get_current_user
from shared.database import get_db
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def get_copilot_service(db=Depends(get_db)) -> CopilotService:
    """Dependency to get copilot service instance."""
    return CopilotService(db, settings.anthropic_api_key)


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
