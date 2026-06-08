"""Pydantic models for service report domain."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List


class ServiceReportCreateRequest(BaseModel):
    """Create service report after job completion."""
    ticket_id: str
    work_description: str
    spare_parts_used: List[str] = []
    resolution_time_minutes: int

    @field_validator('work_description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError('Work description cannot be empty')
        if len(v) > 5000:
            raise ValueError('Description too long (max 5000 chars)')
        return v

    @field_validator('resolution_time_minutes')
    @classmethod
    def validate_time(cls, v):
        """Validate resolution time is positive."""
        if v <= 0:
            raise ValueError('Resolution time must be positive')
        return v


class ServiceReportPhotoRequest(BaseModel):
    """Request presigned URL for service report photo."""
    report_id: str
    photo_type: str  # 'before' or 'after'


class ServiceReportSignatureRequest(BaseModel):
    """Request presigned URL for customer signature."""
    report_id: str


class ServiceReportUpdateRequest(BaseModel):
    """Update service report with photo URLs."""
    before_photo_url: Optional[str] = None
    after_photo_url: Optional[str] = None
    customer_signature_url: Optional[str] = None


class ServiceReportRatingRequest(BaseModel):
    """Customer rating for completed job."""
    report_id: str
    rating: int

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is 1-5."""
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v


class ServiceReportResponse(BaseModel):
    """Service report response."""
    id: str
    ticket_id: str
    engineer_id: str
    work_description: str
    spare_parts_used: List[str]
    before_photo_url: Optional[str]
    after_photo_url: Optional[str]
    customer_signature_url: Optional[str]
    resolution_time_minutes: int
    rating_by_customer: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoUploadResponse(BaseModel):
    """Response with presigned URL for photo upload."""
    report_id: str
    presigned_url: str
    photo_type: str
    upload_expires_at: datetime


class SignatureUploadResponse(BaseModel):
    """Response with presigned URL for signature upload."""
    report_id: str
    presigned_url: str
    upload_expires_at: datetime
