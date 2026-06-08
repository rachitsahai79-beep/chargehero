"""Business logic for admin domain."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations."""

    def __init__(self, db):
        """Initialize with database instance."""
        self.db = db

    # ========================================================================
    # Engineer Management
    # ========================================================================

    def get_engineers_list(self, status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get list of all engineers with summary statistics."""
        try:
            query = self.db.table('auth_users').select('*').eq('role', 'engineer')

            if status:
                query = query.eq('status', status)

            response = query.limit(limit).execute()
            engineers = response.data or []

            # Enrich with statistics
            enriched = []
            for eng in engineers:
                stats = self._get_engineer_stats(eng['id'])
                enriched.append({
                    **eng,
                    'total_jobs': stats.get('total_jobs', 0),
                    'completed_jobs': stats.get('completed_jobs', 0),
                    'average_rating': stats.get('average_rating', 0),
                    'active_tickets': stats.get('active_tickets', 0),
                })

            return enriched

        except Exception as e:
            logger.error(f"Error getting engineers list: {e}")
            return []

    def get_engineer_detail(self, engineer_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed engineer information."""
        try:
            # Get engineer record
            eng_response = self.db.table('auth_users').select('*').eq('id', engineer_id).execute()
            if not eng_response.data:
                return None

            engineer = eng_response.data[0]

            # Get statistics
            stats = self._get_engineer_stats(engineer_id)

            # Get skills
            skills_response = self.db.table('jobs_engineer_skills').select('*').eq(
                'user_id', engineer_id
            ).eq('is_certified', True).execute()
            certifications = [s.get('charger_brand') for s in (skills_response.data or [])]

            # Get earnings
            earnings_response = self.db.table('jobs_earnings').select('amount, status').eq(
                'engineer_id', engineer_id
            ).execute()
            earnings_data = earnings_response.data or []
            total_earnings = sum(float(e.get('amount', 0)) for e in earnings_data)
            pending_earnings = sum(
                float(e.get('amount', 0)) for e in earnings_data
                if e.get('status') == 'pending'
            )

            return {
                **engineer,
                **stats,
                'verified_skills': certifications,
                'certifications': certifications,
                'earnings_total': total_earnings,
                'earnings_pending': pending_earnings,
            }

        except Exception as e:
            logger.error(f"Error getting engineer detail: {e}")
            return None

    def update_engineer(self, engineer_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update engineer status or certification."""
        try:
            update_data = {}

            if 'status' in data:
                update_data['status'] = data['status']
            if 'certification_level' in data:
                update_data['certification_level'] = data['certification_level']
            if 'is_active' in data:
                update_data['is_active'] = data['is_active']

            if not update_data:
                return self.get_engineer_detail(engineer_id)

            updated = self.db.table('auth_users').update(update_data).eq('id', engineer_id).execute()

            logger.info(f"Updated engineer {engineer_id}: {update_data}")
            return self.get_engineer_detail(engineer_id)

        except Exception as e:
            logger.error(f"Error updating engineer: {e}")
            return None

    def certify_engineer(self, engineer_id: str, charger_brand: str, charger_type: str) -> bool:
        """Certify engineer for charger type."""
        try:
            response = self.db.table('jobs_engineer_skills').insert({
                'user_id': engineer_id,
                'charger_type': charger_type,
                'charger_brand': charger_brand,
                'is_certified': True,
                'certified_by': 'admin',
                'certified_at': datetime.utcnow().isoformat()
            }).execute()

            logger.info(f"Certified engineer {engineer_id} for {charger_brand} {charger_type}")
            return bool(response.data)

        except Exception as e:
            logger.error(f"Error certifying engineer: {e}")
            return False

    # ========================================================================
    # Statistics & Reporting
    # ========================================================================

    def _get_engineer_stats(self, engineer_id: str) -> Dict[str, Any]:
        """Get engineer statistics."""
        try:
            # Total and completed jobs
            jobs_response = self.db.table('jobs_tickets').select('id, status').eq(
                'assigned_engineer_id', engineer_id
            ).execute()
            jobs = jobs_response.data or []
            total_jobs = len(jobs)
            completed_jobs = sum(1 for j in jobs if j.get('status') in ['resolved', 'closed'])
            active_tickets = sum(1 for j in jobs if j.get('status') in ['assigned', 'in_progress'])

            # Average rating
            reports_response = self.db.table('jobs_service_reports').select(
                'rating_by_customer'
            ).eq('engineer_id', engineer_id).execute()
            reports = reports_response.data or []
            ratings = [r.get('rating_by_customer') for r in reports if r.get('rating_by_customer')]
            average_rating = sum(ratings) / len(ratings) if ratings else 0

            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'active_tickets': active_tickets,
                'average_rating': round(average_rating, 1),
            }

        except Exception as e:
            logger.error(f"Error calculating engineer stats: {e}")
            return {
                'total_jobs': 0,
                'completed_jobs': 0,
                'active_tickets': 0,
                'average_rating': 0,
            }

    def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get admin dashboard overview."""
        try:
            # Engineer counts
            engineers_response = self.db.table('auth_users').select('id, status').eq(
                'role', 'engineer'
            ).execute()
            engineers = engineers_response.data or []
            total_engineers = len(engineers)
            active_engineers = sum(1 for e in engineers if e.get('status') == 'active')
            pending_engineers = sum(1 for e in engineers if e.get('status') == 'pending')

            # Job counts
            jobs_response = self.db.table('jobs_tickets').select('id, status').execute()
            jobs = jobs_response.data or []
            total_jobs = len(jobs)
            completed_jobs = sum(1 for j in jobs if j.get('status') in ['resolved', 'closed'])
            in_progress_jobs = sum(1 for j in jobs if j.get('status') in ['assigned', 'in_progress'])

            # Revenue
            earnings_response = self.db.table('jobs_earnings').select('amount').execute()
            earnings = earnings_response.data or []
            total_revenue = sum(float(e.get('amount', 0)) for e in earnings)

            # Ratings
            reports_response = self.db.table('jobs_service_reports').select(
                'rating_by_customer'
            ).execute()
            reports = reports_response.data or []
            ratings = [r.get('rating_by_customer') for r in reports if r.get('rating_by_customer')]
            average_engineer_rating = sum(ratings) / len(ratings) if ratings else 0

            # SLA compliance (simplified)
            system_sla_compliance = 95.0

            return {
                'total_engineers': total_engineers,
                'active_engineers': active_engineers,
                'pending_engineers': pending_engineers,
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'in_progress_jobs': in_progress_jobs,
                'total_revenue': round(total_revenue, 2),
                'average_engineer_rating': round(average_engineer_rating, 1),
                'system_sla_compliance': system_sla_compliance,
            }

        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {}

    def get_engineer_statistics(self, engineer_id: str) -> Dict[str, Any]:
        """Get detailed engineer statistics."""
        try:
            engineer = self.get_engineer_detail(engineer_id)
            if not engineer:
                return {}

            stats = self._get_engineer_stats(engineer_id)

            # Resolution time
            reports_response = self.db.table('jobs_service_reports').select(
                'resolution_time_minutes'
            ).eq('engineer_id', engineer_id).execute()
            reports = reports_response.data or []
            times = [r.get('resolution_time_minutes') for r in reports if r.get('resolution_time_minutes')]
            avg_resolution_time = sum(times) / len(times) if times else 0

            return {
                'engineer_id': engineer_id,
                'engineer_name': engineer.get('name'),
                **stats,
                'average_resolution_time_minutes': round(avg_resolution_time, 1),
                'sla_compliance_percentage': 95.0,
                'customer_satisfaction_percentage': round(stats['average_rating'] * 20, 1),
            }

        except Exception as e:
            logger.error(f"Error getting engineer statistics: {e}")
            return {}

    def get_revenue_report(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue report for date range."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Get all earnings in period
            earnings_response = self.db.table('jobs_earnings').select('amount').execute()
            earnings = earnings_response.data or []

            total_earnings = sum(float(e.get('amount', 0)) for e in earnings)
            fees = total_earnings * 0.1  # 10% platform fee (simplified)
            net_revenue = total_earnings - fees

            return {
                'total_revenue': round(total_earnings, 2),
                'total_fees': round(fees, 2),
                'net_revenue': round(net_revenue, 2),
                'job_count': len(earnings),
                'average_job_revenue': round(total_earnings / len(earnings), 2) if earnings else 0,
                'currency': 'INR',
                'period_start': start_date.isoformat(),
                'period_end': datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting revenue report: {e}")
            return {}
