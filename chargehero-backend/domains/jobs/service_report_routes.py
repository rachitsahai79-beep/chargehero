"""FastAPI routes for service report domain."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from domains.jobs.service_report_models import (
    ServiceReportCreateRequest, ServiceReportResponse, ServiceReportUpdateRequest,
    ServiceReportRatingRequest, PhotoUploadResponse, SignatureUploadResponse,
    ServiceReportPhotoRequest, ServiceReportSignatureRequest
)
from domains.jobs.service_report_service import ServiceReportService
from domains.auth.dependencies import get_current_user
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/tickets/{ticket_id}/service-reports", response_model=ServiceReportResponse, status_code=status.HTTP_201_CREATED)
async def create_service_report(
    ticket_id: str,
    request: ServiceReportCreateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a service report for a completed job.
    Only assigned engineer can create the report.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can create service reports")

    try:
        service = ServiceReportService(db)

        # Verify ticket exists and is assigned to engineer
        ticket_response = db.table('jobs_tickets').select('*').eq('id', ticket_id).execute()
        if not ticket_response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket = ticket_response.data[0]
        if ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not assigned to this ticket")

        # Create service report
        report = service.create_report(ticket_id, current_user['user_id'], request.model_dump())
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating service report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create service report")


@router.get("/service-reports/{report_id}", response_model=ServiceReportResponse)
async def get_service_report(
    report_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get service report details."""
    try:
        service = ServiceReportService(db)
        report = service.get_report(report_id)

        if not report:
            raise HTTPException(status_code=404, detail="Service report not found")

        # Verify authorization
        if current_user.get('role') == 'engineer' and report.get('engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching service report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service report")


@router.get("/tickets/{ticket_id}/service-reports", response_model=ServiceReportResponse)
async def get_ticket_service_report(
    ticket_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get service report for a specific ticket."""
    try:
        service = ServiceReportService(db)
        report = service.get_report_by_ticket(ticket_id)

        if not report:
            raise HTTPException(status_code=404, detail="Service report not found for this ticket")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket service report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service report")


@router.post("/service-reports/{report_id}/photo-upload-url", response_model=PhotoUploadResponse)
async def get_photo_upload_url(
    report_id: str,
    request: ServiceReportPhotoRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get presigned URL for service report photo upload."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can upload photos")

    try:
        service = ServiceReportService(db)
        url_info = service.get_photo_upload_url(report_id, request.photo_type)

        if not url_info:
            raise HTTPException(status_code=500, detail="Failed to generate upload URL")

        return url_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo upload URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upload URL")


@router.post("/service-reports/{report_id}/signature-upload-url", response_model=SignatureUploadResponse)
async def get_signature_upload_url(
    report_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get presigned URL for customer signature upload."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can request signature upload")

    try:
        service = ServiceReportService(db)
        url_info = service.get_signature_upload_url(report_id, current_user['user_id'])

        if not url_info:
            raise HTTPException(status_code=500, detail="Failed to generate upload URL")

        return url_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signature upload URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upload URL")


@router.patch("/service-reports/{report_id}/photos", response_model=ServiceReportResponse)
async def update_report_photos(
    report_id: str,
    request: ServiceReportUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update service report with photo and signature URLs."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can update reports")

    try:
        service = ServiceReportService(db)
        report = service.update_report_photos(report_id, request.model_dump(exclude_unset=True))

        if not report:
            raise HTTPException(status_code=404, detail="Service report not found")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating report photos: {e}")
        raise HTTPException(status_code=500, detail="Failed to update report")


@router.post("/service-reports/{report_id}/rate", response_model=ServiceReportResponse)
async def rate_service_report(
    report_id: str,
    request: ServiceReportRatingRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Add customer rating to service report.
    Only customers can rate service reports.
    """
    if current_user.get('role') != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can rate service reports")

    try:
        service = ServiceReportService(db)
        report = service.add_customer_rating(report_id, request.rating)

        if not report:
            raise HTTPException(status_code=404, detail="Service report not found")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding rating: {e}")
        raise HTTPException(status_code=500, detail="Failed to add rating")


@router.get("/engineers/{engineer_id}/service-reports", response_model=list[ServiceReportResponse])
async def list_engineer_reports(
    engineer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """List all service reports for an engineer."""
    try:
        service = ServiceReportService(db)
        reports = service.list_engineer_reports(engineer_id)
        return reports
    except Exception as e:
        logger.error(f"Error listing engineer reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reports")
