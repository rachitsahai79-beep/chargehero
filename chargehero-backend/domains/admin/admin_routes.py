"""FastAPI routes for admin domain."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from domains.admin.admin_models import (
    EngineerListItem, EngineerDetailResponse, EngineerUpdateRequest,
    EngineerStatisticsResponse, AdminDashboardResponse,
    EngineerCertificationRequest, RevenueReportResponse
)
from domains.admin.admin_service import AdminService
from domains.auth.dependencies import get_current_user
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


def _require_admin(current_user):
    """Check if user is admin."""
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/admin/engineers", response_model=list[EngineerListItem])
async def list_engineers(
    status: str = None,
    limit: int = 50,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get list of all engineers (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        engineers = service.get_engineers_list(status, limit)
        return engineers
    except Exception as e:
        logger.error(f"Error listing engineers: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engineers")


@router.get("/admin/engineers/{engineer_id}", response_model=EngineerDetailResponse)
async def get_engineer(
    engineer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get detailed engineer information (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        engineer = service.get_engineer_detail(engineer_id)

        if not engineer:
            raise HTTPException(status_code=404, detail="Engineer not found")

        return engineer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching engineer: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch engineer")


@router.patch("/admin/engineers/{engineer_id}", response_model=EngineerDetailResponse)
async def update_engineer(
    engineer_id: str,
    request: EngineerUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update engineer status or certification (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        engineer = service.update_engineer(engineer_id, request.model_dump(exclude_unset=True))

        if not engineer:
            raise HTTPException(status_code=404, detail="Engineer not found")

        return engineer
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating engineer: {e}")
        raise HTTPException(status_code=500, detail="Failed to update engineer")


@router.post("/admin/engineers/{engineer_id}/certify")
async def certify_engineer(
    engineer_id: str,
    request: EngineerCertificationRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Certify engineer for charger type (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        success = service.certify_engineer(
            engineer_id,
            request.charger_brand,
            request.charger_type
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to certify engineer")

        return {'status': 'certified', 'engineer_id': engineer_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error certifying engineer: {e}")
        raise HTTPException(status_code=500, detail="Failed to certify engineer")


@router.get("/admin/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get admin dashboard overview (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        overview = service.get_dashboard_overview()

        # Get top engineers
        engineers = service.get_engineers_list(status='active', limit=5)
        top_engineers = []
        for eng in engineers[:5]:
            stats = service.get_engineer_statistics(eng['id'])
            if stats:
                top_engineers.append(stats)

        return {
            **overview,
            'top_engineers': top_engineers,
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard")


@router.get("/admin/engineers/{engineer_id}/statistics", response_model=EngineerStatisticsResponse)
async def get_engineer_statistics(
    engineer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get engineer performance statistics (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        stats = service.get_engineer_statistics(engineer_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Engineer not found")

        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


@router.get("/admin/revenue-report", response_model=RevenueReportResponse)
async def get_revenue_report(
    days: int = 30,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get revenue report (admin only)."""
    _require_admin(current_user)

    try:
        service = AdminService(db)
        report = service.get_revenue_report(days)

        if not report:
            raise HTTPException(status_code=500, detail="Failed to generate report")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating revenue report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")
