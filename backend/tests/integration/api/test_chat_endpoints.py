"""
Integration tests for chat API endpoints.

Tests complete chat API flows with real database and services.
"""

import pytest
from fastapi.testclient import TestClient


class TestChatEndpointsIntegration:
    """Integration tests for chat API endpoints."""

    def test_send_message_success(self, test_client: TestClient) -> None:
        """Test successful message sending."""
        response = test_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Hello, how are you?",
                "thread_id": "test_thread_123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "response" in data
        assert "thread_id" in data

    def test_send_message_with_language(self, test_client: TestClient) -> None:
        """Test message sending with language."""
        response = test_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Olá, como você está?",
                "thread_id": "test_thread_456",
                "language": "pt-BR",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("language") == "pt-BR"

    def test_send_message_invalid_request(self, test_client: TestClient) -> None:
        """Test message sending with invalid request."""
        response = test_client.post(
            "/api/v1/chat/message",
            json={
                "query": "",  # Empty query
                "thread_id": "test_thread",
            },
        )
        # Should return validation error
        assert response.status_code in [400, 422]

    def test_get_chat_history(self, test_client: TestClient) -> None:
        """Test getting chat history."""
        thread_id = "test_thread_history"

        # First, send a message
        test_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Test message",
                "thread_id": thread_id,
            },
        )

        # Then get history
        response = test_client.get(
            f"/api/v1/chat/history/{thread_id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_clear_chat_history(self, test_client: TestClient) -> None:
        """Test clearing chat history."""
        thread_id = "test_thread_clear"

        # Send a message
        test_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Test message",
                "thread_id": thread_id,
            },
        )

        # Clear history
        response = test_client.delete(
            f"/api/v1/chat/history/{thread_id}",
        )
        assert response.status_code == 200

        # Verify history is cleared
        history_response = test_client.get(
            f"/api/v1/chat/history/{thread_id}",
        )
        assert history_response.status_code == 200
        data = history_response.json()
        assert len(data.get("messages", [])) == 0

