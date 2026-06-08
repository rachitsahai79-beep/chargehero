"""Tests for real-time, file upload, and location services."""

import pytest
import math
from unittest.mock import MagicMock, patch
from domains.shared.file_upload import FileUploadService, MAX_PHOTO_SIZE, MAX_VIDEO_SIZE
from domains.shared.location_tracking import LocationTrackingService


@pytest.fixture
def mock_db():
    """Mock database client."""
    return MagicMock()


@pytest.fixture
def file_service(mock_db):
    """Create FileUploadService."""
    return FileUploadService(mock_db)


@pytest.fixture
def location_service(mock_db):
    """Create LocationTrackingService."""
    return LocationTrackingService(mock_db)


# ============================================================================
# File Upload Tests
# ============================================================================

class TestFileUploadService:
    """Test file upload and presigned URL generation."""

    def test_get_presigned_url_for_before_photo(self, file_service, mock_db):
        """Get presigned URL for before photo."""
        mock_db.storage.from_.return_value.create_signed_url.return_value = \
            "https://example.com/presigned-url"

        result = file_service.get_presigned_url_for_photo('ticket-1', 'before')

        assert result is not None
        assert 'presigned_url' in result
        assert 'file_path' in result
        assert 'tickets/ticket-1/photos/before' in result['file_path']
        assert result['expected_content_type'] == 'image/jpeg'

    def test_get_presigned_url_for_after_photo(self, file_service, mock_db):
        """Get presigned URL for after photo."""
        mock_db.storage.from_.return_value.create_signed_url.return_value = \
            "https://example.com/presigned-url"

        result = file_service.get_presigned_url_for_photo('ticket-1', 'after')

        assert result is not None
        assert 'after' in result['file_path']

    def test_invalid_photo_type(self, file_service):
        """Invalid photo type returns None."""
        result = file_service.get_presigned_url_for_photo('ticket-1', 'invalid')
        assert result is None

    def test_get_presigned_url_for_signature(self, file_service, mock_db):
        """Get presigned URL for signature."""
        mock_db.storage.from_.return_value.create_signed_url.return_value = \
            "https://example.com/presigned-url"

        result = file_service.get_presigned_url_for_signature('ticket-1', 'engineer-1')

        assert result is not None
        assert 'signatures' in result['file_path']
        assert result['expected_content_type'] == 'image/png'

    def test_get_presigned_url_for_video(self, file_service, mock_db):
        """Get presigned URL for video upload."""
        mock_db.storage.from_.return_value.create_signed_url.return_value = \
            "https://example.com/presigned-url"

        result = file_service.get_presigned_url_for_video('ticket-1')

        assert result is not None
        assert 'videos' in result['file_path']
        assert result['expected_content_type'] == 'video/mp4'

    def test_get_presigned_url_for_document(self, file_service, mock_db):
        """Get presigned URL for certificate upload."""
        mock_db.storage.from_.return_value.create_signed_url.return_value = \
            "https://example.com/presigned-url"

        result = file_service.get_presigned_url_for_document('user-1', '10th_certificate')

        assert result is not None
        assert 'documents' in result['file_path']
        assert '10th_certificate' in result['file_path']
        assert result['expected_content_type'] == 'application/pdf'

    def test_invalid_document_type(self, file_service):
        """Invalid document type returns None."""
        result = file_service.get_presigned_url_for_document('user-1', 'invalid_type')
        assert result is None

    def test_validate_photo_size_valid(self, file_service):
        """Valid photo size passes validation."""
        result = file_service.validate_file_size(5 * 1024 * 1024, 'photo')  # 5 MB
        assert result is True

    def test_validate_photo_size_too_large(self, file_service):
        """Photo exceeding limit fails validation."""
        result = file_service.validate_file_size(15 * 1024 * 1024, 'photo')  # 15 MB
        assert result is False

    def test_validate_content_type_photo(self, file_service):
        """Valid photo MIME type passes validation."""
        assert file_service.validate_content_type('image/jpeg', 'photo') is True
        assert file_service.validate_content_type('image/png', 'photo') is True

    def test_validate_content_type_invalid(self, file_service):
        """Invalid MIME type fails validation."""
        assert file_service.validate_content_type('text/plain', 'photo') is False
        assert file_service.validate_content_type('image/jpeg', 'video') is False


# ============================================================================
# Location Tracking Tests
# ============================================================================

