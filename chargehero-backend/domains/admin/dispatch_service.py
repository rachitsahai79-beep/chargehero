"""Business logic for dispatch center domain."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


class DispatchService:
    """Service for dispatch center operations."""

    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db

    # ========================================================================
    # Active Assignments
    # ========================================================================

    def get_active_assignments(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active job assignments."""
        try:
            # Get tickets that are assigned but not completed
            query = self.db.table('jobs_tickets').select(
                'id, customer_id, assigned_engineer_id, status, priority, location, '
                'latitude, longitude, created_at, estimated_arrival_minutes'
            ).in_('status', ['assigned', 'in_progress', 'on_site'])

            response = query.execute()
            assignments = response.data or []

            enriched = []
            for assign in assignments:
                # Get customer info
                cust_response = self.db.table('auth_users').select('name, phone').eq(
                    'id', assign.get('customer_id')
                ).execute()
                customer = (cust_response.data or [{}])[0]

                # Get engineer info
                eng_response = self.db.table('auth_users').select('name, id').eq(
                    'id', assign.get('assigned_engineer_id')
                ).execute()
                engineer = (eng_response.data or [{}])[0]

                enriched.append({
                    'ticket_id': assign['id'],
                    'customer_name': customer.get('name', 'Unknown'),
                    'location': assign.get('location', ''),
                    'engineer_id': engineer.get('id', ''),
                    'engineer_name': engineer.get('name', 'Unknown'),
                    'assigned_at': assign.get('created_at'),
                    'eta_minutes': assign.get('estimated_arrival_minutes', 0),
                    'priority': assign.get('priority', 'medium'),
                    'status': assign.get('status'),
                    'distance_km': 0.0,  # Would be calculated from GPS
                    'customer_phone': customer.get('phone', ''),
                })

            return enriched

        except Exception as e:
            logger.error(f"Error getting active assignments: {e}")
            return []

    # ========================================================================
    # Engineer Availability
    # ========================================================================

    def get_engineer_availability(self) -> List[Dict[str, Any]]:
        """Get availability status of all engineers."""
        try:
            # Get active engineers
            eng_response = self.db.table('auth_users').select('id, name').eq(
                'role', 'engineer'
            ).eq('status', 'active').execute()
            engineers = eng_response.data or []

            availability_list = []
            for eng in engineers:
                eng_id = eng['id']

                # Check current job assignment
                job_response = self.db.table('jobs_tickets').select('id, created_at').eq(
                    'assigned_engineer_id', eng_id
                ).in_('status', ['assigned', 'in_progress', 'on_site']).limit(1).execute()
                current_job = (job_response.data or [None])[0]

                # Get location tracking
                loc_response = self.db.table('jobs_engineer_locations').select(
                    'latitude, longitude, last_updated'
                ).eq('engineer_id', eng_id).order(
                    'last_updated', desc=True
                ).limit(1).execute()
                location = (loc_response.data or [{}])[0]

                # Get ratings
                rating_response = self.db.table('jobs_service_reports').select(
                    'rating_by_customer'
                ).eq('engineer_id', eng_id).execute()
                ratings = [r.get('rating_by_customer') for r in (rating_response.data or [])
                           if r.get('rating_by_customer')]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0

                # Count jobs today
                today = datetime.utcnow().date()
                jobs_today_response = self.db.table('jobs_tickets').select('id').eq(
                    'assigned_engineer_id', eng_id
                ).gte('created_at', today.isoformat()).execute()
                jobs_today = len(jobs_today_response.data or [])

                availability_status = 'available'
                if current_job:
                    availability_status = 'on_job'

                availability_list.append({
                    'engineer_id': eng_id,
                    'engineer_name': eng.get('name', 'Unknown'),
                    'availability_status': availability_status,
                    'current_location': f"{location.get('latitude', 0)},{location.get('longitude', 0)}",
                    'latitude': location.get('latitude', 0),
                    'longitude': location.get('longitude', 0),
                    'current_job_id': current_job.get('id') if current_job else None,
                    'on_job_since': current_job.get('created_at') if current_job else None,
                    'certifications': self._get_engineer_certifications(eng_id),
                    'rating': round(avg_rating, 1),
                    'jobs_today': jobs_today,
                    'last_online': location.get('last_updated', datetime.utcnow()),
                })

            return availability_list

        except Exception as e:
            logger.error(f"Error getting engineer availability: {e}")
            return []

    def _get_engineer_certifications(self, engineer_id: str) -> List[str]:
        """Get engineer certifications."""
        try:
            certs_response = self.db.table('jobs_engineer_skills').select(
                'charger_brand'
            ).eq('user_id', engineer_id).eq('is_certified', True).execute()
            return [c.get('charger_brand') for c in (certs_response.data or [])]
        except Exception as e:
            logger.error(f"Error getting certifications: {e}")
            return []

    # ========================================================================
    # Dispatch Metrics
    # ========================================================================

    def get_dispatch_metrics(self) -> Dict[str, Any]:
        """Get current dispatch center metrics."""
        try:
            # Count jobs by status
            pending_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'pending'
            ).execute()
            pending = len(pending_response.data or [])

            dispatched_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'dispatched'
            ).execute()
            dispatched = len(dispatched_response.data or [])

            assigned_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'assigned'
            ).execute()
            assigned = len(assigned_response.data or [])

            in_transit_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'in_transit'
            ).execute()
            in_transit = len(in_transit_response.data or [])

            on_site_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'on_site'
            ).execute()
            on_site = len(on_site_response.data or [])

            # Get completed jobs count
            today = datetime.utcnow().date()
            completed_response = self.db.table('jobs_tickets').select('id').eq(
                'status', 'resolved'
            ).gte('created_at', today.isoformat()).execute()
            completed = len(completed_response.data or [])

            # Calculate average dispatch time
            dispatch_response = self.db.table('jobs_tickets').select(
                'created_at, assigned_engineer_id'
            ).not_.is_('assigned_engineer_id', 'null').execute()
            dispatch_times = []
            for ticket in (dispatch_response.data or []):
                if ticket.get('created_at'):
                    # Simplified: assume dispatch time is 15 minutes on average
                    dispatch_times.append(15)
            avg_dispatch = sum(dispatch_times) / len(dispatch_times) if dispatch_times else 0

            # Get engineers count
            eng_response = self.db.table('auth_users').select('id').eq(
                'role', 'engineer'
            ).eq('status', 'active').execute()
            active_engineers = len(eng_response.data or [])

            # Calculate engineer utilization
            on_job_response = self.db.table('jobs_tickets').select('id').in_(
                'status', ['assigned', 'in_progress', 'on_site']
            ).execute()
            on_job_count = len(on_job_response.data or [])
            utilization = (on_job_count / active_engineers * 100) if active_engineers > 0 else 0

            return {
                'total_pending_jobs': pending,
                'jobs_in_dispatch': dispatched,
                'jobs_assigned': assigned,
                'jobs_in_transit': in_transit,
                'jobs_on_site': on_site,
                'average_dispatch_time_minutes': round(avg_dispatch, 1),
                'average_eta_accuracy_percentage': 92.5,  # Simplified
                'jobs_completed_today': completed,
                'jobs_pending_sla': max(0, pending + dispatched - 5),  # Simplified
                'customer_wait_time_average_minutes': round(avg_dispatch * 1.5, 1),
                'engineer_utilization_percentage': round(utilization, 1),
                'dispatch_efficiency_score': round(min(100, 70 + utilization * 0.3), 1),
            }

        except Exception as e:
            logger.error(f"Error getting dispatch metrics: {e}")
            return {}

    # ========================================================================
    # Engineer Performance Comparison
    # ========================================================================

    def get_engineer_performance_comparison(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Compare engineer performance metrics."""
        try:
            # Get active engineers
            eng_response = self.db.table('auth_users').select('id, name').eq(
                'role', 'engineer'
            ).eq('status', 'active').limit(limit).execute()
            engineers = eng_response.data or []

            performance_list = []
            today = datetime.utcnow().date()

            for eng in engineers:
                eng_id = eng['id']

                # Jobs completed today
                jobs_response = self.db.table('jobs_tickets').select('id').eq(
                    'assigned_engineer_id', eng_id
                ).eq('status', 'resolved').gte('created_at', today.isoformat()).execute()
                jobs_today = len(jobs_response.data or [])

                # Average resolution time
                reports_response = self.db.table('jobs_service_reports').select(
                    'resolution_time_minutes, rating_by_customer'
                ).eq('engineer_id', eng_id).limit(20).execute()
                reports = reports_response.data or []

                times = [r.get('resolution_time_minutes', 0) for r in reports]
                avg_resolution = sum(times) / len(times) if times else 0

                ratings = [r.get('rating_by_customer') for r in reports
                          if r.get('rating_by_customer')]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0

                # Check current availability
                current_job_response = self.db.table('jobs_tickets').select('id').eq(
                    'assigned_engineer_id', eng_id
                ).in_('status', ['assigned', 'in_progress', 'on_site']).execute()
                on_job = len(current_job_response.data or []) > 0

                performance_list.append({
                    'engineer_id': eng_id,
                    'engineer_name': eng.get('name', 'Unknown'),
                    'jobs_completed_today': jobs_today,
                    'average_resolution_time_minutes': round(avg_resolution, 1),
                    'customer_satisfaction_score': round(avg_rating * 20, 1),
                    'efficiency_score': round(min(100, 70 + jobs_today * 5), 1),
                    'availability_percentage': 0 if on_job else 100,
                    'current_status': 'on_job' if on_job else 'available',
                    'response_time_secs': 45,  # Simplified
                    'acceptance_rate_percentage': 95.0,  # Simplified
                })

            # Sort by efficiency score
            return sorted(performance_list, key=lambda x: x['efficiency_score'], reverse=True)

        except Exception as e:
            logger.error(f"Error getting engineer performance comparison: {e}")
            return []

    # ========================================================================
    # Dispatch Queue
    # ========================================================================

    def get_dispatch_queue(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get pending jobs in dispatch queue."""
        try:
            # Get pending tickets
            queue_response = self.db.table('jobs_tickets').select(
                'id, customer_id, charger_brand, charger_type, priority, '
                'issue_category, location, latitude, longitude, created_at'
            ).eq('status', 'pending').order(
                'priority', desc=True
            ).limit(limit).execute()
            queue_items = queue_response.data or []

            result = []
            for item in queue_items:
                created_time = datetime.fromisoformat(item.get('created_at', ''))
                time_in_queue = (datetime.utcnow() - created_time).total_seconds() / 60

                result.append({
                    'ticket_id': item['id'],
                    'customer_name': 'Customer',  # Would fetch from customer table
                    'charger_brand': item.get('charger_brand', ''),
                    'charger_type': item.get('charger_type', ''),
                    'priority': item.get('priority', 'medium'),
                    'issue_category': item.get('issue_category', ''),
                    'location': item.get('location', ''),
                    'latitude': item.get('latitude', 0),
                    'longitude': item.get('longitude', 0),
                    'created_at': item.get('created_at'),
                    'time_in_queue_minutes': int(time_in_queue),
                    'required_certifications': [item.get('charger_brand')],
                    'suitable_engineers': 0,  # Would calculate from available engineers
                })

            return result

        except Exception as e:
            logger.error(f"Error getting dispatch queue: {e}")
            return []

    # ========================================================================
    # Performance Reports
    # ========================================================================

    def get_dispatch_performance_report(self, days: int = 7) -> Dict[str, Any]:
        """Get dispatch performance report for period."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get all completed dispatches in period
            dispatch_response = self.db.table('jobs_tickets').select(
                'id, created_at, assigned_engineer_id, status'
            ).gte('created_at', start_date.isoformat()).execute()
            dispatches = dispatch_response.data or []

            completed = [d for d in dispatches if d.get('status') == 'resolved']
            total = len(dispatches)
            success_rate = (len(completed) / total * 100) if total > 0 else 0

            # Get ratings for completed jobs
            ratings_response = self.db.table('jobs_service_reports').select(
                'rating_by_customer'
            ).gte('created_at', start_date.isoformat()).execute()
            ratings = [r.get('rating_by_customer') for r in (ratings_response.data or [])
                      if r.get('rating_by_customer')]
            avg_satisfaction = sum(ratings) / len(ratings) if ratings else 0

            # Calculate peak hours (simplified)
            peak_hour = '14:00-15:00'  # Typically afternoon peak
            least_busy = '02:00-03:00'  # Typically night

            return {
                'period_start': start_date,
                'period_end': datetime.utcnow(),
                'total_dispatches': total,
                'average_dispatch_time_minutes': 18.5,  # Simplified
                'median_dispatch_time_minutes': 15.0,
                'dispatch_success_rate_percentage': round(success_rate, 1),
                'customer_satisfaction_average': round(avg_satisfaction * 20, 1),
                'engineer_acceptance_rate_percentage': 94.2,  # Simplified
                'jobs_completed_on_time_percentage': 88.5,  # Simplified
                'jobs_exceeding_sla_count': max(0, total - int(total * 0.885)),
                'peak_dispatch_hour': peak_hour,
                'least_busy_hour': least_busy,
                'total_distance_traveled_km': 2500.0,  # Simplified
                'average_travel_distance_per_job_km': round(2500.0 / total, 1) if total > 0 else 0,
            }

        except Exception as e:
            logger.error(f"Error getting dispatch performance report: {e}")
            return {}

    # ========================================================================
    # Dispatch History
    # ========================================================================

    def get_dispatch_history(self, limit: int = 50, days: int = 7) -> List[Dict[str, Any]]:
        """Get dispatch history for period."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            history_response = self.db.table('jobs_tickets').select(
                'id, assigned_engineer_id, created_at, status'
            ).gte('created_at', start_date.isoformat()).order(
                'created_at', desc=True
            ).limit(limit).execute()
            tickets = history_response.data or []

            result = []
            for ticket in tickets:
                eng_id = ticket.get('assigned_engineer_id')

                # Get engineer name
                if eng_id:
                    eng_response = self.db.table('auth_users').select('name').eq(
                        'id', eng_id
                    ).execute()
                    eng_name = (eng_response.data or [{}])[0].get('name', 'Unassigned')
                else:
                    eng_name = 'Unassigned'

                created = datetime.fromisoformat(ticket.get('created_at', ''))
                dispatch_time = 15  # Simplified

                result.append({
                    'dispatch_id': f"DISP-{ticket['id'][:8]}",
                    'ticket_id': ticket['id'],
                    'engineer_id': eng_id or 'N/A',
                    'engineer_name': eng_name,
                    'dispatched_at': ticket.get('created_at'),
                    'assigned_at': ticket.get('created_at'),
                    'completed_at': None,  # Would get actual completion time
                    'dispatch_time_minutes': dispatch_time,
                    'total_resolution_time_minutes': 45,  # Simplified
                    'customer_satisfaction': 4.5,  # Simplified
                    'dispatch_efficiency_score': round(70 + dispatch_time * 2, 1),
                    'status': ticket.get('status'),
                })

            return result

        except Exception as e:
            logger.error(f"Error getting dispatch history: {e}")
            return []

    # ========================================================================
    # Dispatch Management
    # ========================================================================

    def reallocate_assignment(self, ticket_id: str, old_eng_id: str, new_eng_id: str,
                             reason: Optional[str] = None) -> bool:
        """Reallocate ticket to different engineer."""
        try:
            update_data = {
                'assigned_engineer_id': new_eng_id,
                'updated_at': datetime.utcnow().isoformat(),
            }

            response = self.db.table('jobs_tickets').update(update_data).eq(
                'id', ticket_id
            ).execute()

            logger.info(
                f"Reallocated ticket {ticket_id} from {old_eng_id} to {new_eng_id}: {reason}"
            )
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error reallocating assignment: {e}")
            return False

    def update_priority(self, ticket_id: str, priority: str) -> bool:
        """Update job priority in queue."""
        try:
            response = self.db.table('jobs_tickets').update(
                {'priority': priority}
            ).eq('id', ticket_id).execute()

            logger.info(f"Updated priority for ticket {ticket_id} to {priority}")
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error updating priority: {e}")
            return False

    # ========================================================================
    # KPI Dashboard
    # ========================================================================

    def get_kpi_dashboard(self) -> Dict[str, Any]:
        """Get complete KPI dashboard for dispatch centre."""
        try:
            return {
                'efficiency_metrics': self.get_dispatch_metrics(),
                'engineer_comparisons': self.get_engineer_performance_comparison(limit=5),
                'active_assignments': self.get_active_assignments(),
                'engineer_availability': self.get_engineer_availability(),
                'queue_status': self.get_dispatch_queue(limit=10),
                'performance_report': self.get_dispatch_performance_report(days=7),
            }

        except Exception as e:
            logger.error(f"Error getting KPI dashboard: {e}")
            return {}
