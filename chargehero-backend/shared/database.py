"""Supabase database client initialization and management."""

from supabase import create_client, Client
from config import settings
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class SupabaseDB:
    """Wrapper around Supabase client for database operations."""

    @staticmethod
    def _clean(value: str) -> str:
        """Strip whitespace and stray surrounding quotes from a config value."""
        if value is None:
            return ""
        return value.strip().strip('"').strip("'").strip()

    def __init__(self):
        """Initialize Supabase client with credentials from settings."""
        # Normalize URL: drop trailing slash and any accidental /rest/v1 suffix
        url = self._clean(settings.supabase_url)
        if url.endswith("/rest/v1/") or url.endswith("/rest/v1"):
            url = url.split("/rest/v1")[0]
        url = url.rstrip("/")

        anon_key = self._clean(settings.supabase_anon_key)
        service_key = self._clean(settings.supabase_service_role_key)

        # Diagnostic: log key FORMAT only (prefix + length), never the full secret.
        # A valid Supabase JWT starts with "eyJ"; the new key format starts with "sb_".
        logger.info(
            "Supabase config -> url=%s | anon_prefix=%r anon_len=%d | service_prefix=%r service_len=%d",
            url,
            anon_key[:4],
            len(anon_key),
            service_key[:4],
            len(service_key),
        )
        if not anon_key.startswith("eyJ"):
            logger.warning(
                "SUPABASE_ANON_KEY does not look like a JWT (expected to start with 'eyJ'). "
                "supabase==2.0.0 requires the legacy JWT key, not the new sb_publishable_ key."
            )

        self.client: Client = create_client(
            supabase_url=url,
            supabase_key=anon_key,
        )
        self.service_client: Client = create_client(
            supabase_url=url,
            supabase_key=service_key,
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
