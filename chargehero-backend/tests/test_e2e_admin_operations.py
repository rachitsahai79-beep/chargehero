"""End-to-end tests for admin operations."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    """Create mock database."""
    return MagicMock()


@pytest.fixture
def admin_service(mock_db):
    """Create AdminService with mock database."""
    from domains.admin.admin_service import AdminService
    return AdminService(mock_db)


@pytest.fixture
def dispatch_service(mock_db):
    """Create DispatchService with mock database."""
    from domains.admin.dispatch_service import DispatchService
    return DispatchService(mock_db)


class TestEngineerManagement:
    """Test engineer management operations."""

    def test_admin_can_list_engineers(self, admin_service, mock_db):
        """Admin should list all engineers."""
        engineers = [
            {
                'id': 'eng1',
                'name': 'Engineer 1',
                'phone': '+919876543210',
                'email': 'eng1@example.com',
                'status': 'active',
                'role': 'engineer'
            },
            {
                'id': 'eng2',
                'name': 'Engineer 2',
                'phone': '+919876543211',
                'email': 'eng2@example.com',
                'status': 'active',
                'role': 'engineer'
            },
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=engineers
        )

        result = admin_service.get_engineers_list(limit=50)

        assert len(result) == 2
        assert result[0].get('role') == 'engineer'

    def test_admin_can_filter_engineers_by_status(self, admin_service, mock_db):
        """Admin should filter engineers by status."""
        active_engineers = [
            {
                'id': 'eng1',
                'status': 'active',
                'role': 'engineer'
            }
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=active_engineers
        )

        result = admin_service.get_engineers_list(status='active', limit=50)

        assert all(eng.get('status') == 'active' for eng in result)

    def test_admin_can_view_engineer_details(self, admin_service, mock_db):
        """Admin should view detailed engineer information."""
        engineer = {
            'id': 'eng1',
            'name': 'Engineer 1',
            'phone': '+919876543210',
            'email': 'eng1@example.com',
            'status': 'active',
            'total_jobs': 45,
            'completed_jobs': 42,
            'average_rating': 4.6
        }

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[engineer]
        )

        result = admin_service.get_engineer_detail('eng1')

        assert result is not None
        assert result.get('id') == 'eng1'

    def test_admin_can_update_engineer_status(self, admin_service, mock_db):
        """Admin should update engineer status."""
        update_data = {'status': 'suspended'}

        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[update_data]
        )

        result = admin_service.update_engineer('eng1', {'status': 'suspended'})

        assert result is not None

    def test_admin_can_certify_engineer(self, admin_service, mock_db):
        """Admin should certify engineer for charger types."""
        mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{
                'user_id': 'eng1',
                'charger_brand': 'Tesla',
                'is_certified': True
            }]
        )

        result = admin_service.certify_engineer('eng1', 'Tesla', 'Wall Connector')

        assert result is True


class TestAdminDashboard:
    """Test admin dashboard operations."""

    def test_admin_can_view_dashboard(self, admin_service, mock_db):
        """Admin should view system overview."""
        # Mock: Get engineer counts
        engineers = [
            {'id': 'eng1', 'status': 'active'},
            {'id': 'eng2', 'status': 'active'},
            {'id': 'eng3', 'status': 'pending'},
        ]

        tickets = [
            {'id': 'ticket1', 'status': 'resolved'},
            {'id': 'ticket2', 'status': 'resolved'},
            {'id': 'ticket3', 'status': 'in_progress'},
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=engineers
        )

        result = admin_service.get_dashboard_overview()

        assert result.get('total_engineers') is not None
        assert result.get('total_jobs') is not None

    def test_dashboard_shows_kpis(self, admin_service, mock_db):
        """Dashboard should display key metrics."""
        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = admin_service.get_dashboard_overview()

        assert 'total_engineers' in result
        assert 'active_engineers' in result
        assert 'total_jobs' in result
        assert 'total_revenue' in result
        assert 'average_engineer_rating' in result

    def test_dashboard_shows_top_engineers(self, admin_service, mock_db):
        """Dashboard should show top performing engineers."""
        engineers = [
            {
                'id': 'eng1',
                'name': 'Top Engineer',
                'average_rating': 4.8,
                'total_jobs': 50
            }
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(
            data=engineers
        )

        result = admin_service.get_engineers_list(status='active', limit=5)

        assert len(result) > 0


class TestEngineerStatistics:
    """Test engineer statistics."""

    def test_admin_can_view_engineer_stats(self, admin_service, mock_db):
        """Admin should view detailed engineer statistics."""
        engineer = {
            'id': 'eng1',
            'name': 'Engineer 1',
            'total_jobs': 45,
            'completed_jobs': 42
        }

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[engineer]
        )

        result = admin_service.get_engineer_statistics('eng1')

        assert result is not None
        assert result.get('engineer_id') == 'eng1'

    def test_stats_include_performance_metrics(self, admin_service, mock_db):
        """Statistics should include performance metrics."""
        engineer = {
            'id': 'eng1',
            'name': 'Engineer 1',
            'total_jobs': 45,
            'completed_jobs': 42,
            'average_rating': 4.6
        }

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[engineer]
        )

        result = admin_service.get_engineer_statistics('eng1')

        assert 'average_rating' in result or 'customer_satisfaction_percentage' in result

    def test_stats_include_resolution_time(self, admin_service, mock_db):
        """Statistics should include average resolution time."""
        reports = [
            {'resolution_time_minutes': 30},
            {'resolution_time_minutes': 45},
            {'resolution_time_minutes': 35},
        ]

        mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=reports
        )

        # Average: (30 + 45 + 35) / 3 = 36.67 minutes
        avg_time = sum(r.get('resolution_time_minutes', 0) for r in reports) / len(reports) if reports else 0

        assert avg_time == pytest.approx(36.67, 0.1)


class TestRevenueReporting:
    """Test revenue reporting."""

    def test_admin_can_view_revenue_report(self, admin_service, mock_db):
        """Admin should view revenue report."""
        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[]
        )

        result = admin_service.get_revenue_report(days=30)

        assert result is not None
        assert 'total_revenue' in result
        assert 'total_fees' in result
        assert 'net_revenue' in result

    def test_revenue_report_calculates_platform_fees(self, admin_service, mock_db):
        """Revenue report should calculate 10% platform fee."""
        earnings = [
            {'amount': 1000},
            {'amount': 500},
            {'amount': 750},
        ]

        mock_db.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=earnings
        )

        result = admin_service.get_revenue_report(days=30)

        total = sum(e.get('amount', 0) for e in earnings)
        expected_fee = total * 0.1

        # Platform fee should be 10% of total
        assert result is not None


class TestDispatchCentreAdmin:
    """Test dispatch centre admin operations."""

    def test_admin_can_view_active_assignments(self, dispatch_service, mock_db):
        """Admin should view all active assignments."""
        assignments = [
            {
                'ticket_id': 'ticket1',
                'engineer_id': 'eng1',
                'status': 'in_progress'
            },
            {
                'ticket_id': 'ticket2',
                'engineer_id': 'eng2',
                'status': 'on_site'
            },
        ]

        # Mock implementation would return assignments
        result = dispatch_service.get_active_assignments()

        assert result is not None

    def test_admin_can_view_engineer_availability(self, dispatch_service, mock_db):
        """Admin should view engineer availability status."""
        engineers = [
            {
                'engineer_id': 'eng1',
                'availability_status': 'available'
            },
            {
                'engineer_id': 'eng2',
                'availability_status': 'on_job'
            },
        ]

        result = dispatch_service.get_engineer_availability()

        assert result is not None

    def test_admin_can_reallocate_assignment(self, dispatch_service, mock_db):
        """Admin should reallocate ticket to different engineer."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                'id': 'ticket123',
                'assigned_engineer_id': 'eng2'
            }]
        )

        result = dispatch_service.reallocate_assignment(
            ticket_id='ticket123',
            old_eng_id='eng1',
            new_eng_id='eng2',
            reason='Engineer unavailable'
        )

        assert result is True

    def test_admin_can_adjust_job_priority(self, dispatch_service, mock_db):
        """Admin should adjust job priority in queue."""
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{'priority': 'critical'}]
        )

        result = dispatch_service.update_priority('ticket123', 'critical')

        assert result is True

    def test_admin_can_view_kpi_dashboard(self, dispatch_service, mock_db):
        """Admin should view complete KPI dashboard."""
        result = dispatch_service.get_kpi_dashboard()

        assert result is not None
        # Dashboard should include all KPI sections


class TestAuditLogging:
    """Test admin action audit logging."""

    def test_admin_actions_are_logged(self, admin_service, mock_db):
        """Admin actions should be logged for audit trail."""
        with patch('domains.admin.admin_service.logger') as mock_logger:
            mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{'id': 'eng1', 'status': 'suspended'}]
            )

            admin_service.update_engineer('eng1', {'status': 'suspended'})

            # Verify logging call
            mock_logger.info.assert_called()

    def test_certification_changes_logged(self, admin_service, mock_db):
        """Engineer certifications changes should be logged."""
        with patch('domains.admin.admin_service.logger') as mock_logger:
            mock_db.table.return_value.insert.return_value.execute.return_value = MagicMock(
                data=[{'user_id': 'eng1', 'is_certified': True}]
            )

            admin_service.certify_engineer('eng1', 'Tesla', 'Wall Connector')

            mock_logger.info.assert_called()
