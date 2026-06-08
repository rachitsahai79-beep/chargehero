"""Real-time features using Supabase Realtime (WebSocket subscriptions)."""

import logging
import json
from typing import Callable, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RealtimeManager:
    """Manages WebSocket subscriptions to Supabase for real-time updates."""

    def __init__(self, db):
        """Initialize with Supabase client."""
        self.db = db
        self.subscriptions = {}

    def subscribe_to_engineer_assignments(self, engineer_id: str, callback: Callable) -> str:
        """
        Subscribe to new job assignments for an engineer.

        Triggers when:
        - New dispatch assignment created
        - Assignment status changes (pending → accepted)
        - Assignment rejected

        Args:
            engineer_id: Engineer UUID
            callback: Function to call when assignment updates

        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"assignments-{engineer_id}"

            def handle_change(payload):
                """Handle real-time changes from database."""
                if payload['eventType'] in ['INSERT', 'UPDATE']:
                    assignment = payload['new']
                    if assignment.get('engineer_id') == engineer_id:
                        logger.info(f"Assignment update for engineer {engineer_id}")
                        callback({
                            'type': 'assignment_update',
                            'engineer_id': engineer_id,
                            'assignment': assignment,
                            'event_type': payload['eventType'],
                            'timestamp': datetime.utcnow().isoformat()
                        })

            # Subscribe to dispatch assignments table
            subscription = self.db.realtime.on(
                'postgres_changes',
                {
                    'event': '*',
                    'schema': 'public',
                    'table': 'jobs_dispatch_assignments',
                    'filter': f'engineer_id=eq.{engineer_id}'
                },
                handle_change
            ).subscribe()

            self.subscriptions[subscription_id] = subscription
            logger.info(f"Subscribed engineer {engineer_id} to assignment updates")
            return subscription_id

        except Exception as e:
            logger.error(f"Error subscribing to assignments: {e}")
            raise

    def subscribe_to_ticket_updates(self, ticket_id: str, callback: Callable) -> str:
        """
        Subscribe to ticket status updates.

        Triggers when:
        - Ticket status changes (open → assigned → in_progress → resolved)
        - Engineer assigned to ticket
        - Service report submitted

        Args:
            ticket_id: Ticket UUID
            callback: Function to call on updates

        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"ticket-{ticket_id}"

            def handle_change(payload):
                """Handle ticket updates."""
                ticket = payload['new']
                if ticket.get('id') == ticket_id:
                    logger.info(f"Ticket {ticket_id} status change: {ticket.get('status')}")
                    callback({
                        'type': 'ticket_update',
                        'ticket_id': ticket_id,
                        'ticket': ticket,
                        'event_type': payload['eventType'],
                        'timestamp': datetime.utcnow().isoformat()
                    })

            subscription = self.db.realtime.on(
                'postgres_changes',
                {
                    'event': '*',
                    'schema': 'public',
                    'table': 'jobs_tickets',
                    'filter': f'id=eq.{ticket_id}'
                },
                handle_change
            ).subscribe()

            self.subscriptions[subscription_id] = subscription
            logger.info(f"Subscribed to ticket {ticket_id} updates")
            return subscription_id

        except Exception as e:
            logger.error(f"Error subscribing to ticket: {e}")
            raise

    def subscribe_to_engineer_earnings(self, engineer_id: str, callback: Callable) -> str:
        """
        Subscribe to engineer earnings updates.

        Triggers when:
        - New earnings recorded (job completed)
        - Earnings status changes (pending → paid)

        Args:
            engineer_id: Engineer UUID
            callback: Function to call on earnings update

        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"earnings-{engineer_id}"

            def handle_change(payload):
                """Handle earnings updates."""
                earning = payload['new']
                if earning.get('engineer_id') == engineer_id:
                    logger.info(f"Earnings update for engineer {engineer_id}: ₹{earning.get('amount')}")
                    callback({
                        'type': 'earnings_update',
                        'engineer_id': engineer_id,
                        'earning': earning,
                        'event_type': payload['eventType'],
                        'timestamp': datetime.utcnow().isoformat()
                    })

            subscription = self.db.realtime.on(
                'postgres_changes',
                {
                    'event': '*',
                    'schema': 'public',
                    'table': 'jobs_earnings',
                    'filter': f'engineer_id=eq.{engineer_id}'
                },
                handle_change
            ).subscribe()

            self.subscriptions[subscription_id] = subscription
            logger.info(f"Subscribed engineer {engineer_id} to earnings updates")
            return subscription_id

        except Exception as e:
            logger.error(f"Error subscribing to earnings: {e}")
            raise

    def subscribe_to_service_reports(self, ticket_id: str, callback: Callable) -> str:
        """
        Subscribe to service report submissions.

        Triggers when:
        - Service report submitted for ticket
        - Report status changes (engineer review → customer approval)

        Args:
            ticket_id: Ticket UUID
            callback: Function to call on report update

        Returns:
            Subscription ID
        """
        try:
            subscription_id = f"report-{ticket_id}"

            def handle_change(payload):
                """Handle report submissions."""
                report = payload['new']
                if report.get('ticket_id') == ticket_id:
                    logger.info(f"Service report update for ticket {ticket_id}")
                    callback({
                        'type': 'service_report_update',
                        'ticket_id': ticket_id,
                        'report': report,
                        'event_type': payload['eventType'],
                        'timestamp': datetime.utcnow().isoformat()
                    })

            subscription = self.db.realtime.on(
                'postgres_changes',
                {
                    'event': '*',
                    'schema': 'public',
                    'table': 'jobs_service_reports',
                    'filter': f'ticket_id=eq.{ticket_id}'
                },
                handle_change
            ).subscribe()

            self.subscriptions[subscription_id] = subscription
            logger.info(f"Subscribed to service reports for ticket {ticket_id}")
            return subscription_id

        except Exception as e:
            logger.error(f"Error subscribing to service reports: {e}")
            raise

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from a real-time channel.

        Args:
            subscription_id: ID of subscription to remove

        Returns:
            True if unsubscribed, False if not found
        """
        try:
            if subscription_id in self.subscriptions:
                subscription = self.subscriptions.pop(subscription_id)
                self.db.realtime.unsubscribe(subscription)
                logger.info(f"Unsubscribed from {subscription_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
            return False

    def unsubscribe_all(self) -> int:
        """
        Unsubscribe from all active subscriptions.

        Returns:
            Number of subscriptions closed
        """
        count = len(self.subscriptions)
        try:
            for subscription_id in list(self.subscriptions.keys()):
                self.unsubscribe(subscription_id)
            logger.info(f"Unsubscribed from {count} subscriptions")
            return count
        except Exception as e:
            logger.error(f"Error unsubscribing all: {e}")
            return 0

    def get_active_subscriptions(self) -> Dict[str, Any]:
        """
        Get list of active subscriptions.

        Returns:
            Dict with subscription IDs and their types
        """
        return {
            'count': len(self.subscriptions),
            'subscriptions': list(self.subscriptions.keys())
        }
