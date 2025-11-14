"""
Document API routes (upload, analysis, and storage endpoints).

Overview
  Provides REST endpoints for commerce document upload, processing, analysis,
  and storage. Only commerce documents can be uploaded by users (knowledge and
  analytics documents are processed via administrative scripts).

Design
  - **Upload Restriction**: Only commerce documents allowed for user uploads.
  - **File Validation**: Validates file type and size before processing.
  - **Storage Integration**: Saves files to local storage before processing.
  - **Commerce Agent Integration**: Uses Commerce Agent for document processing.
  - **Database Persistence**: Stores document metadata in database.

Integration
  - Consumes: Commerce Agent, storage, database models, dependencies.
  - Returns: DocumentResponse, DocumentListResponse.
  - Used by: Frontend Next.js application.
  - Observability: Logs all uploads, processing, and errors.

Usage
  >>> POST /api/v1/documents/upload
  >>> file: <file>, type: "commerce"
  >>> {"document_id": "...", "filename": "...", "status": "processed"}
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AssistantDep, DBDep
from app.api.schemas.documents import DocumentListResponse, DocumentResponse, DocumentUploadRequest
from app.config.constants import MAX_FILE_SIZE_MB, SUPPORTED_FILE_TYPES
from app.config.exceptions import StorageException, ValidationException
from app.graph.state import GraphState
from app.infrastructure.database.models.commerce import CommerceDocument
from app.infrastructure.storage.local_storage import get_storage
from app.utils.validation import validate_file, validate_file_size, validate_file_type

logger = logging.getLogger(__name__)

# Create router
documents_router = APIRouter(prefix="/documents", tags=["documents"])


@documents_router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    type: str = Form(default="commerce"),
    request: Request = None,  # type: ignore
    db: DBDep = None,  # type: ignore
    assistant: AssistantDep = None,  # type: ignore
) -> DocumentResponse:
    """Upload commerce document for processing.

    Uploads a commerce document (PDF, DOCX, TXT, images) and processes it
    using the Commerce Agent. Only commerce documents are allowed for user uploads.

    Args:
        file: Uploaded file.
        type: Document type (must be "commerce").
        request: FastAPI request (for user_id when auth is implemented).
        db: Database session.
        assistant: LangGraph assistant instance.

    Returns:
        DocumentResponse with document_id, filename, status, and metadata.

    Raises:
        HTTPException: 400 if type is not "commerce" or file is invalid.
        HTTPException: 500 if processing fails.
    """
    try:
        # Step 1: Validate type
        if type != "commerce":
            raise ValidationException(
                message="Only commerce documents can be uploaded by users. Knowledge and analytics documents are processed via administrative scripts.",
                details={"type": type, "allowed_type": "commerce"},
            )

        # Step 2: Validate file
        if not file.filename:
            raise ValidationException(
                message="Filename is required",
                details={"file": file.filename},
            )

        # Validate file type
        file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if not validate_file_type(file_extension, SUPPORTED_FILE_TYPES):
            raise ValidationException(
                message=f"File type not supported: {file_extension}",
                details={"file": file.filename, "supported_types": SUPPORTED_FILE_TYPES},
            )

        # Read file content
        file_content = await file.read()
        file_size_mb = len(file_content) / (1024 * 1024)

        # Validate file size
        if not validate_file_size(file_size_mb, MAX_FILE_SIZE_MB):
            raise ValidationException(
                message=f"File size exceeds maximum: {file_size_mb:.2f}MB > {MAX_FILE_SIZE_MB}MB",
                details={"file": file.filename, "size_mb": file_size_mb, "max_mb": MAX_FILE_SIZE_MB},
            )

        # Step 3: Save file to storage
        storage = get_storage()
        try:
            file_path = await storage.save(
                file_content,
                file.filename,
                file_type="commerce",
            )
        except Exception as e:
            logger.error(f"Failed to save file to storage: {e}", exc_info=True)
            raise StorageException(
                message="Failed to save file to storage",
                details={"file": file.filename, "error": str(e)},
            ) from e

        # Step 4: Create document record
        document_id = str(uuid.uuid4())
        user_id = None  # TODO: Get from authentication when implemented

        document = CommerceDocument(
            id=uuid.UUID(document_id),
            user_id=user_id,
            file_name=file.filename,
            file_path=file_path,
            file_type=file_extension,
            extracted_data={},
            schema_definition={},
            processing_metadata=None,
            confidence_score=None,
        )
        db.add(document)
        await db.flush()  # Get document.id

        # Step 5: Process document using Commerce Agent
        try:
            # Create GraphState for commerce agent
            state: GraphState = {
                "thread_id": str(uuid.uuid4()),
                "query": f"Process document: {file.filename}",
                "language": "pt-BR",
                "file_path": file_path,
                "file_type": file_extension,
                "user_id": user_id,
                "router_decision": None,
                "agent_response": None,
                "conversation_history": [],
                "metadata": {},
                "interrupts": {},
            }

            # Execute graph (commerce agent will process the document)
            if hasattr(assistant, "ainvoke"):
                final_state = await assistant.ainvoke(state)
            else:
                import asyncio
                final_state = await asyncio.to_thread(assistant.invoke, state)

            # Get extracted data from state
            extracted_data = final_state.get("extracted_data")
            schema = final_state.get("schema")
            processing_metadata = final_state.get("processing_metadata")
            confidence_score = final_state.get("confidence_score")

            # Update document with extracted data
            document.extracted_data = extracted_data or {}
            document.schema_definition = schema or {}
            document.processing_metadata = processing_metadata
            document.confidence_score = confidence_score

        except Exception as e:
            logger.error(f"Failed to process document: {e}", exc_info=True)
            document.processing_metadata = {"error": str(e)}
            # Continue to save document with error in metadata

        # Step 6: Save document
        await db.commit()

        # Step 7: Create response
        # Determine status based on extracted_data
        status = "processed" if document.extracted_data and len(document.extracted_data) > 0 else "pending"
        if document.processing_metadata and document.processing_metadata.get("error"):
            status = "error"

        response = DocumentResponse(
            document_id=document_id,
            filename=document.file_name,
            file_type=document.file_type,
            status=status,
            extracted_data=document.extracted_data,
            schema_definition=document.schema_definition,
            confidence_score=document.confidence_score,
            processing_metadata=document.processing_metadata,
            created_at=document.created_at.isoformat() if document.created_at else None,
            updated_at=document.updated_at.isoformat() if document.updated_at else None,
        )

        logger.info(
            f"Document uploaded and processed: {document_id}",
            extra={"document_id": document_id, "filename": file.filename, "status": status},
        )

        return response

    except ValidationException:
        raise
    except StorageException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}",
        ) from e


@documents_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: DBDep,
) -> DocumentResponse:
    """Get document information.

    Retrieves information about a processed document.

    Args:
        document_id: Document ID (UUID).
        db: Database session.

    Returns:
        DocumentResponse with document information.

    Raises:
        HTTPException: 404 if document not found.
    """
    try:
        # Find document
        result = await db.execute(
            select(CommerceDocument).where(CommerceDocument.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}",
            )

        # Determine status
        status = "processed" if document.extracted_data and len(document.extracted_data) > 0 else "pending"
        if document.processing_metadata and document.processing_metadata.get("error"):
            status = "error"

        # Create response
        response = DocumentResponse(
            document_id=str(document.id),
            filename=document.file_name,
            file_type=document.file_type,
            status=status,
            extracted_data=document.extracted_data,
            schema_definition=document.schema_definition,
            confidence_score=document.confidence_score,
            processing_metadata=document.processing_metadata,
            created_at=document.created_at.isoformat() if document.created_at else None,
            updated_at=document.updated_at.isoformat() if document.updated_at else None,
        )

        return response

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: {document_id}",
        )
    except Exception as e:
        logger.error(f"Error retrieving document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve document: {str(e)}",
        ) from e


@documents_router.post("/{document_id}/analyze", response_model=DocumentResponse)
async def analyze_document(
    document_id: str,
    db: DBDep,
    assistant: AssistantDep,
) -> DocumentResponse:
    """Re-analyze document.

    Reprocesses a document using the Commerce Agent.

    Args:
        document_id: Document ID (UUID).
        db: Database session.
        assistant: LangGraph assistant instance.

    Returns:
        DocumentResponse with updated information.

    Raises:
        HTTPException: 404 if document not found.
        HTTPException: 500 if processing fails.
    """
    try:
        # Find document
        result = await db.execute(
            select(CommerceDocument).where(CommerceDocument.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}",
            )

        # Reprocess document
        state: GraphState = {
            "thread_id": str(uuid.uuid4()),
            "query": f"Re-analyze document: {document.file_name}",
            "language": "pt-BR",
            "file_path": document.file_path,
            "file_type": document.file_type,
            "user_id": str(document.user_id) if document.user_id else None,
            "router_decision": None,
            "agent_response": None,
            "conversation_history": [],
            "metadata": {},
            "interrupts": {},
        }

        # Execute graph
        if hasattr(assistant, "ainvoke"):
            final_state = await assistant.ainvoke(state)
        else:
            import asyncio
            final_state = await asyncio.to_thread(assistant.invoke, state)

        # Update document
        document.extracted_data = final_state.get("extracted_data") or {}
        document.schema_definition = final_state.get("schema") or {}
        document.processing_metadata = final_state.get("processing_metadata")
        document.confidence_score = final_state.get("confidence_score")

        await db.commit()

        # Determine status
        status = "processed" if document.extracted_data and len(document.extracted_data) > 0 else "pending"

        # Create response
        response = DocumentResponse(
            document_id=str(document.id),
            filename=document.file_name,
            file_type=document.file_type,
            status=status,
            extracted_data=document.extracted_data,
            schema_definition=document.schema_definition,
            confidence_score=document.confidence_score,
            processing_metadata=document.processing_metadata,
            created_at=document.created_at.isoformat() if document.created_at else None,
            updated_at=document.updated_at.isoformat() if document.updated_at else None,
        )

        logger.info(f"Document re-analyzed: {document_id}")

        return response

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: {document_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-analyzing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to re-analyze document: {str(e)}",
        ) from e


@documents_router.post("/{document_id}/store")
async def store_document(
    document_id: str,
    db: DBDep,
) -> Dict[str, bool]:
    """Store document in database.

    Confirms document storage (updates status to "stored").

    Args:
        document_id: Document ID (UUID).
        db: Database session.

    Returns:
        JSON with success: true.

    Raises:
        HTTPException: 404 if document not found.
        HTTPException: 400 if document not processed.
    """
    try:
        # Find document
        result = await db.execute(
            select(CommerceDocument).where(CommerceDocument.id == uuid.UUID(document_id))
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document not found: {document_id}",
            )

        # Check if document is processed
        is_processed = document.extracted_data and len(document.extracted_data) > 0
        if not is_processed:
            raise HTTPException(
                status_code=400,
                detail="Document must be processed before storing. Document has no extracted data.",
            )

        # Mark as stored in metadata
        if not document.processing_metadata:
            document.processing_metadata = {}
        document.processing_metadata["stored"] = True
        await db.commit()

        logger.info(f"Document stored: {document_id}")

        return {"success": True}

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document ID format: {document_id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store document: {str(e)}",
        ) from e


@documents_router.get("/", response_model=DocumentListResponse)
async def list_documents(
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: DBDep = None,  # type: ignore
) -> DocumentListResponse:
    """List documents.

    Lists documents with optional filtering by user_id and pagination.

    Args:
        user_id: User ID to filter by (optional).
        limit: Maximum number of documents to return (default: 50).
        offset: Offset for pagination (default: 0).
        db: Database session.

    Returns:
        DocumentListResponse with documents, total, limit, and offset.

    Raises:
        HTTPException: 400 if parameters are invalid.
    """
    try:
        # Validate parameters
        if limit < 1 or limit > 100:
            raise ValidationException(
                message="Limit must be between 1 and 100",
                details={"limit": limit},
            )

        if offset < 0:
            raise ValidationException(
                message="Offset must be non-negative",
                details={"offset": offset},
            )

        # Build query
        query = select(CommerceDocument)

        # Filter by user_id if provided
        if user_id:
            try:
                user_uuid = uuid.UUID(user_id)
                query = query.where(CommerceDocument.user_id == user_uuid)
            except ValueError:
                raise ValidationException(
                    message="Invalid user_id format",
                    details={"user_id": user_id},
                )

        # Order by created_at DESC
        query = query.order_by(CommerceDocument.created_at.desc())

        # Get total count
        count_query = select(CommerceDocument)
        if user_id:
            count_query = count_query.where(CommerceDocument.user_id == uuid.UUID(user_id))
        total_result = await db.execute(count_query)
        total = len(total_result.scalars().all())

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        documents = result.scalars().all()

        # Format documents
        formatted_documents = []
        for doc in documents:
            # Determine status
            status = "processed" if doc.extracted_data and len(doc.extracted_data) > 0 else "pending"
            if doc.processing_metadata and doc.processing_metadata.get("error"):
                status = "error"
            if doc.processing_metadata and doc.processing_metadata.get("stored"):
                status = "stored"

            formatted_documents.append(
                DocumentResponse(
                    document_id=str(doc.id),
                    filename=doc.file_name,
                    file_type=doc.file_type,
                    status=status,
                    extracted_data=doc.extracted_data,
                    schema_definition=doc.schema_definition,
                    confidence_score=doc.confidence_score,
                    processing_metadata=doc.processing_metadata,
                    created_at=doc.created_at.isoformat() if doc.created_at else None,
                    updated_at=doc.updated_at.isoformat() if doc.updated_at else None,
                )
            )

        return DocumentListResponse(
            documents=formatted_documents,
            total=total,
            limit=limit,
            offset=offset,
        )

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}",
        ) from e

