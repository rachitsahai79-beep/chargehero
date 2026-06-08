"""Pydantic models for jobs domain - chargers, tickets, dispatch, service reports."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TicketType(str, Enum):
    """Types of service tickets."""
    PREVENTIVE_MAINTENANCE = "preventive_maintenance"
    COMMISSION = "commission"
    ISSUE = "issue"


class Priority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(str, Enum):
    """Ticket workflow status."""
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ChargerStatus(str, Enum):
    """Charger operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class DispatchStatus(str, Enum):
    """Job dispatch assignment status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ============================================================================
# Charger Models
# ============================================================================

class ChargerBase(BaseModel):
    """Base charger information."""
    serial_number: str
    model: str
    brand: str
    address: str
    latitude: float
    longitude: float

    @field_validator('latitude')
    @classmethod
    def validate_latitude(cls, v):
        """Validate latitude range."""
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @field_validator('longitude')
    @classmethod
    def validate_longitude(cls, v):
        """Validate longitude range."""
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v


class ChargerRequest(ChargerBase):
    """Create or update charger."""
    status: ChargerStatus = ChargerStatus.ACTIVE


class ChargerResponse(ChargerBase):
    """Charger response with metadata."""
    id: str
    customer_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Ticket Models
# ============================================================================

class TicketRequest(BaseModel):
    """Create ticket."""
    charger_id: str
    ticket_type: TicketType
    fault_type: Optional[str] = None
    description: str
    priority: Priority = Priority.MEDIUM

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate description is not empty."""
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        if len(v) > 1000:
            raise ValueError('Description too long (max 1000 chars)')
        return v


class TicketResponse(BaseModel):
    """Ticket response with full details."""
    id: str
    charger_id: str
    customer_id: str
    ticket_type: str
    fault_type: Optional[str]
    description: str
    priority: str
    status: str
    sla_minutes: int
    assigned_engineer_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketUpdateRequest(BaseModel):
    """Update ticket status."""
    status: TicketStatus
    notes: Optional[str] = None


# ============================================================================
# Dispatch Models
# ============================================================================

class DispatchAssignmentResponse(BaseModel):
    """Dispatch assignment details."""
    id: str
    ticket_id: str
    engineer_id: str
    status: str
    dispatch_score: Optional[float]
    assigned_at: datetime
    accepted_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DispatchActionRequest(BaseModel):
    """Engineer action on dispatch assignment."""
    action: str  # "accept" or "reject"
    notes: Optional[str] = None

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is accept or reject."""
        if v not in ['accept', 'reject']:
            raise ValueError('Action must be "accept" or "reject"')
        return v


# ============================================================================
# Service Report Models
# ============================================================================

class ServiceReportRequest(BaseModel):
    """Submit service completion report."""
    ticket_id: str
    work_description: str
    spare_parts_used: Optional[List[str]] = None
    resolution_time_minutes: int

    @field_validator('work_description')
    @classmethod
    def validate_work_description(cls, v):
        """Validate work description."""
        if not v or not v.strip():
            raise ValueError('Work description cannot be empty')
        if len(v) > 2000:
            raise ValueError('Work description too long (max 2000 chars)')
        return v

    @field_validator('resolution_time_minutes')
    @classmethod
    def validate_time(cls, v):
        """Validate resolution time is positive."""
        if v <= 0:
            raise ValueError('Resolution time must be positive')
        return v


class ServiceReportResponse(BaseModel):
    """Service report response."""
    id: str
    ticket_id: str
    engineer_id: str
    work_description: str
    spare_parts_used: Optional[List[str]]
    before_photo_url: Optional[str]
    after_photo_url: Optional[str]
    customer_signature_url: Optional[str]
    resolution_time_minutes: int
    rating_by_customer: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Engineer Skills Models
# ============================================================================

class EngineerSkillRequest(BaseModel):
    """Add or update engineer skill/certification."""
    user_id: str
    charger_type: str
    charger_brand: str
    is_certified: bool = False


class EngineerSkillResponse(BaseModel):
    """Engineer skill response."""
    id: str
    user_id: str
    charger_type: str
    charger_brand: str
    is_certified: bool
    certified_by: Optional[str]
    certified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Earnings Models
# ============================================================================

class EarningsResponse(BaseModel):
    """Engineer earnings response."""
    id: str
    engineer_id: str
    ticket_id: str
    amount: float
    status: str
    paid_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class EarningsSummaryResponse(BaseModel):
    """Engineer earnings summary."""
    total_earned: float
    total_paid: float
    pending_amount: float
    completed_jobs: int
