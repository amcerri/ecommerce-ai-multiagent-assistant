"""
Integration tests for documents API endpoints.

Tests complete documents API flows with real database and services.
"""

import pytest
from fastapi.testclient import TestClient


class TestDocumentsEndpointsIntegration:
    """Integration tests for documents API endpoints."""

    def test_upload_document_success(self, test_client: TestClient) -> None:
        """Test successful document upload."""
        # Create a test file
        test_file_content = b"PDF content for testing"
        files = {
            "file": ("test_document.pdf", test_file_content, "application/pdf"),
        }
        data = {
            "file_type": "commerce",
        }

        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )
        assert response.status_code == 200
        response_data = response.json()
        assert "document_id" in response_data
        assert "file_path" in response_data

    def test_upload_document_invalid_type(self, test_client: TestClient) -> None:
        """Test document upload with invalid file type."""
        test_file_content = b"Invalid file content"
        files = {
            "file": ("test.exe", test_file_content, "application/x-msdownload"),
        }
        data = {
            "file_type": "commerce",
        }

        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )
        # Should return validation error
        assert response.status_code in [400, 422]

    def test_get_document(self, test_client: TestClient) -> None:
        """Test getting document by ID."""
        # First upload a document
        test_file_content = b"PDF content for testing"
        files = {
            "file": ("test_document.pdf", test_file_content, "application/pdf"),
        }
        data = {
            "file_type": "commerce",
        }

        upload_response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # Then get the document
        response = test_client.get(
            f"/api/v1/documents/{document_id}",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == document_id

    def test_list_documents(self, test_client: TestClient) -> None:
        """Test listing documents."""
        response = test_client.get(
            "/api/v1/documents",
        )
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)

    def test_delete_document(self, test_client: TestClient) -> None:
        """Test deleting document."""
        # First upload a document
        test_file_content = b"PDF content for testing"
        files = {
            "file": ("test_document.pdf", test_file_content, "application/pdf"),
        }
        data = {
            "file_type": "commerce",
        }

        upload_response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            data=data,
        )
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]

        # Then delete it
        response = test_client.delete(
            f"/api/v1/documents/{document_id}",
        )
        assert response.status_code == 200

        # Verify it's deleted
        get_response = test_client.get(
            f"/api/v1/documents/{document_id}",
        )
        assert get_response.status_code == 404

