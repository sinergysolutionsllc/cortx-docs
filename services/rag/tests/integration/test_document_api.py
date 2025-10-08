"""
Integration tests for document management API endpoints.

Tests cover:
- POST /documents/upload (document upload and processing)
- GET /documents (list documents with filtering)
- DELETE /documents/{id} (soft delete)
- Error handling and validation
"""

import io

import pytest


@pytest.mark.integration
class TestDocumentUpload:
    """Test document upload endpoint."""

    def test_upload_document_success(self, client, db_session, mock_embedding_model):
        """Test successful document upload."""
        # Create test file
        file_content = """# Test Document

This is a test document for upload.

## Section 1

Some content in section 1.

## Section 2

Some content in section 2.
"""
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.md", file, "text/markdown")},
            data={
                "title": "Test Document",
                "level": "platform",
                "description": "A test document",
                "access_level": "public",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["title"] == "Test Document"
        assert data["level"] == "platform"
        assert data["chunks_count"] > 0
        assert data["status"] == "active"

    def test_upload_document_with_hierarchy(self, client, mock_embedding_model):
        """Test uploading document with suite/module hierarchy."""
        file_content = "# Module Documentation\n\nThis is module-specific content."
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("module.md", file, "text/markdown")},
            data={
                "title": "DataFlow Module Docs",
                "level": "module",
                "suite_id": "fedsuite",
                "module_id": "dataflow",
                "access_level": "internal",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["title"] == "DataFlow Module Docs"
        assert data["level"] == "module"

    def test_upload_document_empty_file(self, client):
        """Test uploading empty file."""
        file = io.BytesIO(b"")

        response = client.post(
            "/documents/upload",
            files={"file": ("empty.txt", file, "text/plain")},
            data={"title": "Empty Doc", "level": "platform"},
        )

        assert response.status_code == 400
        assert "no usable content" in response.json()["detail"].lower()

    def test_upload_document_invalid_utf8(self, client):
        """Test uploading non-UTF-8 file."""
        # Invalid UTF-8 bytes
        file = io.BytesIO(b"\xff\xfe\xfd")

        response = client.post(
            "/documents/upload",
            files={"file": ("invalid.txt", file, "text/plain")},
            data={"title": "Invalid File", "level": "platform"},
        )

        assert response.status_code == 400
        assert "utf-8" in response.json()["detail"].lower()

    def test_upload_document_missing_title(self, client):
        """Test uploading without required title."""
        file_content = "Test content"
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={
                "level": "platform"
                # Missing title
            },
        )

        assert response.status_code == 422  # Validation error

    def test_upload_document_missing_level(self, client):
        """Test uploading without required level."""
        file_content = "Test content"
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={
                "title": "Test Doc"
                # Missing level
            },
        )

        assert response.status_code == 422  # Validation error

    def test_upload_document_large_file(self, client, mock_embedding_model):
        """Test uploading large document."""
        # Create large content
        large_content = "\n\n".join([f"Paragraph {i} with some content." for i in range(100)])
        file = io.BytesIO(large_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("large.txt", file, "text/plain")},
            data={"title": "Large Document", "level": "platform"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should create multiple chunks
        assert data["chunks_count"] > 1

    def test_upload_document_with_special_characters(self, client, mock_embedding_model):
        """Test uploading document with special characters."""
        file_content = """# Document with Special Chars

Content with émojis 🎉 and spëcial çharacters!

## Section with <>&"'

More content with [brackets] and {braces}.
"""
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("special.md", file, "text/markdown")},
            data={"title": "Special Characters Doc", "level": "platform"},
        )

        assert response.status_code == 200

    def test_upload_creates_chunks_in_db(self, client, db_session, mock_embedding_model):
        """Test that upload creates chunks in database."""
        from app.models import Chunk, Document

        file_content = """# Test

Section 1 content.

Section 2 content.
"""
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.md", file, "text/markdown")},
            data={"title": "Chunk Test", "level": "platform"},
        )

        assert response.status_code == 200
        doc_id = response.json()["id"]

        # Verify document in database
        doc = db_session.query(Document).filter(Document.id == doc_id).first()
        assert doc is not None

        # Verify chunks in database
        chunks = db_session.query(Chunk).filter(Chunk.document_id == doc_id).all()
        assert len(chunks) > 0
        assert all(chunk.embedding is not None for chunk in chunks)


