"""
E2E tests for chat flows.

Tests complete chat flows including REST API, WebSocket streaming,
and conversation history persistence.
"""

import json
import uuid
from typing import Any, Dict

import pytest

try:
    import websockets
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    websockets = None  # type: ignore


class TestChatFlowsE2E:
    """E2E tests for chat flows."""

    @pytest.mark.asyncio
    async def test_send_message_and_receive_response(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test sending message and receiving response via REST API."""
        thread_id = str(uuid.uuid4())

        # Send message
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Hello, how are you?",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        assert "thread_id" in data
        assert data["thread_id"] == thread_id
        assert "response" in data
        assert "text" in data["response"]
        assert "agent" in data["response"]

    @pytest.mark.asyncio
    async def test_chat_history(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test chat history with multiple messages."""
        thread_id = str(uuid.uuid4())

        # Send first message
        response1 = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "First message",
                "thread_id": thread_id,
            },
        )
        assert response1.status_code == 200

        # Send second message
        response2 = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": "Second message",
                "thread_id": thread_id,
            },
        )
        assert response2.status_code == 200

        # Get history
        history_response = await e2e_client.get(
            f"/api/v1/chat/history?thread_id={thread_id}",
        )
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert "messages" in history_data
        assert len(history_data["messages"]) >= 2

        # Verify order (most recent first or chronological)
        messages = history_data["messages"]
        assert messages[0]["content"] in ["First message", "Second message"]
        assert messages[1]["content"] in ["First message", "Second message"]

    @pytest.mark.asyncio
    @pytest.mark.skipif(not WEBSOCKETS_AVAILABLE, reason="websockets library not available")
    async def test_websocket_streaming(
        self,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test WebSocket streaming for chat responses."""
        if not WEBSOCKETS_AVAILABLE or websockets is None:
            pytest.skip("websockets library not available")

        base_url = e2e_environment["api_base_url"]
        # Convert http:// to ws:// for WebSocket
        ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_endpoint = f"{ws_url}/api/v1/chat/stream"

        thread_id = str(uuid.uuid4())

        # Connect via WebSocket
        async with websockets.connect(ws_endpoint) as websocket:
            # Send message
            message = {
                "query": "Test streaming message",
                "thread_id": thread_id,
                "language": "pt-BR",
            }
            await websocket.send(json.dumps(message))

            # Receive status updates
            status_received = False
            response_received = False

            while True:
                try:
                    data = await websocket.recv()
                    message_data = json.loads(data)

                    if "status" in message_data:
                        status_received = True
                        assert message_data["status"] in ["processing", "routing", "complete"]

                    if "response" in message_data:
                        response_received = True
                        assert "text" in message_data["response"]
                        break

                    # Timeout protection
                    if status_received and "complete" in str(message_data):
                        break

                except websockets.exceptions.ConnectionClosed:
                    break

            assert status_received, "Should receive status updates"
            assert response_received, "Should receive response"

    @pytest.mark.asyncio
    async def test_chat_persistence(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test that chat messages are persisted in database."""
        thread_id = str(uuid.uuid4())
        query = f"Test persistence message {uuid.uuid4()}"

        # Send message
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": query,
                "thread_id": thread_id,
            },
        )
        assert response.status_code == 200

        # Get history and verify persistence
        history_response = await e2e_client.get(
            f"/api/v1/chat/history?thread_id={thread_id}",
        )
        assert history_response.status_code == 200
        history_data = history_response.json()

        # Verify message is in history
        messages = history_data.get("messages", [])
        message_contents = [msg.get("content", "") for msg in messages]
        assert query in message_contents

