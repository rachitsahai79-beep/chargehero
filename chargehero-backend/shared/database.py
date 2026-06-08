"""Supabase database client initialization and management."""

from supabase import create_client, Client
from config import settings
from fastapi import HTTPException, status
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

    def execute_sql(self, query: str, params: dict = None) -> dict:
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

    def health_check(self) -> bool:
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


# Lazy-initialize database service on first use
_db_instance = None


def get_db_instance() -> SupabaseDB:
    """Lazy-initialize database service on first use."""
    global _db_instance
    if _db_instance is None:
        try:
            _db_instance = SupabaseDB()
            logger.info("Database service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return None
    return _db_instance


def get_db() -> SupabaseDB:
    """Dependency injection function to get the database instance."""
    db = get_db_instance()
    if db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable"
        )
    return db