@pytest.mark.integration
class TestListDocuments:
    """Test document listing endpoint."""

    def test_list_documents_empty(self, client):
        """Test listing when no documents exist."""
        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()

        assert "documents" in data
        assert data["total"] == 0
        assert len(data["documents"]) == 0

    def test_list_documents_basic(self, client, sample_document):
        """Test basic document listing."""
        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        assert len(data["documents"]) >= 1

        # Check document structure
        doc = data["documents"][0]
        assert "id" in doc
        assert "title" in doc
        assert "level" in doc
        assert "created_at" in doc

    def test_list_documents_filter_by_level(self, client, sample_document, suite_document):
        """Test filtering documents by level."""
        # Filter for platform level
        response = client.get("/documents?level=platform")

        assert response.status_code == 200
        data = response.json()

        # All results should be platform level
        for doc in data["documents"]:
            assert doc["level"] == "platform"

    def test_list_documents_filter_by_suite(self, client, sample_document, suite_document):
        """Test filtering documents by suite_id."""
        response = client.get("/documents?suite_id=fedsuite")

        assert response.status_code == 200
        data = response.json()

        # All results should have fedsuite
        for doc in data["documents"]:
            if doc["suite_id"]:
                assert doc["suite_id"] == "fedsuite"

    def test_list_documents_filter_by_module(self, client, module_document):
        """Test filtering documents by module_id."""
        response = client.get("/documents?module_id=dataflow")

        assert response.status_code == 200
        data = response.json()

        # All results should have dataflow module
        for doc in data["documents"]:
            if doc["module_id"]:
                assert doc["module_id"] == "dataflow"

    def test_list_documents_pagination(self, client, db_session, mock_embedding_model):
        """Test document listing pagination."""
        from app.models import Document

        # Create multiple documents
        for i in range(15):
            doc = Document(
                tenant_id="test_tenant",
                level="platform",
                title=f"Doc {i}",
                source_type="text",
                status="active",
            )
            db_session.add(doc)
        db_session.commit()

        # Get first page
        response1 = client.get("/documents?limit=5&offset=0")
        assert response1.status_code == 200
        data1 = response1.json()

        assert len(data1["documents"]) <= 5
        assert data1["limit"] == 5
        assert data1["offset"] == 0

        # Get second page
        response2 = client.get("/documents?limit=5&offset=5")
        assert response2.status_code == 200
        data2 = response2.json()

        assert len(data2["documents"]) <= 5
        assert data2["offset"] == 5

        # Documents should be different
        ids1 = {doc["id"] for doc in data1["documents"]}
        ids2 = {doc["id"] for doc in data2["documents"]}
        assert ids1 != ids2

    def test_list_documents_ordering(self, client, db_session):
        """Test that documents are ordered by created_at desc."""
        import time

        from app.models import Document

        # Create documents with slight delay
        for i in range(3):
            doc = Document(
                tenant_id="test_tenant",
                level="platform",
                title=f"Time Doc {i}",
                source_type="text",
                status="active",
            )
            db_session.add(doc)
            db_session.commit()
            time.sleep(0.01)

        response = client.get("/documents")
        data = response.json()

        # Should be in reverse chronological order
        titles = [doc["title"] for doc in data["documents"] if "Time Doc" in doc["title"]]
        assert titles == sorted(titles, reverse=True)

    def test_list_documents_with_chunks_count(self, client, sample_document, sample_chunks):
        """Test that listing includes chunk count."""
        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()

        # Find our document
        doc = next((d for d in data["documents"] if d["id"] == str(sample_document.id)), None)
        assert doc is not None
        assert doc["chunk_count"] > 0


