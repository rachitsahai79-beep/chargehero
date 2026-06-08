"""Tests for service report service."""

import pytest
from unittest.mock import MagicMock, patch
from domains.jobs.service_report_service import ServiceReportService


@pytest.fixture
def mock_db():
    """Mock database client."""
    return MagicMock()


@pytest.fixture
def service_report_service(mock_db):
    """Create ServiceReportService."""
    return ServiceReportService(mock_db)


class TestServiceReportCreation:
    """Test service report creation."""

    def test_create_report_success(self, service_report_service, mock_db):
        """Successfully create a service report."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'ticket_id': 'ticket-1',
            'engineer_id': 'engineer-1',
            'work_description': 'Fixed voltage regulator'
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'work_description': 'Fixed voltage regulator',
            'spare_parts_used': ['Voltage Regulator'],
            'resolution_time_minutes': 45
        }

        result = service_report_service.create_report('ticket-1', 'engineer-1', data)
        assert result is not None
        assert result['ticket_id'] == 'ticket-1'

    def test_get_report_success(self, service_report_service, mock_db):
        """Get service report by ID."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'ticket_id': 'ticket-1',
            'engineer_id': 'engineer-1'
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = service_report_service.get_report('report-1')
        assert result is not None
        assert result['id'] == 'report-1'

    def test_get_report_not_found(self, service_report_service, mock_db):
        """Return None if report not found."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = service_report_service.get_report('nonexistent')
        assert result is None


class TestServiceReportPhotos:
    """Test service report photo uploads."""

    @patch('domains.jobs.service_report_service.FileUploadService')
    def test_get_photo_upload_url(self, mock_file_service_class, service_report_service, mock_db):
        """Get presigned URL for photo upload."""
        # Mock FileUploadService
        mock_file_service = MagicMock()
        mock_file_service.get_presigned_url_for_photo.return_value = {
            'presigned_url': 'https://s3.example.com/presigned-url',
            'file_path': 'tickets/ticket-1/photos/before_abc123.jpg'
        }
        mock_file_service_class.return_value = mock_file_service

        # Mock get_report
        mock_report_response = MagicMock()
        mock_report_response.data = [{'id': 'report-1', 'ticket_id': 'ticket-1'}]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_report_response

        result = service_report_service.get_photo_upload_url('report-1', 'before')

        assert result is not None
        assert 'presigned_url' in result
        assert result['photo_type'] == 'before'

    @patch('domains.jobs.service_report_service.FileUploadService')
    def test_get_signature_upload_url(self, mock_file_service_class, service_report_service, mock_db):
        """Get presigned URL for signature upload."""
        # Mock FileUploadService
        mock_file_service = MagicMock()
        mock_file_service.get_presigned_url_for_signature.return_value = {
            'presigned_url': 'https://s3.example.com/presigned-signature',
            'file_path': 'tickets/ticket-1/signatures/engineer-1_xyz789.png'
        }
        mock_file_service_class.return_value = mock_file_service

        # Mock get_report
        mock_report_response = MagicMock()
        mock_report_response.data = [{'id': 'report-1', 'ticket_id': 'ticket-1'}]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_report_response

        result = service_report_service.get_signature_upload_url('report-1', 'engineer-1')

        assert result is not None
        assert 'presigned_url' in result


class TestServiceReportUpdate:
    """Test service report updates."""

    def test_update_report_photos(self, service_report_service, mock_db):
        """Update report with photo URLs."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'before_photo_url': 'https://s3.example.com/before.jpg',
            'after_photo_url': 'https://s3.example.com/after.jpg'
        }]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        data = {
            'before_photo_url': 'https://s3.example.com/before.jpg',
            'after_photo_url': 'https://s3.example.com/after.jpg'
        }

        result = service_report_service.update_report_photos('report-1', data)

        assert result is not None
        assert result['before_photo_url'] == 'https://s3.example.com/before.jpg'

    def test_add_customer_rating(self, service_report_service, mock_db):
        """Add customer rating to report."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'rating_by_customer': 5
        }]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = service_report_service.add_customer_rating('report-1', 5)

        assert result is not None
        assert result['rating_by_customer'] == 5


class TestServiceReportStatistics:
    """Test service report statistics."""

    def test_list_engineer_reports(self, service_report_service, mock_db):
        """List all reports for an engineer."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'report-1', 'engineer_id': 'engineer-1', 'resolution_time_minutes': 45},
            {'id': 'report-2', 'engineer_id': 'engineer-1', 'resolution_time_minutes': 60}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        result = service_report_service.list_engineer_reports('engineer-1')

        assert len(result) == 2
        assert result[0]['engineer_id'] == 'engineer-1'

    def test_get_report_statistics(self, service_report_service, mock_db):
        """Calculate engineer report statistics."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                'id': 'report-1',
                'engineer_id': 'engineer-1',
                'resolution_time_minutes': 45,
                'rating_by_customer': 5
            },
            {
                'id': 'report-2',
                'engineer_id': 'engineer-1',
                'resolution_time_minutes': 60,
                'rating_by_customer': 4
            }
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_response

        result = service_report_service.get_report_statistics('engineer-1')

        assert result['total_reports'] == 2
        assert result['total_resolution_time_minutes'] == 105
        assert result['average_resolution_time_minutes'] == 52.5
        assert result['average_customer_rating'] == 4.5
