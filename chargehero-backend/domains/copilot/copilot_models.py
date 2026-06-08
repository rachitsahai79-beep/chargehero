"""Pydantic models for copilot domain."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class QueryType(str, Enum):
    """Types of copilot queries."""
    TROUBLESHOOTING = "troubleshooting"
    PROCEDURE = "procedure"
    COMPONENT = "component"
    MAINTENANCE = "maintenance"
    OTHER = "other"


class CopilotQueryRequest(BaseModel):
    """Request for copilot assistance."""
    query: str
    query_type: QueryType
    charger_brand: Optional[str] = None
    charger_model: Optional[str] = None
    ticket_id: Optional[str] = None

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        """Validate query is not empty."""
        if not v or not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v) > 2000:
            raise ValueError('Query too long (max 2000 chars)')
        return v


class CopilotResponseRequest(BaseModel):
    """Store copilot response for future reference."""
    query_id: str
    is_helpful: bool
    feedback: Optional[str] = None


class KnowledgeBaseItem(BaseModel):
    """Item in the knowledge base."""
    id: str
    title: str
    content: str
    charger_brand: Optional[str]
    charger_model: Optional[str]
    category: str
    embedding_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CopilotQueryResponse(BaseModel):
    """Response from copilot."""
    id: str
    query: str
    query_type: str
    response: str
    sources: List[str]
    confidence_score: float
    usage_credits: int
    created_at: datetime

    class Config:
        from_attributes = True


class CopilotHistoryResponse(BaseModel):
    """Copilot query history."""
    id: str
    engineer_id: str
    query: str
    response: str
    is_helpful: Optional[bool]
    feedback: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseCreateRequest(BaseModel):
    """Create knowledge base item."""
    title: str
    content: str
    charger_brand: Optional[str] = None
    charger_model: Optional[str] = None
    category: str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate title is not empty."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title too long (max 200 chars)')
        return v

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate content is not empty."""
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        """Validate category."""
        valid_categories = ['troubleshooting', 'maintenance', 'setup', 'safety', 'specification', 'other']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of {valid_categories}')
        return v


class SimilarItemResponse(BaseModel):
    """Similar knowledge base item for reference."""
    id: str
    title: str
    similarity_score: float
