"""Tests for jobs domain - chargers, tickets, dispatch, service reports."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from domains.jobs.service import JobsService
from domains.jobs.models import (
    TicketType, Priority, TicketStatus,
    ChargerRequest, TicketRequest
)


@pytest.fixture
def mock_db():
    """Create mock database instance."""
    return MagicMock()


@pytest.fixture
def jobs_service(mock_db):
    """Create JobsService with mock DB."""
    return JobsService(mock_db)


# ============================================================================
# Charger Tests
# ============================================================================

class TestChargerCreation:
    """Test charger creation functionality."""

    def test_create_charger_success(self, jobs_service, mock_db):
        """Successfully create a charger."""
        # Mock database response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'charger-1',
            'customer_id': 'customer-1',
            'serial_number': 'ABB-12345',
            'model': '22kW',
            'brand': 'ABB',
            'address': '123 Main St',
            'status': 'active'
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'serial_number': 'ABB-12345',
            'model': '22kW',
            'brand': 'ABB',
            'address': '123 Main St',
            'latitude': 28.7041,
            'longitude': 77.1025,
            'status': 'active'
        }

        result = jobs_service.create_charger('customer-1', data)

        assert result['id'] == 'charger-1'
        assert result['serial_number'] == 'ABB-12345'
        assert result['status'] == 'active'

    def test_create_charger_failure(self, jobs_service, mock_db):
        """Handle charger creation failure."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'serial_number': 'ABB-12345',
            'model': '22kW',
            'brand': 'ABB',
            'address': '123 Main St',
            'latitude': 28.7041,
            'longitude': 77.1025
        }

        with pytest.raises(Exception):
            jobs_service.create_charger('customer-1', data)


class TestChargerRetrieval:
    """Test charger retrieval functionality."""

    def test_get_charger_success(self, jobs_service, mock_db):
        """Successfully retrieve a charger."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'charger-1',
            'customer_id': 'customer-1',
            'serial_number': 'ABB-12345'
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.get_charger('charger-1')

        assert result is not None
        assert result['id'] == 'charger-1'

    def test_get_charger_not_found(self, jobs_service, mock_db):
        """Handle charger not found."""
        mock_response = MagicMock()
        mock_response.data = []
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.get_charger('nonexistent')

        assert result is None


# ============================================================================
# Ticket Tests
# ============================================================================

class TestTicketCreation:
    """Test ticket creation functionality."""

    def test_create_ticket_success(self, jobs_service, mock_db):
        """Successfully create a ticket."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'ticket-1',
            'charger_id': 'charger-1',
            'customer_id': 'customer-1',
            'ticket_type': 'preventive_maintenance',
            'description': 'Routine maintenance',
            'priority': 'medium',
            'status': 'open',
            'sla_minutes': 240
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'ticket_type': 'preventive_maintenance',
            'description': 'Routine maintenance',
            'priority': 'medium'
        }

        result = jobs_service.create_ticket('charger-1', 'customer-1', data)

        assert result['id'] == 'ticket-1'
        assert result['status'] == 'open'
        assert result['sla_minutes'] == 240

    def test_create_ticket_critical_priority_sla(self, jobs_service, mock_db):
        """Critical priority ticket gets 60 minute SLA."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'ticket-1',
            'priority': 'critical',
            'sla_minutes': 60
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'ticket_type': 'issue',
            'description': 'Charger not working',
            'priority': 'critical'
        }

        result = jobs_service.create_ticket('charger-1', 'customer-1', data)

        assert result['sla_minutes'] == 60

    def test_create_ticket_low_priority_sla(self, jobs_service, mock_db):
        """Low priority ticket gets 480 minute SLA."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'ticket-1',
            'priority': 'low',
            'sla_minutes': 480
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'ticket_type': 'preventive_maintenance',
            'description': 'Optional upgrade',
            'priority': 'low'
        }

        result = jobs_service.create_ticket('charger-1', 'customer-1', data)

        assert result['sla_minutes'] == 480


class TestTicketRetrieval:
    """Test ticket retrieval functionality."""

    def test_get_ticket_success(self, jobs_service, mock_db):
        """Successfully retrieve a ticket."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'ticket-1',
            'status': 'open',
            'priority': 'medium'
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.get_ticket('ticket-1')

        assert result is not None
        assert result['id'] == 'ticket-1'

    def test_list_open_tickets(self, jobs_service, mock_db):
        """List all open tickets."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'ticket-1', 'status': 'open'},
            {'id': 'ticket-2', 'status': 'open'}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.list_open_tickets()

        assert len(result) == 2
        assert all(t['status'] == 'open' for t in result)


# ============================================================================
# Dispatch Tests
# ============================================================================

class TestDispatchAssignment:
    """Test dispatch assignment functionality."""

    def test_assign_ticket_to_engineer(self, jobs_service, mock_db):
        """Successfully assign ticket to engineer."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'assignment-1',
            'ticket_id': 'ticket-1',
            'engineer_id': 'engineer-1',
            'status': 'pending',
            'dispatch_score': 85.5
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        result = jobs_service.assign_ticket_to_engineer('ticket-1', 'engineer-1', 85.5)

        assert result['id'] == 'assignment-1'
        assert result['status'] == 'pending'
        assert result['dispatch_score'] == 85.5

    def test_accept_assignment(self, jobs_service, mock_db):
        """Engineer accepts assignment."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'assignment-1',
            'ticket_id': 'ticket-1',
            'status': 'accepted',
            'accepted_at': datetime.utcnow().isoformat()
        }]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.accept_assignment('assignment-1')

        assert result is not None
        assert result['status'] == 'accepted'

    def test_reject_assignment(self, jobs_service, mock_db):
        """Engineer rejects assignment."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'assignment-1',
            'ticket_id': 'ticket-1',
            'status': 'rejected'
        }]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.reject_assignment('assignment-1')

        assert result is not None
        assert result['status'] == 'rejected'

    def test_list_engineer_assignments(self, jobs_service, mock_db):
        """List assignments for engineer."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'assignment-1', 'status': 'pending'},
            {'id': 'assignment-2', 'status': 'accepted'}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.list_engineer_assignments('engineer-1')

        assert len(result) == 2


