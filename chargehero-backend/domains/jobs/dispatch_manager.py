"""Dispatch manager - integrates dispatch algorithm with jobs service for automated assignment."""

import logging
from typing import List, Optional, Dict, Any
from domains.jobs.service import JobsService
from domains.jobs.dispatch_algorithm import DispatchAlgorithm, DispatchScore
from shared.database import SupabaseDB

logger = logging.getLogger(__name__)


class DispatchManager:
    """Orchestrates job dispatch to engineers using scoring algorithm."""

    def __init__(self, db: SupabaseDB):
        """Initialize with database and dependencies."""
        self.db = db
        self.jobs_service = JobsService(db)
        self.algorithm = DispatchAlgorithm(db)

    def get_eligible_engineers(self, ticket_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get eligible engineers for a ticket based on:
        - Skills/certifications
        - Current availability
        - Geographic proximity

        Args:
            ticket_id: Ticket ID to find engineers for
            limit: Maximum number of engineers to return

        Returns:
            List of engineer records with computed scores
        """
        try:
            ticket = self.jobs_service.get_ticket(ticket_id)
            if not ticket:
                logger.warning(f"Ticket {ticket_id} not found")
                return []

            charger = self.jobs_service.get_charger(ticket['charger_id'])
            if not charger:
                logger.warning(f"Charger {ticket['charger_id']} not found")
                return []

            # Get all engineers (should be filtered by availability in production)
            try:
                engineers_response = self.db.table('auth_engineer_profiles').select('*').execute()
                engineers = engineers_response.data or []
            except Exception as e:
                logger.error(f"Error fetching engineers: {e}")
                return []

            if not engineers:
                logger.info(f"No engineers available for ticket {ticket_id}")
                return []

            # Build context for each engineer
            eligible_engineers = []

            for engineer in engineers:
                user_id = engineer.get('id')

                # Get engineer skills
                try:
                    skills_response = self.db.table('jobs_engineer_skills').select('*').eq(
                        'user_id', user_id
                    ).execute()
                    skills = skills_response.data or []
                except Exception as e:
                    logger.error(f"Error fetching skills for engineer {user_id}: {e}")
                    skills = []

                # Get engineer rating (from completed jobs)
                try:
                    completed_response = self.db.table('jobs_service_reports').select('rating_by_customer').eq(
                        'engineer_id', user_id
                    ).execute()
                    ratings = [r['rating_by_customer'] for r in (completed_response.data or [])
                              if r.get('rating_by_customer')]
                    avg_rating = sum(ratings) / len(ratings) if ratings else 5.0
                    completed_jobs = len(ratings)
                except Exception as e:
                    logger.error(f"Error fetching ratings for engineer {user_id}: {e}")
                    avg_rating = 5.0
                    completed_jobs = 0

                # Get current job count
                try:
                    jobs_response = self.db.table('jobs_dispatch_assignments').select('count', count='exact').eq(
                        'engineer_id', user_id
                    ).in_('status', ['pending', 'accepted', 'in_progress']).execute()
                    current_jobs = jobs_response.count or 0
                except Exception as e:
                    logger.error(f"Error fetching current jobs for engineer {user_id}: {e}")
                    current_jobs = 0

                # Score this engineer
                score = self.algorithm.score_engineer(
                    engineer, charger, skills,
                    engineer_rating=avg_rating,
                    completed_jobs=completed_jobs,
                    current_jobs_count=current_jobs
                )

                if score:
                    eligible_engineers.append(score)

            # Sort by total score descending
            eligible_engineers.sort(key=lambda s: s.total_score, reverse=True)

            logger.info(f"Found {len(eligible_engineers)} eligible engineers for ticket {ticket_id}")
            return eligible_engineers[:limit]

        except Exception as e:
            logger.error(f"Error getting eligible engineers: {e}")
            return []

    def auto_dispatch_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """
        Automatically dispatch ticket to best available engineer.

        Uses dispatch algorithm to:
        1. Find eligible engineers
        2. Select best match
        3. Create dispatch assignment
        4. Notify engineer

        Args:
            ticket_id: Ticket ID to dispatch

        Returns:
            Dispatch assignment record or None if no suitable engineer
        """
        try:
            # Get eligible engineers
            eligible = self.get_eligible_engineers(ticket_id, limit=10)

            if not eligible:
                logger.warning(f"No eligible engineers found for ticket {ticket_id}")
                return None

            # Get recommendation
            best_engineer = self.algorithm.get_assignment_recommendation(eligible)

            if not best_engineer:
                logger.warning(f"No recommended engineer for ticket {ticket_id}")
                return None

            # Dispatch to best engineer
            assignment = self.jobs_service.assign_ticket_to_engineer(
                ticket_id=ticket_id,
                engineer_id=best_engineer.engineer_id,
                dispatch_score=best_engineer.total_score
            )

            logger.info(
                f"Auto-dispatched ticket {ticket_id} to engineer {best_engineer.engineer_id} "
                f"with score {best_engineer.total_score:.1f}"
            )

            # TODO: Send real-time notification to engineer
            # TODO: Send SMS/push notification

            return assignment

        except Exception as e:
            logger.error(f"Error auto-dispatching ticket {ticket_id}: {e}")
            return None

    def manually_dispatch_ticket(self, ticket_id: str, engineer_id: str) -> Optional[Dict[str, Any]]:
        """
        Manually dispatch ticket to specific engineer.

        Args:
            ticket_id: Ticket ID to dispatch
            engineer_id: Engineer ID to assign to

        Returns:
            Dispatch assignment record or None on error
        """
        try:
            ticket = self.jobs_service.get_ticket(ticket_id)
            if not ticket:
                logger.warning(f"Ticket {ticket_id} not found")
                return None

            # Get eligible engineers to compute score
            eligible = self.get_eligible_engineers(ticket_id, limit=100)
            selected = next((e for e in eligible if e.engineer_id == engineer_id), None)

            dispatch_score = selected.total_score if selected else 0.0

            assignment = self.jobs_service.assign_ticket_to_engineer(
                ticket_id=ticket_id,
                engineer_id=engineer_id,
                dispatch_score=dispatch_score
            )

            logger.info(
                f"Manually dispatched ticket {ticket_id} to engineer {engineer_id} "
                f"with score {dispatch_score:.1f}"
            )

            return assignment

        except Exception as e:
            logger.error(f"Error manually dispatching ticket: {e}")
            return None

    def get_dispatch_score_breakdown(self, ticket_id: str, engineer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed score breakdown for an engineer for a ticket.

        Args:
            ticket_id: Ticket ID
            engineer_id: Engineer ID

        Returns:
            Detailed score breakdown or None
        """
        try:
            ticket = self.jobs_service.get_ticket(ticket_id)
            charger = self.jobs_service.get_charger(ticket['charger_id'])

            # Fetch engineer data
            engineer_response = self.db.table('auth_engineer_profiles').select('*').eq(
                'id', engineer_id
            ).execute()

            if not engineer_response.data:
                return None

            engineer = engineer_response.data[0]

            # Get skills
            skills_response = self.db.table('jobs_engineer_skills').select('*').eq(
                'user_id', engineer_id
            ).execute()
            skills = skills_response.data or []

            # Get rating
            ratings_response = self.db.table('jobs_service_reports').select('rating_by_customer').eq(
                'engineer_id', engineer_id
            ).execute()
            ratings = [r['rating_by_customer'] for r in (ratings_response.data or [])
                      if r.get('rating_by_customer')]
            avg_rating = sum(ratings) / len(ratings) if ratings else 5.0
            completed_jobs = len(ratings)

            # Get current jobs
            jobs_response = self.db.table('jobs_dispatch_assignments').select('count', count='exact').eq(
                'engineer_id', engineer_id
            ).in_('status', ['pending', 'accepted', 'in_progress']).execute()
            current_jobs = jobs_response.count or 0

            # Calculate score
            score = self.algorithm.score_engineer(
                engineer, charger, skills,
                engineer_rating=avg_rating,
                completed_jobs=completed_jobs,
                current_jobs_count=current_jobs
            )

            if not score:
                return None

            return {
                'engineer_id': engineer_id,
                'ticket_id': ticket_id,
                'total_score': score.total_score,
                'skill_match_score': score.skill_match_score,
                'proximity_score': score.proximity_score,
                'rating_score': score.rating_score,
                'availability_score': score.availability_score,
                'distance_km': score.distance_km,
                'is_certified': score.is_certified,
                'is_available': score.is_available,
                'current_jobs': current_jobs,
                'average_rating': round(avg_rating, 2),
                'completed_jobs': completed_jobs
            }

        except Exception as e:
            logger.error(f"Error getting score breakdown: {e}")
            return None

    def batch_dispatch_tickets(self, ticket_ids: List[str], strategy: str = 'auto') -> Dict[str, Any]:
        """
        Dispatch multiple tickets using specified strategy.

        Args:
            ticket_ids: List of ticket IDs to dispatch
            strategy: 'auto' for automatic, 'manual' for manual assignment

        Returns:
            Summary of dispatch results
        """
        results = {
            'total': len(ticket_ids),
            'successful': 0,
            'failed': 0,
            'assignments': []
        }

        for ticket_id in ticket_ids:
            try:
                if strategy == 'auto':
                    assignment = self.auto_dispatch_ticket(ticket_id)
                else:
                    # Default to auto if strategy unknown
                    assignment = self.auto_dispatch_ticket(ticket_id)

                if assignment:
                    results['successful'] += 1
                    results['assignments'].append(assignment)
                else:
                    results['failed'] += 1
            except Exception as e:
                logger.error(f"Error dispatching ticket {ticket_id}: {e}")
                results['failed'] += 1

        logger.info(
            f"Batch dispatch completed: {results['successful']}/{results['total']} successful"
        )

        return results
