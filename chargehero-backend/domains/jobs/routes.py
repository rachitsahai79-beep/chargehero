"""FastAPI routes for jobs domain - chargers, tickets, dispatch, service reports."""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from domains.jobs.models import (
    ChargerRequest, ChargerResponse,
    TicketRequest, TicketResponse, TicketUpdateRequest,
    DispatchAssignmentResponse, DispatchActionRequest,
    ServiceReportRequest, ServiceReportResponse,
    EngineerSkillRequest, EngineerSkillResponse,
    EarningsResponse, EarningsSummaryResponse
)
from domains.jobs.service import JobsService
from domains.auth.dependencies import get_current_user
from shared.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Charger Endpoints
# ============================================================================

@router.post("/chargers", response_model=ChargerResponse, status_code=status.HTTP_201_CREATED)
async def create_charger(
    request: ChargerRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a new charger.
    Only customers can create chargers.
    """
    if current_user.get('role') != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can create chargers")

    try:
        service = JobsService(db)
        charger = service.create_charger(
            customer_id=current_user['user_id'],
            data=request.model_dump()
        )
        return charger
    except Exception as e:
        logger.error(f"Error creating charger: {e}")
        raise HTTPException(status_code=500, detail="Failed to create charger")


@router.get("/chargers/{charger_id}", response_model=ChargerResponse)
async def get_charger(
    charger_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get charger details by ID."""
    try:
        service = JobsService(db)
        charger = service.get_charger(charger_id)

        if not charger:
            raise HTTPException(status_code=404, detail="Charger not found")

        # Verify ownership if customer
        if current_user.get('role') == 'customer' and charger.get('customer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return charger
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching charger: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch charger")


@router.get("/customers/{customer_id}/chargers", response_model=List[ChargerResponse])
async def list_customer_chargers(
    customer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """List all chargers for a customer."""
    # Verify authorization
    if current_user.get('role') == 'customer' and customer_id != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        service = JobsService(db)
        chargers = service.list_customer_chargers(customer_id)
        return chargers
    except Exception as e:
        logger.error(f"Error listing chargers: {e}")
        raise HTTPException(status_code=500, detail="Failed to list chargers")


# ============================================================================
# Ticket Endpoints
# ============================================================================

@router.post("/chargers/{charger_id}/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    charger_id: str,
    request: TicketRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Create a service ticket for a charger.
    Only customers can create tickets.
    """
    if current_user.get('role') != 'customer':
        raise HTTPException(status_code=403, detail="Only customers can create tickets")

    try:
        service = JobsService(db)

        # Verify charger exists and belongs to customer
        charger = service.get_charger(charger_id)
        if not charger:
            raise HTTPException(status_code=404, detail="Charger not found")
        if charger.get('customer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        ticket = service.create_ticket(
            charger_id=charger_id,
            customer_id=current_user['user_id'],
            data=request.model_dump()
        )
        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to create ticket")


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get ticket details by ID."""
    try:
        service = JobsService(db)
        ticket = service.get_ticket(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Verify authorization
        if current_user.get('role') == 'customer' and ticket.get('customer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if current_user.get('role') == 'engineer' and ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ticket")


@router.put("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    request: TicketUpdateRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update ticket status."""
    try:
        service = JobsService(db)
        ticket = service.get_ticket(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Only assigned engineer or admin can update
        if current_user.get('role') == 'engineer' and ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        updated_ticket = service.update_ticket_status(ticket_id, request.status.value, request.notes)
        return updated_ticket
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        raise HTTPException(status_code=500, detail="Failed to update ticket")


# ============================================================================
# Dispatch Endpoints
# ============================================================================

@router.get("/jobs/open", response_model=List[TicketResponse])
async def list_open_jobs(
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    List all open tickets for dispatch.
    Only engineers can view open jobs.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can view open jobs")

    try:
        service = JobsService(db)
        tickets = service.list_open_tickets()
        return tickets
    except Exception as e:
        logger.error(f"Error listing open jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list open jobs")


@router.get("/engineers/{engineer_id}/assignments", response_model=List[DispatchAssignmentResponse])
async def list_engineer_assignments(
    engineer_id: str,
    status: str = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """List dispatch assignments for engineer."""
    # Verify authorization
    if current_user.get('role') == 'engineer' and engineer_id != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        service = JobsService(db)
        assignments = service.list_engineer_assignments(engineer_id, status)
        return assignments
    except Exception as e:
        logger.error(f"Error listing assignments: {e}")
        raise HTTPException(status_code=500, detail="Failed to list assignments")


@router.post("/assignments/{assignment_id}/accept", response_model=DispatchAssignmentResponse)
async def accept_assignment(
    assignment_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Engineer accepts a dispatch assignment."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can accept assignments")

    try:
        service = JobsService(db)
        assignment = service.get_dispatch_assignment(assignment_id)

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Verify it's assigned to this engineer
        if assignment.get('engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        updated = service.accept_assignment(assignment_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept assignment")


@router.post("/assignments/{assignment_id}/reject", response_model=DispatchAssignmentResponse)
async def reject_assignment(
    assignment_id: str,
    request: DispatchActionRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Engineer rejects a dispatch assignment."""
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can reject assignments")

    try:
        service = JobsService(db)
        assignment = service.get_dispatch_assignment(assignment_id)

        if not assignment:
            raise HTTPException(status_code=404, detail="Assignment not found")

        # Verify it's assigned to this engineer
        if assignment.get('engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        updated = service.reject_assignment(assignment_id)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting assignment: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject assignment")


# ============================================================================
# Service Report Endpoints
# ============================================================================

@router.post("/tickets/{ticket_id}/service-report", response_model=ServiceReportResponse, status_code=status.HTTP_201_CREATED)
async def create_service_report(
    ticket_id: str,
    request: ServiceReportRequest,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """
    Submit service completion report.
    Only assigned engineer can submit.
    """
    if current_user.get('role') != 'engineer':
        raise HTTPException(status_code=403, detail="Only engineers can submit reports")

    try:
        service = JobsService(db)
        ticket = service.get_ticket(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Verify engineer is assigned to this ticket
        if ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        report = service.create_service_report(
            ticket_id=ticket_id,
            engineer_id=current_user['user_id'],
            data=request.model_dump()
        )
        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating service report: {e}")
        raise HTTPException(status_code=500, detail="Failed to create service report")


@router.get("/tickets/{ticket_id}/service-report", response_model=ServiceReportResponse)
async def get_ticket_service_report(
    ticket_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get service report for a ticket."""
    try:
        service = JobsService(db)
        ticket = service.get_ticket(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        # Verify authorization
        if current_user.get('role') == 'customer' and ticket.get('customer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")
        if current_user.get('role') == 'engineer' and ticket.get('assigned_engineer_id') != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Unauthorized")

        report = service.get_ticket_service_report(ticket_id)
        if not report:
            raise HTTPException(status_code=404, detail="Service report not found")

        return report
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching service report: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch service report")


# ============================================================================
# Earnings Endpoints
# ============================================================================

@router.get("/engineers/{engineer_id}/earnings/summary", response_model=EarningsSummaryResponse)
async def get_engineer_earnings_summary(
    engineer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get engineer earnings summary."""
    # Verify authorization
    if current_user.get('role') == 'engineer' and engineer_id != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        service = JobsService(db)
        summary = service.get_engineer_earnings(engineer_id)
        return summary
    except Exception as e:
        logger.error(f"Error fetching earnings summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch earnings summary")


@router.get("/engineers/{engineer_id}/earnings", response_model=List[EarningsResponse])
async def list_engineer_earnings(
    engineer_id: str,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    """List earnings records for engineer."""
    # Verify authorization
    if current_user.get('role') == 'engineer' and engineer_id != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        service = JobsService(db)
        earnings = service.list_engineer_earnings(engineer_id)
        return earnings
    except Exception as e:
        logger.error(f"Error listing earnings: {e}")
        raise HTTPException(status_code=500, detail="Failed to list earnings")
