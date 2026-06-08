"""FastAPI routes for checklist domain - templates, responses, approvals."""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from domains.jobs.checklist_models import (
    ChecklistTemplateRequest, ChecklistTemplateResponse, ChecklistItemResponse,
    ChecklistResponseSubmitRequest, ChecklistResponseRecord, ChecklistResponseUpdateRequest,
    ChecklistSummaryResponse, ChecklistItemMediaUploadRequest, ChecklistItemMediaUploadResponse,
    ChecklistItemMediaRecord
)
from domains.jobs.checklist_service import ChecklistService
from domains.auth.dependencies import get_current_user
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Template Endpoints
# ============================================================================

@router.post("/checklist-templates", response_model=ChecklistTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    request: ChecklistTemplateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new checklist template.
    Only admins can create templates.
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create templates")

    try:
        service = ChecklistService(db)
        template = service.create_template(request.model_dump())
        return template
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail="Failed to create template")


@router.get("/checklist-templates/{template_id}", response_model=ChecklistTemplateResponse)
async def get_template(
    template_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get checklist template with all items."""
    try:
        service = ChecklistService(db)
        template = service.get_template(template_id)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching template: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch template")


@router.get("/checklist-templates", response_model=list[ChecklistTemplateResponse])
async def list_templates(
    checklist_type: str = None,
    charger_brand: str = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """List available checklist templates."""
    try:
        service = ChecklistService(db)
        templates = service.list_templates(checklist_type, charger_brand)
        return templates
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


# ============================================================================
# Checklist Response Endpoints
# ============================================================================

@router.post("/tickets/{ticket_id}/checklists", response_model=ChecklistResponseRecord, status_code=status.HTTP_201_CREATED)
async def create_checklist_for_ticket(
    ticket_id: str,
    template_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a checklist response for engineer to fill out.
    Only assigned engineers can create checklists.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can create checklists")

    try:
        service = ChecklistService(db)

        # Verify engineer is assigned to ticket
        ticket_response = db.table('jobs_tickets').select('*').eq('id', ticket_id).execute()
        if not ticket_response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")

        ticket = ticket_response.data[0]
        if ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Not assigned to this ticket")

        checklist = service.create_checklist_response(template_id, ticket_id, current_user['user_id'])
        return checklist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checklist")


@router.get("/checklists/{response_id}", response_model=ChecklistResponseRecord)
async def get_checklist(
    response_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get checklist response with all item responses."""
    try:
        service = ChecklistService(db)
        checklist = service.get_checklist_response(response_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        # Verify authorization
        if current_user.get('role') == 'engineer' and checklist.get('engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return checklist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch checklist")


@router.post("/checklists/{response_id}/submit", response_model=ChecklistResponseRecord)
async def submit_checklist(
    response_id: str,
    request: ChecklistResponseSubmitRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Submit completed checklist responses.
    Only the assigned engineer can submit.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can submit checklists")

    try:
        service = ChecklistService(db)

        # Verify engineer is the one who created this
        checklist = service.get_checklist_response(response_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        if checklist.get('engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # Submit responses
        updated = service.submit_checklist_response(response_id, request.items)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit checklist")


@router.get("/checklists/{response_id}/summary", response_model=ChecklistSummaryResponse)
async def get_checklist_summary(
    response_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get checklist completion summary."""
    try:
        service = ChecklistService(db)
        summary = service.get_checklist_summary(response_id)

        if not summary:
            raise HTTPException(status_code=404, detail="Checklist not found")

        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch summary")


# ============================================================================
# Approval Endpoints
# ============================================================================

@router.post("/checklists/{response_id}/submit-for-approval", response_model=ChecklistResponseRecord)
async def submit_for_approval(
    response_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Submit checklist for customer approval."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can submit for approval")

    try:
        service = ChecklistService(db)
        updated = service.submit_for_customer_approval(response_id)
        return updated
    except Exception as e:
        logger.error(f"Error submitting for approval: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit for approval")


@router.post("/checklists/{response_id}/approve", response_model=ChecklistResponseRecord)
async def approve_checklist(
    response_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Customer approves the checklist."""
    if current_user.get('role') != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can approve checklists")

    try:
        service = ChecklistService(db)
        updated = service.approve_checklist(response_id)
        return updated
    except Exception as e:
        logger.error(f"Error approving checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to approve checklist")


@router.post("/checklists/{response_id}/reject", response_model=ChecklistResponseRecord)
async def reject_checklist(
    response_id: str,
    request: ChecklistResponseUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Customer rejects the checklist."""
    if current_user.get('role') != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can reject checklists")

    try:
        service = ChecklistService(db)
        updated = service.reject_checklist(response_id, request.rejection_reason or "")
        return updated
    except Exception as e:
        logger.error(f"Error rejecting checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject checklist")


# ============================================================================
# Media Upload Endpoints
# ============================================================================

@router.post("/checklist-item-responses/{response_id}/media/upload-url", response_model=ChecklistItemMediaUploadResponse)
async def get_media_upload_url(
    response_id: str,
    request: ChecklistItemMediaUploadRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get presigned URL for media upload."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can upload media")

    try:
        service = ChecklistService(db)
        url_info = service.get_media_upload_url(
            response_id=request.checklist_item_response_id,
            media_type=request.media_type,
            file_name=request.file_name,
            file_size_bytes=request.file_size_bytes
        )

        if not url_info:
            raise HTTPException(status_code=500, detail="Failed to generate upload URL")

        return url_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting media upload URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to get upload URL")


@router.post("/checklist-item-responses/{response_id}/media/confirm", response_model=ChecklistItemMediaRecord)
async def confirm_media_upload(
    response_id: str,
    media_id: str,
    media_url: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Confirm media upload after file is stored in S3."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can confirm uploads")

    try:
        service = ChecklistService(db)
        media = service.confirm_media_upload(media_id, media_url, current_user['user_id'])

        if not media:
            raise HTTPException(status_code=404, detail="Media not found")

        return media
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming media upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm upload")


@router.get("/checklist-item-responses/{response_id}/media", response_model=list[ChecklistItemMediaRecord])
async def get_item_response_media(
    response_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get all media files for a checklist item response."""
    try:
        service = ChecklistService(db)
        media_list = service.get_item_response_media(response_id)
        return media_list
    except Exception as e:
        logger.error(f"Error fetching item response media: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch media")


@router.get("/tickets/{ticket_id}/checklist", response_model=ChecklistResponseRecord)
async def get_ticket_checklist(
    ticket_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get checklist for a specific ticket."""
    try:
        service = ChecklistService(db)
        checklist = service.get_checklist_for_ticket(ticket_id)

        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found for this ticket")

        return checklist
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket checklist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch checklist")
