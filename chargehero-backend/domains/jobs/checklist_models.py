"""Pydantic models for checklist domain - templates, items, responses."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class ChecklistType(str, Enum):
    """Types of checklists."""
    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    COMMISSION = "commission"
    ISSUE = "issue"


class ItemType(str, Enum):
    """Types of checklist items."""
    TEXT = "text"
    YES_NO = "yes_no"
    PHOTO = "photo"
    VIDEO = "video"
    SIGNATURE = "signature"


class ChecklistResponseStatus(str, Enum):
    """Status of checklist response."""
    IN_PROGRESS = "in_progress"
    COMPLETED_BY_ENGINEER = "completed_by_engineer"
    SUBMITTED_TO_CUSTOMER = "submitted_to_customer"
    APPROVED_BY_CUSTOMER = "approved_by_customer"
    REJECTED_BY_CUSTOMER = "rejected_by_customer"


# ============================================================================
# Template Models
# ============================================================================

class ChecklistItemRequest(BaseModel):
    """Checklist item in template."""
    item_number: int
    task_description: str
    expected_result: Optional[str] = None
    is_required: bool = True
    item_type: ItemType = ItemType.TEXT

    @field_validator('task_description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError('Task description cannot be empty')
        return v


class ChecklistTemplateRequest(BaseModel):
    """Create or update checklist template."""
    name: str
    checklist_type: ChecklistType
    charger_brand: Optional[str] = None
    charger_model: Optional[str] = None
    description: Optional[str] = None
    items: List[ChecklistItemRequest]

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate name is not empty."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        if len(v) > 200:
            raise ValueError('Name too long (max 200 chars)')
        return v

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        """Validate at least one item exists."""
        if not v:
            raise ValueError('Checklist must have at least one item')
        if len(v) > 50:
            raise ValueError('Too many items (max 50)')
        return v


class ChecklistItemResponse(BaseModel):
    """Checklist item response."""
    id: str
    template_id: str
    item_number: int
    task_description: str
    expected_result: Optional[str]
    is_required: bool
    item_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChecklistTemplateResponse(BaseModel):
    """Checklist template response."""
    id: str
    name: str
    checklist_type: str
    charger_brand: Optional[str]
    charger_model: Optional[str]
    description: Optional[str]
    is_active: bool
    items: List[ChecklistItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Response Models
# ============================================================================

class ChecklistItemMediaRequest(BaseModel):
    """Media upload for checklist item response."""
    media_type: str  # photo, video, signature
    file_size_bytes: int
    file_name: str


class ChecklistItemResponseRequest(BaseModel):
    """Engineer response to a checklist item."""
    checklist_item_id: str
    response_value: Optional[str] = None
    passed: Optional[bool] = None
    notes: Optional[str] = None
    media: Optional[List[ChecklistItemMediaRequest]] = None


class ChecklistResponseSubmitRequest(BaseModel):
    """Submit completed checklist responses."""
    template_id: str
    ticket_id: str
    items: List[ChecklistItemResponseRequest]

    @field_validator('items')
    @classmethod
    def validate_items(cls, v):
        """Validate at least one item."""
        if not v:
            raise ValueError('Must respond to at least one item')
        return v


class ChecklistItemMediaRecord(BaseModel):
    """Stored checklist item media."""
    id: str
    checklist_item_response_id: str
    media_url: str
    media_type: str
    uploaded_by: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ChecklistItemResponseRecord(BaseModel):
    """Stored checklist item response."""
    id: str
    checklist_response_id: str
    checklist_item_id: str
    response_value: Optional[str]
    passed: Optional[bool]
    notes: Optional[str]
    media: List[ChecklistItemMediaRecord] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ChecklistResponseRecord(BaseModel):
    """Stored checklist response."""
    id: str
    template_id: str
    ticket_id: str
    engineer_id: str
    status: str
    started_at: Optional[datetime]
    completed_by_engineer_at: Optional[datetime]
    submitted_to_customer_at: Optional[datetime]
    approved_by_customer_at: Optional[datetime]
    rejection_reason: Optional[str]
    items: List[ChecklistItemResponseRecord]
    created_at: datetime

    class Config:
        from_attributes = True


class ChecklistResponseUpdateRequest(BaseModel):
    """Update checklist response status."""
    status: ChecklistResponseStatus
    rejection_reason: Optional[str] = None


# ============================================================================
# Summary Models
# ============================================================================

class ChecklistItemMediaUploadRequest(BaseModel):
    """Request presigned URL for media upload."""
    checklist_item_response_id: str
    media_type: str  # photo, video, signature
    file_name: str
    file_size_bytes: int

    @field_validator('media_type')
    @classmethod
    def validate_media_type(cls, v):
        """Validate media type is supported."""
        if v not in ['photo', 'video', 'signature']:
            raise ValueError('Media type must be photo, video, or signature')
        return v

    @field_validator('file_size_bytes')
    @classmethod
    def validate_file_size(cls, v, info):
        """Validate file size matches limits."""
        media_type = info.data.get('media_type')
        max_sizes = {'photo': 10 * 1024 * 1024, 'video': 100 * 1024 * 1024, 'signature': 5 * 1024 * 1024}
        max_size = max_sizes.get(media_type, 10 * 1024 * 1024)
        if v > max_size:
            raise ValueError(f'File size exceeds limit for {media_type}')
        return v


class ChecklistItemMediaUploadResponse(BaseModel):
    """Response with presigned URL for media upload."""
    id: str
    presigned_url: str
    media_type: str
    upload_expires_at: datetime


class ChecklistSummaryResponse(BaseModel):
    """Summary of checklist completion."""
    total_items: int
    completed_items: int
    required_items: int
    passed_items: int
    completion_percentage: float
    status: str
    estimated_time_minutes: Optional[int] = None

    @field_validator('completion_percentage')
    @classmethod
    def validate_percentage(cls, v):
        """Validate percentage is 0-100."""
        if not 0 <= v <= 100:
            raise ValueError('Completion percentage must be 0-100')
        return v
