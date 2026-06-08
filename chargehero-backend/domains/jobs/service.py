"""Business logic for jobs domain - chargers, tickets, dispatch, service reports."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from shared.database import SupabaseDB

logger = logging.getLogger(__name__)


class JobsService:
    """Service for managing jobs, tickets, and dispatch."""

    def __init__(self, db: SupabaseDB):
        """Initialize with database instance."""
        self.db = db

    # ========================================================================
    # Charger Operations
    # ========================================================================

    def create_charger(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new charger for customer."""
        try:
            response = self.db.table('jobs_chargers').insert({
                'customer_id': customer_id,
                'serial_number': data['serial_number'],
                'model': data['model'],
                'brand': data['brand'],
                'address': data['address'],
                'location': f"POINT({data['longitude']} {data['latitude']})",
                'status': data.get('status', 'active')
            }).execute()

            if response.data:
                logger.info(f"Created charger {response.data[0]['id']} for customer {customer_id}")
                return response.data[0]
            raise Exception("Failed to create charger")
        except Exception as e:
            logger.error(f"Error creating charger: {e}")
            raise

    def get_charger(self, charger_id: str) -> Optional[Dict[str, Any]]:
        """Get charger by ID."""
        try:
            response = self.db.table('jobs_chargers').select('*').eq('id', charger_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching charger {charger_id}: {e}")
            return None

    def list_customer_chargers(self, customer_id: str) -> List[Dict[str, Any]]:
        """List all chargers for a customer."""
        try:
            response = self.db.table('jobs_chargers').select('*').eq('customer_id', customer_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing chargers for customer {customer_id}: {e}")
            return []

    # ========================================================================
    # Ticket Operations
    # ========================================================================

    def create_ticket(self, charger_id: str, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a service ticket."""
        try:
            # Determine SLA based on priority
            sla_minutes = {
                'critical': 60,
                'high': 120,
                'medium': 240,
                'low': 480
            }.get(data['priority'], 240)

            response = self.db.table('jobs_tickets').insert({
                'charger_id': charger_id,
                'customer_id': customer_id,
                'ticket_type': data['ticket_type'],
                'fault_type': data.get('fault_type'),
                'description': data['description'],
                'priority': data['priority'],
                'status': 'open',
                'sla_minutes': sla_minutes
            }).execute()

            if response.data:
                ticket_id = response.data[0]['id']
                logger.info(f"Created ticket {ticket_id} for charger {charger_id}")
                return response.data[0]
            raise Exception("Failed to create ticket")
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            raise

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID."""
        try:
            response = self.db.table('jobs_tickets').select('*').eq('id', ticket_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching ticket {ticket_id}: {e}")
            return None

    def list_open_tickets(self) -> List[Dict[str, Any]]:
        """List all open tickets for dispatch."""
        try:
            response = self.db.table('jobs_tickets').select('*').eq('status', 'open').execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing open tickets: {e}")
            return []

    def list_engineer_tickets(self, engineer_id: str) -> List[Dict[str, Any]]:
        """List tickets assigned to engineer."""
        try:
            response = self.db.table('jobs_tickets').select('*').eq('assigned_engineer_id', engineer_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing tickets for engineer {engineer_id}: {e}")
            return []

    def update_ticket_status(self, ticket_id: str, status: str, notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update ticket status."""
        try:
            response = self.db.table('jobs_tickets').update({
                'status': status,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', ticket_id).execute()

            if response.data:
                logger.info(f"Updated ticket {ticket_id} status to {status}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_id}: {e}")
            raise

    # ========================================================================
    # Dispatch Operations
    # ========================================================================

    def assign_ticket_to_engineer(self, ticket_id: str, engineer_id: str, dispatch_score: float = 0.0) -> Dict[str, Any]:
        """Assign ticket to engineer via dispatch system."""
        try:
            response = self.db.table('jobs_dispatch_assignments').insert({
                'ticket_id': ticket_id,
                'engineer_id': engineer_id,
                'status': 'pending',
                'dispatch_score': dispatch_score,
                'assigned_at': datetime.utcnow().isoformat()
            }).execute()

            if response.data:
                assignment_id = response.data[0]['id']
                # Update ticket to assigned status
                self.db.table('jobs_tickets').update({
                    'status': 'assigned',
                    'assigned_engineer_id': engineer_id,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', ticket_id).execute()

                logger.info(f"Assigned ticket {ticket_id} to engineer {engineer_id} with score {dispatch_score}")
                return response.data[0]
            raise Exception("Failed to assign ticket")
        except Exception as e:
            logger.error(f"Error assigning ticket {ticket_id}: {e}")
            raise

    def get_dispatch_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Get dispatch assignment by ID."""
        try:
            response = self.db.table('jobs_dispatch_assignments').select('*').eq('id', assignment_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching assignment {assignment_id}: {e}")
            return None

    def list_engineer_assignments(self, engineer_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List dispatch assignments for engineer."""
        try:
            query = self.db.table('jobs_dispatch_assignments').select('*').eq('engineer_id', engineer_id)
            if status:
                query = query.eq('status', status)
            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing assignments for engineer {engineer_id}: {e}")
            return []

    def accept_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Engineer accepts dispatch assignment."""
        try:
            response = self.db.table('jobs_dispatch_assignments').update({
                'status': 'accepted',
                'accepted_at': datetime.utcnow().isoformat()
            }).eq('id', assignment_id).execute()

            if response.data:
                # Update ticket to in_progress
                assignment = response.data[0]
                self.db.table('jobs_tickets').update({
                    'status': 'in_progress',
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', assignment['ticket_id']).execute()

                logger.info(f"Engineer accepted assignment {assignment_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error accepting assignment {assignment_id}: {e}")
            raise

    def reject_assignment(self, assignment_id: str) -> Optional[Dict[str, Any]]:
        """Engineer rejects dispatch assignment."""
        try:
            response = self.db.table('jobs_dispatch_assignments').update({
                'status': 'rejected'
            }).eq('id', assignment_id).execute()

            if response.data:
                # Reset ticket status to open
                assignment = response.data[0]
                self.db.table('jobs_tickets').update({
                    'status': 'open',
                    'assigned_engineer_id': None,
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', assignment['ticket_id']).execute()

                logger.info(f"Engineer rejected assignment {assignment_id}")
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error rejecting assignment {assignment_id}: {e}")
            raise

    # ========================================================================
    # Service Report Operations
    # ========================================================================

    def create_service_report(self, ticket_id: str, engineer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create service completion report."""
        try:
            response = self.db.table('jobs_service_reports').insert({
                'ticket_id': ticket_id,
                'engineer_id': engineer_id,
                'work_description': data['work_description'],
                'spare_parts_used': data.get('spare_parts_used'),
                'resolution_time_minutes': data['resolution_time_minutes']
            }).execute()

            if response.data:
                # Update ticket to resolved
                self.db.table('jobs_tickets').update({
                    'status': 'resolved',
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', ticket_id).execute()

                logger.info(f"Created service report for ticket {ticket_id}")
                return response.data[0]
            raise Exception("Failed to create service report")
        except Exception as e:
            logger.error(f"Error creating service report: {e}")
            raise

    def get_service_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get service report by ID."""
        try:
            response = self.db.table('jobs_service_reports').select('*').eq('id', report_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching report {report_id}: {e}")
            return None

    def get_ticket_service_report(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get service report for a ticket."""
        try:
            response = self.db.table('jobs_service_reports').select('*').eq('ticket_id', ticket_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching report for ticket {ticket_id}: {e}")
            return None

    def update_service_report_with_files(self, report_id: str, before_photo: Optional[str] = None,
                                        after_photo: Optional[str] = None, signature: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update service report with photo and signature URLs."""
        try:
            update_data = {}
            if before_photo:
                update_data['before_photo_url'] = before_photo
            if after_photo:
                update_data['after_photo_url'] = after_photo
            if signature:
                update_data['customer_signature_url'] = signature

            if not update_data:
                return self.get_service_report(report_id)

            response = self.db.table('jobs_service_reports').update(update_data).eq('id', report_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error updating service report {report_id}: {e}")
            raise

    # ========================================================================
    # Earnings Operations
    # ========================================================================

    def create_earnings_record(self, engineer_id: str, ticket_id: str, amount: float) -> Dict[str, Any]:
        """Create earnings record for engineer."""
        try:
            response = self.db.table('jobs_earnings').insert({
                'engineer_id': engineer_id,
                'ticket_id': ticket_id,
                'amount': amount,
                'status': 'pending'
            }).execute()

            if response.data:
                logger.info(f"Created earnings record for engineer {engineer_id}: ₹{amount}")
                return response.data[0]
            raise Exception("Failed to create earnings record")
        except Exception as e:
            logger.error(f"Error creating earnings record: {e}")
            raise

    def get_engineer_earnings(self, engineer_id: str) -> Dict[str, Any]:
        """Get engineer earnings summary."""
        try:
            response = self.db.table('jobs_earnings').select('*').eq('engineer_id', engineer_id).execute()
            earnings = response.data or []

            total_earned = sum(e['amount'] for e in earnings)
            total_paid = sum(e['amount'] for e in earnings if e['status'] == 'paid')
            pending_amount = total_earned - total_paid
            completed_jobs = len([e for e in earnings if e['status'] == 'paid'])

            return {
                'total_earned': total_earned,
                'total_paid': total_paid,
                'pending_amount': pending_amount,
                'completed_jobs': completed_jobs
            }
        except Exception as e:
            logger.error(f"Error calculating engineer earnings: {e}")
            raise

    def list_engineer_earnings(self, engineer_id: str) -> List[Dict[str, Any]]:
        """List all earnings records for engineer."""
        try:
            response = self.db.table('jobs_earnings').select('*').eq('engineer_id', engineer_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing earnings for engineer {engineer_id}: {e}")
            return []
