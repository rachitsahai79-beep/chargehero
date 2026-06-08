"""Pydantic models for dispatch center domain."""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DispatchStatus(str, Enum):
    """Dispatch assignment status."""
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    ACKNOWLEDGED = "acknowledged"
    IN_TRANSIT = "in_transit"
    ON_SITE = "on_site"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EngineerAvailability(str, Enum):
    """Engineer availability status."""
    AVAILABLE = "available"
    ON_JOB = "on_job"
    LUNCH_BREAK = "lunch_break"
    OFF_DUTY = "off_duty"
    OFFLINE = "offline"


class ActiveAssignmentResponse(BaseModel):
    """Active job assignment."""
    ticket_id: str
    customer_name: str
    location: str
    engineer_id: str
    engineer_name: str
    assigned_at: datetime
    eta_minutes: int
    priority: str
    status: str
    distance_km: float
    customer_phone: str

    class Config:
        from_attributes = True


class EngineerAvailabilityResponse(BaseModel):
    """Engineer availability status."""
    engineer_id: str
    engineer_name: str
    availability_status: str
    current_location: str
    latitude: float
    longitude: float
    current_job_id: Optional[str]
    on_job_since: Optional[datetime]
    certifications: List[str]
    rating: float
    jobs_today: int
    last_online: datetime

    class Config:
        from_attributes = True


class DispatchMetricsResponse(BaseModel):
    """Dispatch center metrics."""
    total_pending_jobs: int
    jobs_in_dispatch: int
    jobs_assigned: int
    jobs_in_transit: int
    jobs_on_site: int
    average_dispatch_time_minutes: float
    average_eta_accuracy_percentage: float
    jobs_completed_today: int
    jobs_pending_sla: int
    customer_wait_time_average_minutes: float
    engineer_utilization_percentage: float
    dispatch_efficiency_score: float

    class Config:
        from_attributes = True


class EngineerPerformanceComparisonResponse(BaseModel):
    """Compare engineer performance."""
    engineer_id: str
    engineer_name: str
    jobs_completed_today: int
    average_resolution_time_minutes: float
    customer_satisfaction_score: float
    efficiency_score: float
    availability_percentage: float
    current_status: str
    response_time_secs: int
    acceptance_rate_percentage: float

    class Config:
        from_attributes = True


class DispatchQueueItemResponse(BaseModel):
    """Job in dispatch queue."""
    ticket_id: str
    customer_name: str
    charger_brand: str
    charger_type: str
    priority: str
    issue_category: str
    location: str
    latitude: float
    longitude: float
    created_at: datetime
    time_in_queue_minutes: int
    required_certifications: List[str]
    suitable_engineers: int

    class Config:
        from_attributes = True


class DispatchPerformanceReportResponse(BaseModel):
    """Overall dispatch performance metrics."""
    period_start: datetime
    period_end: datetime
    total_dispatches: int
    average_dispatch_time_minutes: float
    median_dispatch_time_minutes: float
    dispatch_success_rate_percentage: float
    customer_satisfaction_average: float
    engineer_acceptance_rate_percentage: float
    jobs_completed_on_time_percentage: float
    jobs_exceeding_sla_count: int
    peak_dispatch_hour: str
    least_busy_hour: str
    total_distance_traveled_km: float
    average_travel_distance_per_job_km: float


class DispatchHistoryResponse(BaseModel):
    """Historical dispatch record."""
    dispatch_id: str
    ticket_id: str
    engineer_id: str
    engineer_name: str
    dispatched_at: datetime
    assigned_at: Optional[datetime]
    completed_at: Optional[datetime]
    dispatch_time_minutes: float
    total_resolution_time_minutes: float
    customer_satisfaction: Optional[float]
    dispatch_efficiency_score: float
    status: str

    class Config:
        from_attributes = True


class DispatchReallocateRequest(BaseModel):
    """Reallocate assignment to different engineer."""
    ticket_id: str
    current_engineer_id: str
    new_engineer_id: str
    reason: Optional[str] = None

    @field_validator('current_engineer_id', 'new_engineer_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate engineer ID is not empty."""
        if not v or not v.strip():
            raise ValueError('Engineer ID required')
        return v


class DispatchPriorityUpdateRequest(BaseModel):
    """Update job priority in dispatch queue."""
    ticket_id: str
    priority: str  # critical, high, medium, low

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        """Validate priority value."""
        if v not in ['critical', 'high', 'medium', 'low']:
            raise ValueError('Priority must be critical, high, medium, or low')
        return v


class DispatchCentreKPIResponse(BaseModel):
    """KPI dashboard for dispatch centre."""
    efficiency_metrics: DispatchMetricsResponse
    engineer_comparisons: List[EngineerPerformanceComparisonResponse]
    active_assignments: List[ActiveAssignmentResponse]
    engineer_availability: List[EngineerAvailabilityResponse]
    queue_status: List[DispatchQueueItemResponse]
    performance_report: DispatchPerformanceReportResponse