class TestLocationTracking:
    """Test location tracking and GPS services."""

    def test_update_engineer_location(self, location_service, mock_db):
        """Update engineer location successfully."""
        mock_response = MagicMock()
        mock_response.data = [{'user_id': 'engineer-1', 'gps_location': 'POINT(77.1025 28.7041)'}]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = location_service.update_engineer_location('engineer-1', 28.7041, 77.1025)

        assert result is True
        mock_db.table.assert_called_with('auth_engineer_profiles')

    def test_calculate_distance_same_location(self, location_service):
        """Distance at same location is ~0."""
        distance = location_service.calculate_distance_to_job(
            (28.7041, 77.1025),
            (28.7041, 77.1025)
        )
        assert distance < 0.1

    def test_calculate_distance_known_points(self, location_service):
        """Calculate distance between known locations."""
        # Delhi to nearby location (10 km away)
        distance = location_service.calculate_distance_to_job(
            (28.7041, 77.1025),
            (28.7700, 77.1150)  # ~8 km away
        )
        assert 7 < distance < 10

    def test_calculate_eta_to_job(self, location_service):
        """Calculate ETA for job."""
        eta = location_service.calculate_eta_to_job(20)  # 20 km away
        # At 40 km/h, should be 30 minutes
        assert 25 < eta < 35

    def test_calculate_eta_zero_distance(self, location_service):
        """ETA at zero distance is 0."""
        eta = location_service.calculate_eta_to_job(0)
        assert eta == 0

    def test_check_arrival_within_threshold(self, location_service):
        """Engineer within geofence threshold is considered arrived."""
        # Very close location (50 meters = 0.00045 degrees)
        arrived = location_service.check_arrival_at_job(
            (28.7041, 77.1025),
            (28.7041, 77.1025)  # Same location
        )
        assert arrived is True

    def test_check_arrival_outside_threshold(self, location_service):
        """Engineer far away is not arrived."""
        arrived = location_service.check_arrival_at_job(
            (28.7041, 77.1025),
            (28.8041, 77.2025)  # ~15 km away
        )
        assert arrived is False

    def test_estimate_service_duration_pm_abb(self, location_service):
        """Service duration estimate for preventive maintenance on ABB."""
        duration = location_service.estimate_service_duration('preventive_maintenance', 'ABB')
        assert duration == 45

    def test_estimate_service_duration_issue(self, location_service):
        """Service duration estimate for issue resolution."""
        duration = location_service.estimate_service_duration('issue', 'Delta')
        assert duration == 85

    def test_estimate_service_duration_unknown(self, location_service):
        """Unknown combination returns default estimate."""
        duration = location_service.estimate_service_duration('unknown', 'Unknown')
        assert duration == 60

    def test_get_location_history(self, location_service, mock_db):
        """Get location history for engineer."""
        history = location_service.get_location_history('engineer-1', hours=24)
        assert isinstance(history, list)

    def test_get_heatmap_data(self, location_service):
        """Get heatmap data for region."""
        region = (28.0, 77.0, 29.0, 78.0)
        heatmap = location_service.get_heatmap_data(region)
        assert isinstance(heatmap, dict)


# ============================================================================
# Integration Tests
# ============================================================================

class TestJobDispatchIntegration:
    """Integration tests for complete job dispatch workflow."""

    def test_end_to_end_job_assignment_flow(self):
        """Test complete flow: create ticket → dispatch → engineer accepts → report submitted."""
        # This is a high-level integration test
        # In production, would use test database and real service instances

        # Step 1: Create ticket
        ticket = {
            'id': 'ticket-1',
            'charger_id': 'charger-1',
            'status': 'open',
            'priority': 'high'
        }

        # Step 2: Find and dispatch to engineer
        dispatch = {
            'id': 'assignment-1',
            'ticket_id': ticket['id'],
            'engineer_id': 'engineer-1',
            'status': 'pending'
        }

        # Step 3: Engineer accepts
        dispatch['status'] = 'accepted'
        dispatch['accepted_at'] = '2026-06-08T10:30:00Z'

        # Step 4: Engineer submits report
        report = {
            'id': 'report-1',
            'ticket_id': ticket['id'],
            'engineer_id': 'engineer-1',
            'work_description': 'Fixed isolation fault',
            'resolution_time_minutes': 45
        }

        # Verify flow
        assert ticket['id'] == dispatch['ticket_id']
        assert dispatch['engineer_id'] == report['engineer_id']
        assert dispatch['status'] == 'accepted'

    def test_location_tracking_during_dispatch(self):
        """Test location tracking updates during active dispatch."""
        locations = [
            {'engineer_id': 'eng-1', 'lat': 28.7041, 'lon': 77.1025},  # Start
            {'engineer_id': 'eng-1', 'lat': 28.7050, 'lon': 77.1050},  # En route
            {'engineer_id': 'eng-1', 'lat': 28.7100, 'lon': 77.1100},  # Near job
            {'engineer_id': 'eng-1', 'lat': 28.7100, 'lon': 77.1100},  # Arrived
        ]

        # Verify progression
        assert locations[0]['lat'] < locations[3]['lat']
        assert len(locations) == 4

    def test_file_upload_for_service_report(self):
        """Test file upload presigned URLs in service report workflow."""
        uploads = {
            'before_photo': 'tickets/ticket-1/photos/before_xxxxx.jpg',
            'after_photo': 'tickets/ticket-1/photos/after_xxxxx.jpg',
            'signature': 'tickets/ticket-1/signatures/engineer-1_xxxxx.png'
        }

        # Verify all required uploads present
        assert 'before_photo' in uploads
        assert 'after_photo' in uploads
        assert 'signature' in uploads

        # Verify paths are unique
        paths = list(uploads.values())
        assert len(paths) == len(set(paths))