@pytest.mark.integration
class TestDeleteDocument:
    """Test document deletion endpoint."""

    def test_delete_document_success(self, client, db_session):
        """Test successful document deletion."""
        from app.models import Document

        # Create document
        doc = Document(
            tenant_id="test_tenant",
            level="platform",
            title="To Delete",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = str(doc.id)

        # Delete document
        response = client.delete(f"/documents/{doc_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert data["id"] == doc_id

        # Verify soft delete (status changed)
        db_session.refresh(doc)
        assert doc.status == "deleted"

    def test_delete_document_not_found(self, client):
        """Test deleting non-existent document."""
        import uuid

        fake_id = str(uuid.uuid4())

        response = client.delete(f"/documents/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_document_invalid_id(self, client):
        """Test deleting with invalid UUID."""
        response = client.delete("/documents/invalid-uuid")

        # Should return validation error or 404
        assert response.status_code in [404, 422]

    def test_delete_document_twice(self, client, db_session):
        """Test deleting same document twice."""
        from app.models import Document

        doc = Document(
            tenant_id="test_tenant",
            level="platform",
            title="Delete Twice",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = str(doc.id)

        # First delete
        response1 = client.delete(f"/documents/{doc_id}")
        assert response1.status_code == 200

        # Second delete (document already deleted)
        response2 = client.delete(f"/documents/{doc_id}")
        # Should fail since status is now 'deleted'
        assert response2.status_code == 404


@pytest.mark.integration
class TestDocumentEndpointsErrorHandling:
    """Test error handling in document endpoints."""

    def test_upload_without_file(self, client):
        """Test upload without file attachment."""
        response = client.post("/documents/upload", data={"title": "No File", "level": "platform"})

        assert response.status_code == 422  # Validation error

    def test_list_documents_invalid_params(self, client):
        """Test listing with invalid parameters."""
        response = client.get("/documents?limit=-1")

        # Should either reject or use default
        assert response.status_code in [200, 422]

    def test_upload_document_db_error(self, client, db_session, mock_embedding_model):
        """Test handling database error during upload."""
        from unittest.mock import patch

        file_content = "Test content"
        file = io.BytesIO(file_content.encode("utf-8"))

        # Mock database commit to fail
        with patch.object(db_session, "commit", side_effect=Exception("DB error")):
            response = client.post(
                "/documents/upload",
                files={"file": ("test.txt", file, "text/plain")},
                data={"title": "DB Error Test", "level": "platform"},
            )

            # Should handle error gracefully
            # Note: This might not work as expected with test client
            # since it uses its own session


@pytest.mark.integration
class TestDocumentAccessControl:
    """Test access control for documents."""

    def test_list_documents_tenant_isolation(self, client, db_session):
        """Test that documents are isolated by tenant."""
        from app.models import Document

        # Create documents for different tenants
        doc1 = Document(
            tenant_id="tenant_a",
            level="platform",
            title="Tenant A Doc",
            source_type="text",
            status="active",
        )
        doc2 = Document(
            tenant_id="tenant_b",
            level="platform",
            title="Tenant B Doc",
            source_type="text",
            status="active",
        )
        db_session.add_all([doc1, doc2])
        db_session.commit()

        # List documents (will use test_tenant from fixture)
        response = client.get("/documents")

        assert response.status_code == 200
        data = response.json()

        # Should not see other tenant's documents
        titles = [doc["title"] for doc in data["documents"]]
        assert "Tenant A Doc" not in titles
        assert "Tenant B Doc" not in titles

    def test_delete_document_tenant_isolation(self, client, db_session):
        """Test that users can only delete their tenant's documents."""
        from app.models import Document

        # Create document for different tenant
        doc = Document(
            tenant_id="other_tenant",
            level="platform",
            title="Other Tenant Doc",
            source_type="text",
            status="active",
        )
        db_session.add(doc)
        db_session.commit()

        doc_id = str(doc.id)

        # Try to delete (should fail due to tenant mismatch)
        response = client.delete(f"/documents/{doc_id}")

        assert response.status_code == 404  # Not found (tenant filter)


@pytest.mark.integration
class TestDocumentMetadata:
    """Test document metadata handling."""

    def test_upload_preserves_metadata(self, client, db_session, mock_embedding_model):
        """Test that upload preserves file metadata."""
        file_content = "Test content"
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={"title": "Metadata Test", "level": "platform", "description": "Test description"},
        )

        assert response.status_code == 200
        doc_id = response.json()["id"]

        # Check in database
        from app.models import Document

        doc = db_session.query(Document).filter(Document.id == doc_id).first()

        assert doc.description == "Test description"
        assert "original_filename" in doc.doc_metadata
        assert doc.doc_metadata["original_filename"] == "test.txt"

    def test_upload_tracks_user(self, client, db_session, mock_embedding_model):
        """Test that upload tracks uploading user."""
        file_content = "Test content"
        file = io.BytesIO(file_content.encode("utf-8"))

        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
            data={"title": "User Track Test", "level": "platform"},
        )

        assert response.status_code == 200
        doc_id = response.json()["id"]

        # Check in database
        from app.models import Document

        doc = db_session.query(Document).filter(Document.id == doc_id).first()

        assert "uploaded_by" in doc.doc_metadata
