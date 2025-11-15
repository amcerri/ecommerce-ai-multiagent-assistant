# API Documentation

Complete documentation for the REST API and WebSocket endpoints of the E-Commerce AI Multi-Agent Assistant.

## Overview

The API provides endpoints for:

- **Chat**: Message sending, conversation history, WebSocket streaming
- **Documents**: Upload and processing of commerce documents
- **Health**: Health checks, readiness, and liveness

**API Implementation**: [backend/app/api/main.py](../../backend/app/api/main.py)

## Base URL

```text
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. Authentication will be implemented in future versions.

## Interactive Documentation

The API includes interactive documentation via Swagger UI:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### Chat

- **[POST /chat/message](endpoints.md#post-chatmessage)**: Send message - [Implementation](../../backend/app/api/routes/chat.py)
- **[GET /chat/history](endpoints.md#get-chathistory)**: Get conversation history - [Implementation](../../backend/app/api/routes/chat.py)
- **[DELETE /chat/history/{thread_id}](endpoints.md#delete-chathistorythread_id)**: Clear history - [Implementation](../../backend/app/api/routes/chat.py)
- **[WebSocket /chat/stream](endpoints.md#websocket-chatstream)**: Streaming messages - [Implementation](../../backend/app/api/routes/chat.py)

### Documents

- **[POST /documents/upload](endpoints.md#post-documentsupload)**: Upload document - [Implementation](../../backend/app/api/routes/documents.py)
- **[GET /documents](endpoints.md#get-documents)**: List documents - [Implementation](../../backend/app/api/routes/documents.py)
- **[GET /documents/{document_id}](endpoints.md#get-documentsdocument_id)**: Get document - [Implementation](../../backend/app/api/routes/documents.py)
- **[DELETE /documents/{document_id}](endpoints.md#delete-documentsdocument_id)**: Delete document - [Implementation](../../backend/app/api/routes/documents.py)
- **[POST /documents/{document_id}/analyze](endpoints.md#post-documentsdocument_idanalyze)**: Analyze document - [Implementation](../../backend/app/api/routes/documents.py)

### Health

- **[GET /health](endpoints.md#get-health)**: Basic health check - [Implementation](../../backend/app/api/routes/health.py)
- **[GET /health/ready](endpoints.md#get-healthready)**: Readiness check - [Implementation](../../backend/app/api/routes/health.py)
- **[GET /health/live](endpoints.md#get-healthlive)**: Liveness check - [Implementation](../../backend/app/api/routes/health.py)

## Schemas

All endpoints use Pydantic schemas for validation:

- **Chat Schemas**: [backend/app/api/schemas/chat.py](../../backend/app/api/schemas/chat.py)
- **Document Schemas**: [backend/app/api/schemas/documents.py](../../backend/app/api/schemas/documents.py)
- **Health Schemas**: [backend/app/api/schemas/health.py](../../backend/app/api/schemas/health.py)

See [Endpoints](endpoints.md) for complete request/response details.

## Error Codes

- **200 OK**: Success
- **400 Bad Request**: Invalid request
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Internal server error

Error handling is implemented in [backend/app/config/exceptions.py](../../backend/app/config/exceptions.py).

## Rate Limiting

The API implements rate limiting (see [backend/app/config/constants.py](../../backend/app/config/constants.py) - `RATE_LIMITS`):

- **Per user**: 100 requests per hour
- **Per IP**: 1000 requests per hour
- **LLM calls**: 50 calls per user per hour

## Detailed Documentation

See [Endpoints](endpoints.md) for complete documentation of all endpoints with examples.

---

**← [Back to Documentation Index](../README.md)**
