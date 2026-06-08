"""Business logic for service report domain."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from domains.shared.file_upload import FileUploadService

logger = logging.getLogger(__name__)


class ServiceReportService:
    """Service for managing service reports."""

    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db

    def create_report(self, ticket_id: str, engineer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service report."""
        try:
            response = self.db.table('jobs_service_reports').insert({
                'ticket_id': ticket_id,
                'engineer_id': engineer_id,
                'work_description': data['work_description'],
                'spare_parts_used': data.get('spare_parts_used', []),
                'resolution_time_minutes': data['resolution_time_minutes'],
                'created_at': datetime.utcnow().isoformat()
            }).execute()

            if response.data:
                report_id = response.data[0]['id']
                logger.info(f"Created service report {report_id} for ticket {ticket_id}")
                return response.data[0]

            raise Exception("Failed to create service report")
        except Exception as e:
            logger.error(f"Error creating service report: {e}")
            raise

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get service report by ID."""
        try:
            response = self.db.table('jobs_service_reports').select('*').eq('id', report_id).execute()

            if not response.data:
                return None

            return response.data[0]

        except Exception as e:
            logger.error(f"Error fetching service report: {e}")
            return None

    def get_report_by_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get service report for a specific ticket."""
        try:
            response = self.db.table('jobs_service_reports').select('*').eq('ticket_id', ticket_id).execute()

            if not response.data:
                return None

            return response.data[0]

        except Exception as e:
            logger.error(f"Error fetching service report for ticket: {e}")
            return None

    def get_photo_upload_url(self, report_id: str, photo_type: str) -> Optional[Dict[str, Any]]:
        """Get presigned URL for photo upload."""
        try:
            # Verify report exists
            report = self.get_report(report_id)
            if not report:
                raise Exception("Service report not found")

            # Get presigned URL from FileUploadService
            file_upload_service = FileUploadService(self.db)
            presigned_url = file_upload_service.get_presigned_url_for_photo(report['ticket_id'], photo_type)

            if not presigned_url:
                raise Exception("Failed to generate presigned URL")

            logger.info(f"Generated presigned URL for {photo_type} photo of report {report_id}")
            return {
                'report_id': report_id,
                'presigned_url': presigned_url.get('presigned_url'),
                'photo_type': photo_type,
                'upload_expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting photo upload URL: {e}")
            raise

    def get_signature_upload_url(self, report_id: str, engineer_id: str) -> Optional[Dict[str, Any]]:
        """Get presigned URL for signature upload."""
        try:
            # Verify report exists
            report = self.get_report(report_id)
            if not report:
                raise Exception("Service report not found")

            # Get presigned URL from FileUploadService
            file_upload_service = FileUploadService(self.db)
            presigned_url = file_upload_service.get_presigned_url_for_signature(report['ticket_id'], engineer_id)

            if not presigned_url:
                raise Exception("Failed to generate presigned URL")

            logger.info(f"Generated presigned URL for signature of report {report_id}")
            return {
                'report_id': report_id,
                'presigned_url': presigned_url.get('presigned_url'),
                'upload_expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting signature upload URL: {e}")
            raise

    def update_report_photos(self, report_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update report with photo and signature URLs."""
        try:
            update_data = {}
            if 'before_photo_url' in data and data['before_photo_url']:
                update_data['before_photo_url'] = data['before_photo_url']
            if 'after_photo_url' in data and data['after_photo_url']:
                update_data['after_photo_url'] = data['after_photo_url']
            if 'customer_signature_url' in data and data['customer_signature_url']:
                update_data['customer_signature_url'] = data['customer_signature_url']

            if not update_data:
                return self.get_report(report_id)

            updated = self.db.table('jobs_service_reports').update(update_data).eq('id', report_id).execute()

            logger.info(f"Updated service report {report_id} with photos/signature")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error updating report photos: {e}")
            raise

    def add_customer_rating(self, report_id: str, rating: int) -> Optional[Dict[str, Any]]:
        """Add customer rating to service report."""
        try:
            # Verify rating is valid
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be between 1 and 5")

            updated = self.db.table('jobs_service_reports').update({
                'rating_by_customer': rating
            }).eq('id', report_id).execute()

            logger.info(f"Added rating {rating} to service report {report_id}")
            return updated.data[0] if updated.data else None

        except Exception as e:
            logger.error(f"Error adding customer rating: {e}")
            raise

    def list_engineer_reports(self, engineer_id: str) -> List[Dict[str, Any]]:
        """List all service reports for an engineer."""
        try:
            response = self.db.table('jobs_service_reports').select('*').eq(
                'engineer_id', engineer_id
            ).order('created_at', desc=True).execute()

            return response.data or []

        except Exception as e:
            logger.error(f"Error listing engineer reports: {e}")
            return []

    def get_report_statistics(self, engineer_id: str) -> Dict[str, Any]:
        """Get statistics for an engineer's service reports."""
        try:
            reports = self.list_engineer_reports(engineer_id)

            total_reports = len(reports)
            total_time = sum(r.get('resolution_time_minutes', 0) for r in reports)
            avg_time = total_time / total_reports if total_reports > 0 else 0

            ratings = [r.get('rating_by_customer') for r in reports if r.get('rating_by_customer')]
            avg_rating = sum(ratings) / len(ratings) if ratings else 0

            return {
                'total_reports': total_reports,
                'total_resolution_time_minutes': total_time,
                'average_resolution_time_minutes': round(avg_time, 1),
                'average_customer_rating': round(avg_rating, 1),
                'rated_reports': len(ratings)
            }

        except Exception as e:
            logger.error(f"Error calculating report statistics: {e}")
            return {}
