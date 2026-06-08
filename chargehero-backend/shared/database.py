"""Supabase database client initialization and management."""

from supabase import create_client, Client
from config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Wrapper around Supabase client for database operations."""

    def __init__(self):
        """Initialize Supabase client with credentials from settings."""
        self.client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_anon_key,
        )
        self.service_client: Client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key,
        )
        logger.info("Supabase client initialized")

    def get_client(self) -> Client:
        """Get the anonymous Supabase client for standard operations."""
        return self.client

    def get_service_client(self) -> Client:
        """Get the service role Supabase client for admin operations."""
        return self.service_client

    async def execute_sql(self, query: str, params: dict = None) -> dict:
        """
        Execute raw SQL query against the database.

        Args:
            query: SQL query string
            params: Optional parameters for the query

        Returns:
            Query result as dictionary
        """
        try:
            result = self.service_client.rpc("execute_sql", {"query": query})
            logger.debug(f"Query executed: {query}")
            return result
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            response = self.client.auth.get_session()
            logger.info("Database health check passed")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database instance
db = SupabaseDB()


def get_db() -> SupabaseDB:
    """Dependency injection function to get the database instance."""
    return db
