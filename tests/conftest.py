"""
Test configuration for FastBoard application.
Sets up test fixtures and common utilities.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing WebSocket functionality."""
    # This would be implemented with proper WebSocket testing tools
    pass
