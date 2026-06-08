"""Pydantic models for admin domain."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class EngineerStatus(str, Enum):
    """Engineer account status."""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class CertificationLevel(str, Enum):
    """Engineer certification levels."""
    TRAINEE = "trainee"
    CERTIFIED = "certified"
    EXPERT = "expert"
    MASTER = "master"


class EngineerListItem(BaseModel):
    """Engineer list response."""
    id: str
    name: str
    phone: str
    email: str
    status: str
    certification_level: str
    total_jobs: int
    completed_jobs: int
    average_rating: float
    active_tickets: int
    created_at: datetime

    class Config:
        from_attributes = True


class EngineerDetailResponse(BaseModel):
    """Detailed engineer information."""
    id: str
    name: str
    phone: str
    email: str
    status: str
    certification_level: str
    total_jobs: int
    completed_jobs: int
    average_rating: float
    active_tickets: int
    verified_skills: List[str]
    certifications: List[str]
    earnings_total: float
    earnings_pending: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EngineerUpdateRequest(BaseModel):
    """Update engineer status and certification."""
    status: Optional[str] = None
    certification_level: Optional[str] = None
    is_active: Optional[bool] = None


class EngineerStatisticsResponse(BaseModel):
    """Engineer performance statistics."""
    engineer_id: str
    engineer_name: str
    total_jobs: int
    completed_jobs: int
    in_progress_jobs: int
    average_rating: float
    total_earnings: float
    pending_earnings: float
    average_resolution_time_minutes: float
    sla_compliance_percentage: float
    customer_satisfaction_percentage: float


class AdminDashboardResponse(BaseModel):
    """Admin dashboard overview."""
    total_engineers: int
    active_engineers: int
    pending_engineers: int
    total_jobs: int
    completed_jobs: int
    in_progress_jobs: int
    total_revenue: float
    average_engineer_rating: float
    system_sla_compliance: float
    top_engineers: List[EngineerStatisticsResponse]


class EngineerAssignmentRequest(BaseModel):
    """Assign ticket to engineer."""
    ticket_id: str
    engineer_id: str


class BulkEngineerActionRequest(BaseModel):
    """Perform bulk action on engineers."""
    engineer_ids: List[str]
    action: str  # "activate", "suspend", "certify"
    reason: Optional[str] = None

    @field_validator('engineer_ids')
    @classmethod
    def validate_ids(cls, v):
        """Validate at least one engineer ID."""
        if not v:
            raise ValueError('At least one engineer ID required')
        return v


class EngineerTrainingRecord(BaseModel):
    """Training record for engineer."""
    id: str
    engineer_id: str
    training_name: str
    training_type: str  # "mandatory", "optional", "certification"
    status: str  # "pending", "in_progress", "completed"
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EngineerCertificationRequest(BaseModel):
    """Certify engineer for charger types."""
    engineer_id: str
    charger_brand: str
    charger_type: str


class RevenueReportResponse(BaseModel):
    """Revenue report for date range."""
    total_revenue: float
    total_fees: float
    net_revenue: float
    job_count: int
    average_job_revenue: float
    currency: str = "INR"
    period_start: datetime
    period_end: datetime
