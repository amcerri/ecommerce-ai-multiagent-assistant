"""
E2E tests for Commerce Agent flows.

Tests complete Commerce Agent flows including document upload,
processing, and analysis.
"""

import uuid
from typing import Any, Dict

import pytest


class TestCommerceFlowsE2E:
    """E2E tests for Commerce Agent flows."""

    @pytest.mark.asyncio
    async def test_commerce_document_upload(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test commerce document upload and processing."""
        # Create a test PDF file content
        test_file_content = b"%PDF-1.4\nTest PDF content for E2E testing"

        # Upload document
        files = {
            "file": ("test_document.pdf", test_file_content, "application/pdf"),
        }
        data = {
            "type": "commerce",
        }

        response = await e2e_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )

        assert response.status_code == 200
        upload_data = response.json()
        assert "document_id" in upload_data
        assert "file_path" in upload_data

        # Verify document was created
        document_id = upload_data["document_id"]
        get_response = await e2e_client.get(
            f"/api/v1/documents/{document_id}",
        )
        assert get_response.status_code == 200
        document_data = get_response.json()
        assert document_data["id"] == document_id

    @pytest.mark.asyncio
    async def test_commerce_routing(
        self,
        e2e_client: Any,
        e2e_environment: Dict[str, Any],
    ) -> None:
        """Test routing to commerce agent with document context."""
        thread_id = str(uuid.uuid4())

        # First upload a document
        test_file_content = b"%PDF-1.4\nTest PDF content"
        files = {
            "file": ("test_document.pdf", test_file_content, "application/pdf"),
        }
        data = {
            "type": "commerce",
        }

        upload_response = await e2e_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # Send query about the document
        response = await e2e_client.post(
            "/api/v1/chat/message",
            json={
                "query": f"Analyze document {document_id}",
                "thread_id": thread_id,
                "language": "pt-BR",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent" in data["response"]

        # Verify routing (might route to commerce or triage)
        agent = data["response"].get("agent")
        assert agent in ["commerce", "triage", "knowledge", "analytics"]