# ============================================================================
# Service Report Tests
# ============================================================================

class TestServiceReport:
    """Test service report functionality."""

    def test_create_service_report(self, jobs_service, mock_db):
        """Successfully create service report."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'ticket_id': 'ticket-1',
            'engineer_id': 'engineer-1',
            'work_description': 'Fixed isolation fault',
            'resolution_time_minutes': 45
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        data = {
            'work_description': 'Fixed isolation fault',
            'resolution_time_minutes': 45
        }

        result = jobs_service.create_service_report('ticket-1', 'engineer-1', data)

        assert result['id'] == 'report-1'
        assert result['work_description'] == 'Fixed isolation fault'

    def test_get_ticket_service_report(self, jobs_service, mock_db):
        """Retrieve service report for ticket."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'ticket_id': 'ticket-1'
        }]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.get_ticket_service_report('ticket-1')

        assert result is not None
        assert result['id'] == 'report-1'

    def test_update_service_report_with_files(self, jobs_service, mock_db):
        """Update service report with photos and signature."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'report-1',
            'before_photo_url': 'https://example.com/before.jpg',
            'after_photo_url': 'https://example.com/after.jpg',
            'customer_signature_url': 'https://example.com/signature.png'
        }]
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.update_service_report_with_files(
            'report-1',
            before_photo='https://example.com/before.jpg',
            after_photo='https://example.com/after.jpg',
            signature='https://example.com/signature.png'
        )

        assert result is not None
        assert result['before_photo_url'] == 'https://example.com/before.jpg'


# ============================================================================
# Earnings Tests
# ============================================================================

class TestEarnings:
    """Test earnings functionality."""

    def test_create_earnings_record(self, jobs_service, mock_db):
        """Create earnings record for engineer."""
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'earning-1',
            'engineer_id': 'engineer-1',
            'ticket_id': 'ticket-1',
            'amount': 500.0,
            'status': 'pending'
        }]
        mock_db.table.return_value.insert.return_value.execute.return_value = mock_response

        result = jobs_service.create_earnings_record('engineer-1', 'ticket-1', 500.0)

        assert result['id'] == 'earning-1'
        assert result['amount'] == 500.0
        assert result['status'] == 'pending'

    def test_get_engineer_earnings_summary(self, jobs_service, mock_db):
        """Get engineer earnings summary."""
        mock_response = MagicMock()
        mock_response.data = [
            {'amount': 500.0, 'status': 'pending'},
            {'amount': 300.0, 'status': 'paid'},
            {'amount': 200.0, 'status': 'paid'}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.get_engineer_earnings('engineer-1')

        assert result['total_earned'] == 1000.0
        assert result['total_paid'] == 500.0
        assert result['pending_amount'] == 500.0
        assert result['completed_jobs'] == 2

    def test_list_engineer_earnings(self, jobs_service, mock_db):
        """List earnings records for engineer."""
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'earning-1', 'amount': 500.0},
            {'id': 'earning-2', 'amount': 300.0}
        ]
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

        result = jobs_service.list_engineer_earnings('engineer-1')

        assert len(result) == 2
        assert sum(e['amount'] for e in result) == 800.0


# ============================================================================
# Model Validation Tests
# ============================================================================

class TestChargerRequestValidation:
    """Test ChargerRequest model validation."""

    def test_valid_charger_request(self):
        """Valid charger request."""
        request = ChargerRequest(
            serial_number='ABB-12345',
            model='22kW',
            brand='ABB',
            address='123 Main St',
            latitude=28.7041,
            longitude=77.1025
        )
        assert request.serial_number == 'ABB-12345'
        assert request.latitude == 28.7041

    def test_invalid_latitude(self):
        """Invalid latitude outside range."""
        with pytest.raises(ValueError):
            ChargerRequest(
                serial_number='ABB-12345',
                model='22kW',
                brand='ABB',
                address='123 Main St',
                latitude=100.0,  # Invalid: > 90
                longitude=77.1025
            )

    def test_invalid_longitude(self):
        """Invalid longitude outside range."""
        with pytest.raises(ValueError):
            ChargerRequest(
                serial_number='ABB-12345',
                model='22kW',
                brand='ABB',
                address='123 Main St',
                latitude=28.7041,
                longitude=200.0  # Invalid: > 180
            )


class TestTicketRequestValidation:
    """Test TicketRequest model validation."""

    def test_valid_ticket_request(self):
        """Valid ticket request."""
        request = TicketRequest(
            charger_id='charger-1',
            ticket_type=TicketType.PREVENTIVE_MAINTENANCE,
            description='Routine maintenance'
        )
        assert request.ticket_type == TicketType.PREVENTIVE_MAINTENANCE

    def test_empty_description(self):
        """Empty description validation."""
        with pytest.raises(ValueError):
            TicketRequest(
                charger_id='charger-1',
                ticket_type=TicketType.ISSUE,
                description=''
            )

    def test_description_too_long(self):
        """Description exceeds max length."""
        with pytest.raises(ValueError):
            TicketRequest(
                charger_id='charger-1',
                ticket_type=TicketType.ISSUE,
                description='x' * 1001
            )
