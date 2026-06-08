"""Business logic for checklist domain - templates, responses, approvals."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from domains.jobs.checklist_models import ChecklistType
from domains.shared.file_upload import FileUploadService

logger = logging.getLogger(__name__)


class ChecklistService:
    """Service for managing checklist templates and responses."""

    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db

    # ========================================================================
    # Template Operations
    # ========================================================================

    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new checklist template."""
        try:
            response = self.db.table('jobs_checklist_templates').insert({
                'name': data['name'],
                'checklist_type': data['checklist_type'],
                'charger_brand': data.get('charger_brand'),
                'charger_model': data.get('charger_model'),
                'description': data.get('description'),
                'is_active': True
            }).execute()

            if response.data:
                template_id = response.data[0]['id']

                # Insert items
                items_to_insert = [
                    {
                        'template_id': template_id,
                        'item_number': item['item_number'],
                        'task_description': item['task_description'],
                        'expected_result': item.get('expected_result'),
                        'is_required': item.get('is_required', True),
                        'item_type': item.get('item_type', 'text')
                    }
                    for item in data.get('items', [])
                ]

                if items_to_insert:
                    self.db.table('jobs_checklist_items').insert(items_to_insert).execute()

                logger.info(f"Created template {template_id} with {len(items_to_insert)} items")
                return self.get_template(template_id)

            raise Exception("Failed to create template")
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template with all items."""
        try:
            response = self.db.table('jobs_checklist_templates').select('*').eq('id', template_id).execute()

            if not response.data:
                return None

            template = response.data[0]

            # Get items
            items_response = self.db.table('jobs_checklist_items').select('*').eq(
                'template_id', template_id
            ).order('item_number').execute()

            template['items'] = items_response.data or []
            return template

        except Exception as e:
            logger.error(f"Error fetching template: {e}")
            return None

    def list_templates(self, checklist_type: Optional[str] = None, charger_brand: Optional[str] = None) -> List[Dict[str, Any]]:
        """List checklist templates with optional filtering."""
        try:
            query = self.db.table('jobs_checklist_templates').select('*').eq('is_active', True)

            if checklist_type:
                query = query.eq('checklist_type', checklist_type)
            if charger_brand:
                query = query.eq('charger_brand', charger_brand)

            response = query.execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []

    # ========================================================================
    # Checklist Response Operations
    # ========================================================================

    def create_checklist_response(self, template_id: str, ticket_id: str, engineer_id: str) -> Dict[str, Any]:
        """Create a new checklist response for an engineer to fill out."""
        try:
            response = self.db.table('jobs_checklist_responses').insert({
                'template_id': template_id,
                'ticket_id': ticket_id,
                'engineer_id': engineer_id,
                'status': 'in_progress',
                'started_at': datetime.utcnow().isoformat()
            }).execute()

            if response.data:
                response_id = response.data[0]['id']
                logger.info(f"Created checklist response {response_id} for ticket {ticket_id}")
                return response.data[0]

            raise Exception("Failed to create checklist response")
        except Exception as e:
            logger.error(f"Error creating checklist response: {e}")
            raise

    def get_checklist_response(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Get checklist response with all item responses."""
        try:
            response = self.db.table('jobs_checklist_responses').select('*').eq('id', response_id).execute()

            if not response.data:
                return None

            checklist_response = response.data[0]

            # Get item responses
            items_response = self.db.table('jobs_checklist_item_responses').select('*').eq(
                'checklist_response_id', response_id
            ).execute()

            checklist_response['items'] = items_response.data or []
            return checklist_response

        except Exception as e:
            logger.error(f"Error fetching checklist response: {e}")
            return None

    def submit_checklist_response(self, response_id: str, items_data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Submit checklist responses for items."""
        try:
            # Insert item responses
            responses_to_insert = [
                {
                    'checklist_response_id': response_id,
                    'checklist_item_id': item['checklist_item_id'],
                    'response_value': item.get('response_value'),
                    'passed': item.get('passed'),
                    'notes': item.get('notes')
                }
                for item in items_data
            ]

            if responses_to_insert:
                self.db.table('jobs_checklist_item_responses').insert(responses_to_insert).execute()

            # Update response status
            updated = self.db.table('jobs_checklist_responses').update({
                'status': 'completed_by_engineer',
                'completed_by_engineer_at': datetime.utcnow().isoformat()
            }).eq('id', response_id).execute()

            logger.info(f"Submitted checklist response {response_id}")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error submitting checklist response: {e}")
            raise

    def get_checklist_for_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get the checklist response for a specific ticket."""
        try:
            response = self.db.table('jobs_checklist_responses').select('*').eq('ticket_id', ticket_id).execute()

            if not response.data:
                return None

            return self.get_checklist_response(response.data[0]['id'])

        except Exception as e:
            logger.error(f"Error fetching ticket checklist: {e}")
            return None

    def get_checklist_summary(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Get summary statistics for a checklist response."""
        try:
            response = self.db.table('jobs_checklist_responses').select('*').eq('id', response_id).execute()

            if not response.data:
                return None

            checklist = response.data[0]

            # Get item responses
            items_response = self.db.table('jobs_checklist_item_responses').select('*').eq(
                'checklist_response_id', response_id
            ).execute()

            items = items_response.data or []

            # Calculate summary
            total_items = len(items)
            completed_items = sum(1 for item in items if item.get('response_value') or item.get('passed') is not None)
            required_items = sum(1 for item in items if item.get('is_required', True))
            passed_items = sum(1 for item in items if item.get('passed') is True)

            completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0

            return {
                'total_items': total_items,
                'completed_items': completed_items,
                'required_items': required_items,
                'passed_items': passed_items,
                'completion_percentage': round(completion_percentage, 1),
                'status': checklist['status']
            }

        except Exception as e:
            logger.error(f"Error calculating checklist summary: {e}")
            return None

    # ========================================================================
    # Approval Operations
    # ========================================================================

    def submit_for_customer_approval(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Submit checklist for customer approval."""
        try:
            updated = self.db.table('jobs_checklist_responses').update({
                'status': 'submitted_to_customer',
                'submitted_to_customer_at': datetime.utcnow().isoformat()
            }).eq('id', response_id).execute()

            logger.info(f"Submitted checklist {response_id} for customer approval")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error submitting for approval: {e}")
            raise

    def approve_checklist(self, response_id: str) -> Optional[Dict[str, Any]]:
        """Customer approves the checklist."""
        try:
            updated = self.db.table('jobs_checklist_responses').update({
                'status': 'approved_by_customer',
                'approved_by_customer_at': datetime.utcnow().isoformat()
            }).eq('id', response_id).execute()

            logger.info(f"Checklist {response_id} approved by customer")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error approving checklist: {e}")
            raise

    def reject_checklist(self, response_id: str, reason: str) -> Optional[Dict[str, Any]]:
        """Customer rejects the checklist with reason."""
        try:
            updated = self.db.table('jobs_checklist_responses').update({
                'status': 'rejected_by_customer',
                'rejection_reason': reason
            }).eq('id', response_id).execute()

            logger.info(f"Checklist {response_id} rejected: {reason}")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error rejecting checklist: {e}")
            raise

    # ========================================================================
    # Media Operations
    # ========================================================================

    def get_media_upload_url(self, response_id: str, media_type: str, file_name: str, file_size_bytes: int) -> Optional[Dict[str, Any]]:
        """Get presigned URL for media upload."""
        try:
            # Create media record
            media_record = self.db.table('jobs_checklist_item_media').insert({
                'checklist_item_response_id': response_id,
                'media_type': media_type,
                'uploaded_by': 'pending',  # Will be updated after upload confirmation
                'uploaded_at': datetime.utcnow().isoformat()
            }).execute()

            if not media_record.data:
                raise Exception("Failed to create media record")

            media_id = media_record.data[0]['id']

            # Get presigned URL from FileUploadService
            file_upload_service = FileUploadService(self.db)
            folder = f"checklists/{response_id}"
            presigned_url = file_upload_service.get_presigned_upload_url(
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                content_type=self._get_content_type(media_type),
                folder=folder
            )

            logger.info(f"Generated presigned URL for media {media_id}")
            return {
                'id': media_id,
                'presigned_url': presigned_url,
                'media_type': media_type,
                'upload_expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting media upload URL: {e}")
            raise

    def confirm_media_upload(self, media_id: str, media_url: str, engineer_id: str) -> Optional[Dict[str, Any]]:
        """Confirm media upload after file is stored in S3."""
        try:
            updated = self.db.table('jobs_checklist_item_media').update({
                'media_url': media_url,
                'uploaded_by': engineer_id,
                'uploaded_at': datetime.utcnow().isoformat()
            }).eq('id', media_id).execute()

            logger.info(f"Confirmed media upload {media_id}")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error confirming media upload: {e}")
            raise

    def get_item_response_media(self, item_response_id: str) -> List[Dict[str, Any]]:
        """Get all media files for a checklist item response."""
        try:
            response = self.db.table('jobs_checklist_item_media').select('*').eq(
                'checklist_item_response_id', item_response_id
            ).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error fetching item response media: {e}")
            return []

    @staticmethod
    def _get_content_type(media_type: str) -> str:
        """Map media type to content type."""
        mapping = {
            'photo': 'image/jpeg',
            'video': 'video/mp4',
            'signature': 'image/png'
        }
        return mapping.get(media_type, 'application/octet-stream')

    def list_checklist_responses_for_engineer(self, engineer_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List checklist responses for an engineer."""
        try:
            query = self.db.table('jobs_checklist_responses').select('*').eq('engineer_id', engineer_id)

            if status:
                query = query.eq('status', status)

            response = query.execute()
            return response.data or []

        except Exception as e:
            logger.error(f"Error listing engineer checklists: {e}")
            return []
