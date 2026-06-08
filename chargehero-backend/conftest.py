"""Pytest configuration and fixtures for ChargeHero backend tests."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Load test environment variables before importing anything else
test_env_file = Path(__file__).parent / ".env.test"
if test_env_file.exists():
    with open(test_env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key] = value

import pytest

# Mock supabase before any local imports
sys.modules["supabase"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.extensions"] = MagicMock()


@pytest.fixture
def mock_db():
    """Create a mock Supabase database instance."""
    db = MagicMock()
    db.client = MagicMock()
    db.service_client = MagicMock()
    return db


@pytest.fixture
def mock_supabase_client(mock_db):
    """Create a mock Supabase client with table operations."""
    mock_client = MagicMock()

    # Create chainable mock for table().select().eq().execute()
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_execute
    mock_table.update.return_value = mock_eq
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute

    return mock_client
