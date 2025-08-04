"""
Basic tests for FastBoard application.
Demonstrates testing patterns for the refactored codebase.
"""

def test_app_info(client):
    """Test the app info endpoint."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "FastBoard"
    assert "features" in data
    assert "limits" in data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]  # 503 if AI service unavailable
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_main_page(client):
    """Test the main application page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


# Note: These tests would require pytest and httpx to be installed
# Add to requirements.txt for development:
# pytest==7.4.3
# httpx==0.25.0
