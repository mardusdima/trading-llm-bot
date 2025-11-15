"""
Pytest configuration and fixtures
"""
import pytest
import os
from unittest.mock import Mock, patch

@pytest.fixture
def mock_env():
    """Fixture to set up mock environment variables"""
    env_vars = {
        "PAPER_TRADING": "1",
        "DATABASE_URL": "postgresql://test:test@localhost/testdb",
        "REDIS_URL": "redis://localhost:6379/0",
        "LOG_LEVEL": "INFO"
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def mock_db_session():
    """Fixture for mocking database session"""
    from unittest.mock import Mock, MagicMock
    session = MagicMock()
    session.query.return_value.filter_by.return_value.first.return_value = None
    session.query.return_value.filter_by.return_value.all.return_value = []
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    return session

