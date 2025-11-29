"""
Tests for the FastAPI endpoints.

These tests verify that the /chat and /health endpoints
work correctly with mock data.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""
    
    def test_health_returns_200(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_returns_status(self, client):
        """Test that health endpoint returns status."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_health_returns_environment(self, client):
        """Test that health endpoint returns environment."""
        response = client.get("/health")
        data = response.json()
        
        assert "environment" in data


class TestChatEndpoint:
    """Tests for the /chat endpoint."""
    
    def test_chat_with_policy_id(self, client):
        """Test chat with a policy ID."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "What is the status of POL-1234?"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "data" in data
        assert data["data"]["policy"] is not None
        assert data["data"]["policy"]["policyId"] == "POL-1234"
    
    def test_chat_with_claim_id(self, client):
        """Test chat with a claim ID."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "What is the status of CLM-8899?"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["claim"] is not None
        assert data["data"]["claim"]["claimId"] == "CLM-8899"
    
    def test_chat_with_both_ids(self, client):
        """Test chat with both policy and claim IDs."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "Check claim CLM-8899 on policy POL-1234"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["data"]["policy"] is not None
        assert data["data"]["claim"] is not None
        assert data["data"]["documents"] is not None
    
    def test_chat_not_found(self, client):
        """Test chat with non-existent policy."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "Check POL-0000"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "couldn't find" in data["answer"].lower() or "not found" in data["answer"].lower()
    
    def test_chat_no_ids(self, client):
        """Test chat without any IDs."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "Hello"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
    
    def test_chat_missing_fields(self, client):
        """Test chat with missing required fields."""
        response = client.post("/chat", json={
            "userId": "user-123"
            # Missing "message"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_chat_answer_mentions_missing_docs(self, client):
        """Test that answer mentions missing documents."""
        response = client.post("/chat", json={
            "userId": "user-123",
            "message": "Status of CLM-8899"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # CLM-8899 has missing docs
        assert data["data"]["documents"]["missingDocs"] is not None
        assert len(data["data"]["documents"]["missingDocs"]) > 0
