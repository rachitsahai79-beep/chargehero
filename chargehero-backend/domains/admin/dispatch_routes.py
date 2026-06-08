"""FastAPI routes for dispatch center domain."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from domains.admin.dispatch_models import (
    ActiveAssignmentResponse, EngineerAvailabilityResponse,
    DispatchMetricsResponse, EngineerPerformanceComparisonResponse,
    DispatchQueueItemResponse, DispatchPerformanceReportResponse,
    DispatchHistoryResponse, DispatchReallocateRequest,
    DispatchPriorityUpdateRequest, DispatchCentreKPIResponse
)
from domains.admin.dispatch_service import DispatchService
from domains.auth.dependencies import get_current_user
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


def _require_admin(current_user):
    """Check if user is admin."""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/admin/dispatch/active-assignments", response_model=list[ActiveAssignmentResponse])
async def get_active_assignments(
    status: str = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get all active job assignments (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        assignments = service.get_active_assignments(status)
        return assignments
    except Exception as e:
        logger.error(f"Error fetching active assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch active assignments")


@router.get("/admin/dispatch/engineer-availability", response_model=list[EngineerAvailabilityResponse])
async def get_engineer_availability(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get engineer availability status (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        availability = service.get_engineer_availability()
        return availability
    except Exception as e:
        logger.error(f"Error fetching engineer availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engineer availability")


@router.get("/admin/dispatch/metrics", response_model=DispatchMetricsResponse)
async def get_dispatch_metrics(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get dispatch center metrics (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        metrics = service.get_dispatch_metrics()

        if not metrics:
            raise HTTPException(status_code=500, detail="Failed to fetch metrics")

        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching dispatch metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dispatch metrics")


@router.get(
    "/admin/dispatch/engineer-performance",
    response_model=list[EngineerPerformanceComparisonResponse]
)
async def get_engineer_performance_comparison(
    limit: int = 10,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get engineer performance comparison (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        performance = service.get_engineer_performance_comparison(limit)
        return performance
    except Exception as e:
        logger.error(f"Error fetching engineer performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engineer performance")


@router.get("/admin/dispatch/queue", response_model=list[DispatchQueueItemResponse])
async def get_dispatch_queue(
    limit: int = 25,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get pending jobs in dispatch queue (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        queue = service.get_dispatch_queue(limit)
        return queue
    except Exception as e:
        logger.error(f"Error fetching dispatch queue: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dispatch queue")


@router.get("/admin/dispatch/performance-report", response_model=DispatchPerformanceReportResponse)
async def get_performance_report(
    days: int = 7,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get dispatch performance report (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        report = service.get_dispatch_performance_report(days)

        if not report:
            raise HTTPException(status_code=500, detail="Failed to generate report")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching performance report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch performance report")


@router.get("/admin/dispatch/history", response_model=list[DispatchHistoryResponse])
async def get_dispatch_history(
    limit: int = 50,
    days: int = 7,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get dispatch history (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        history = service.get_dispatch_history(limit, days)
        return history
    except Exception as e:
        logger.error(f"Error fetching dispatch history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dispatch history")


@router.post("/admin/dispatch/reallocate")
async def reallocate_assignment(
    request: DispatchReallocateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Reallocate job to different engineer (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        success = service.reallocate_assignment(
            request.ticket_id,
            request.current_engineer_id,
            request.new_engineer_id,
            request.reason
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to reallocate assignment")

        return {
            'status': 'reallocated',
            'ticket_id': request.ticket_id,
            'new_engineer_id': request.new_engineer_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reallocating assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to reallocate assignment")


@router.patch("/admin/dispatch/priority")
async def update_job_priority(
    request: DispatchPriorityUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update job priority in dispatch queue (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        success = service.update_priority(request.ticket_id, request.priority)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update priority")

        return {
            'status': 'updated',
            'ticket_id': request.ticket_id,
            'priority': request.priority
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating priority: {e}")
        raise HTTPException(status_code=500, detail="Failed to update priority")


@router.get("/admin/dispatch/kpi-dashboard", response_model=DispatchCentreKPIResponse)
async def get_kpi_dashboard(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get complete KPI dashboard for dispatch centre (admin only)."""
    _require_admin(current_user)

    try:
        service = DispatchService(db)
        dashboard = service.get_kpi_dashboard()

        if not dashboard or not dashboard.get('efficiency_metrics'):
            raise HTTPException(status_code=500, detail="Failed to fetch KPI dashboard")

        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching KPI dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch KPI dashboard")
