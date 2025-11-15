# API Endpoints Documentation

Complete documentation for all API endpoints.

## Chat Endpoints

### POST /chat/message

Send a message and receive response from the appropriate agent.

**Implementation**: [backend/app/api/routes/chat.py](../../backend/app/api/routes/chat.py)

**Request Body**:
```json
{
  "query": "How many orders do we have?",
  "thread_id": "thread-123",  // Optional
  "attachment": {              // Optional
    "filename": "document.pdf",
    "content": "base64-encoded-content",
    "mime_type": "application/pdf"
  }
}
```

**Request Schema**: [backend/app/api/schemas/chat.py](../../backend/app/api/schemas/chat.py) - `ChatRequest`

**Response** (200 OK):
```json
{
  "message_id": "msg-456",
  "thread_id": "thread-123",
  "response": {
    "text": "You have 150 orders in total.",
    "agent": "analytics",
    "language": "en-US",
    "citations": [],
    "sql_metadata": {
      "sql": "SELECT COUNT(*) FROM orders",
      "explanation": "Count total orders"
    },
    "performance_metrics": {
      "total_time_ms": 1250.5,
      "generation_time_ms": 800.2,
      "tokens_used": 150
    }
  },
  "language": "en-US",
  "metadata": {
    "sql": {
      "sql": "SELECT COUNT(*) FROM orders",
      "explanation": "Count total orders"
    }
  }
}
```

**Response Schema**: [backend/app/api/schemas/chat.py](../../backend/app/api/schemas/chat.py) - `ChatResponse`

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How many orders do we have?",
    "thread_id": "thread-123"
  }'
```

### GET /chat/history

Get message history for a conversation.

**Implementation**: [backend/app/api/routes/chat.py](../../backend/app/api/routes/chat.py)

**Query Parameters**:
- `thread_id` (required): Thread/conversation ID
- `limit` (optional, default: 50): Maximum number of messages

**Response** (200 OK):
```json
{
  "thread_id": "thread-123",
  "messages": [
    {
      "id": "msg-1",
      "role": "user",
      "content": "How many orders do we have?",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "msg-2",
      "role": "assistant",
      "content": "You have 150 orders in total.",
      "agent": "analytics",
      "created_at": "2024-01-01T12:00:05Z"
    }
  ],
  "total": 2
}
```

**Response Schema**: [backend/app/api/schemas/chat.py](../../backend/app/api/schemas/chat.py) - `ChatHistoryResponse`

**Example**:
```bash
curl "http://localhost:8000/api/v1/chat/history?thread_id=thread-123&limit=50"
```

### DELETE /chat/history/{thread_id}

Clear message history for a conversation.

**Implementation**: [backend/app/api/routes/chat.py](../../backend/app/api/routes/chat.py)

**Path Parameters**:
- `thread_id` (required): Thread/conversation ID

**Response** (200 OK):
```json
{
  "message": "History cleared successfully",
  "thread_id": "thread-123"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/chat/history/thread-123
```

### WebSocket /chat/stream

WebSocket endpoint for real-time response streaming.

**Implementation**: [backend/app/api/routes/chat.py](../../backend/app/api/routes/chat.py) - `stream_chat()`

**Connection**:
```
ws://localhost:8000/api/v1/chat/stream
```

**Send Message**:
```json
{
  "query": "How many orders do we have?",
  "thread_id": "thread-123",
  "language": "en-US"
}
```

**Receive Messages**:
```json
// Status: processing
{
  "status": "processing",
  "message_id": "msg-456",
  "thread_id": "thread-123"
}

// Status: routing
{
  "status": "routing",
  "thread_id": "thread-123"
}

// Status: complete + response
{
  "status": "complete",
  "thread_id": "thread-123",
  "response": {
    "text": "You have 150 orders in total.",
    "agent": "analytics",
    "language": "en-US"
  }
}
```

**JavaScript Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/chat/stream');

ws.onopen = () => {
  ws.send(JSON.stringify({
    query: "How many orders do we have?",
    thread_id: "thread-123"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## Document Endpoints

### POST /documents/upload

Upload a commerce document for processing.

**Implementation**: [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py)

**Request** (multipart/form-data):
- `file` (required): File to upload
- `type` (required): Document type (must be "commerce")

**Supported File Types** (see [backend/app/config/constants.py](../../backend/app/config/constants.py) - `SUPPORTED_FILE_TYPES`):
- PDF: `application/pdf`
- DOCX: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- TXT: `text/plain`
- Images: `image/png`, `image/jpeg`, `image/tiff`

**Maximum Size** (see [backend/app/config/constants.py](../../backend/app/config/constants.py) - `MAX_FILE_SIZE_MB`): 10MB

**Response** (200 OK):
```json
{
  "document_id": "doc-789",
  "filename": "invoice.pdf",
  "file_type": "pdf",
  "file_path": "commerce/2024/01/15/uuid.pdf",
  "status": "processed",
  "extracted_data": {
    "total": 1500.00,
    "date": "2024-01-15",
    "items": [...]
  },
  "schema_definition": {
    "fields": ["total", "date", "items"]
  },
  "confidence_score": 0.95,
  "created_at": "2024-01-15T12:00:00Z",
  "processed_at": "2024-01-15T12:00:05Z"
}
```

**Response Schema**: [backend/app/api/schemas/documents.py](../../backend/app/api/schemas/documents.py) - `DocumentResponse`

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf" \
  -F "type=commerce"
```

The document is processed by the [Commerce Agent](../../backend/app/agents/commerce/agent.py) and stored using [LocalStorage](../../backend/app/infrastructure/storage/local_storage.py).

### GET /documents

List all documents.

**Implementation**: [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py)

**Query Parameters**:
- `limit` (optional, default: 50): Maximum number of documents
- `offset` (optional, default: 0): Offset for pagination
- `status` (optional): Filter by status ("pending", "processing", "processed", "error", "stored")

**Response** (200 OK):
```json
{
  "documents": [
    {
      "document_id": "doc-789",
      "filename": "invoice.pdf",
      "file_type": "pdf",
      "status": "processed",
      "created_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Response Schema**: [backend/app/api/schemas/documents.py](../../backend/app/api/schemas/documents.py) - `DocumentListResponse`

**Example**:
```bash
curl "http://localhost:8000/api/v1/documents?limit=10&status=processed"
```

### GET /documents/{document_id}

Get detailed information about a document.

**Implementation**: [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py)

**Path Parameters**:
- `document_id` (required): Document ID (UUID)

**Response** (200 OK):
```json
{
  "document_id": "doc-789",
  "filename": "invoice.pdf",
  "file_type": "pdf",
  "status": "processed",
  "extracted_data": {
    "total": 1500.00,
    "date": "2024-01-15"
  },
  "schema_definition": {
    "fields": ["total", "date"]
  },
  "confidence_score": 0.95,
  "processing_metadata": {
    "ocr_used": true,
    "processing_time_ms": 2500.0
  },
  "created_at": "2024-01-15T12:00:00Z",
  "processed_at": "2024-01-15T12:00:05Z"
}
```

**Response Schema**: [backend/app/api/schemas/documents.py](../../backend/app/api/schemas/documents.py) - `DocumentResponse`

**Example**:
```bash
curl http://localhost:8000/api/v1/documents/doc-789
```

### DELETE /documents/{document_id}

Delete a document and its associated data.

**Implementation**: [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py)

**Path Parameters**:
- `document_id` (required): Document ID (UUID)

**Response** (200 OK):
```json
{
  "message": "Document deleted successfully",
  "document_id": "doc-789"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/documents/doc-789
```

### POST /documents/{document_id}/analyze

Re-analyze an existing document.

**Implementation**: [backend/app/api/routes/documents.py](../../backend/app/api/routes/documents.py)

**Path Parameters**:
- `document_id` (required): Document ID (UUID)

**Response** (200 OK):
```json
{
  "document_id": "doc-789",
  "status": "processed",
  "extracted_data": {...},
  "confidence_score": 0.95,
  "processed_at": "2024-01-15T12:10:00Z"
}
```

**Response Schema**: [backend/app/api/schemas/documents.py](../../backend/app/api/schemas/documents.py) - `DocumentResponse`

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/documents/doc-789/analyze
```

This re-processes the document using the [Commerce Agent](../../backend/app/agents/commerce/agent.py).

## Health Endpoints

### GET /health

Basic health check. Returns "ok" if the application is running.

**Implementation**: [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py)

**Response** (200 OK):
```json
{
  "status": "ok"
}
```

**Response Schema**: [backend/app/api/schemas/health.py](../../backend/app/api/schemas/health.py) - `HealthResponse`

**Example**:
```bash
curl http://localhost:8000/api/v1/health
```

### GET /health/ready

Readiness check. Verifies that all critical dependencies are available.

**Implementation**: [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py)

**Response** (200 OK):
```json
{
  "status": "ready",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "llm": "ok"
  }
}
```

**Response** (503 Service Unavailable):
```json
{
  "status": "not_ready",
  "checks": {
    "database": "error",
    "cache": "optional",
    "llm": "ok"
  }
}
```

**Response Schema**: [backend/app/api/schemas/health.py](../../backend/app/api/schemas/health.py) - `ReadinessResponse`

**Example**:
```bash
curl http://localhost:8000/api/v1/health/ready
```

### GET /health/live

Liveness check. Returns "alive" if the application is running.

**Implementation**: [backend/app/api/routes/health.py](../../backend/app/api/routes/health.py)

**Response** (200 OK):
```json
{
  "status": "alive"
}
```

**Response Schema**: [backend/app/api/schemas/health.py](../../backend/app/api/schemas/health.py) - `LivenessResponse`

**Example**:
```bash
curl http://localhost:8000/api/v1/health/live
```

## Error Codes

### 400 Bad Request

Invalid request (missing parameters, incorrect format).

**Exception**: [backend/app/config/exceptions.py](../../backend/app/config/exceptions.py) - `ValidationException`

```json
{
  "message": "Query cannot be empty",
  "details": {
    "query": ""
  }
}
```

### 404 Not Found

Resource not found.

```json
{
  "message": "Document not found",
  "details": {
    "document_id": "doc-999"
  }
}
```

### 422 Unprocessable Entity

Validation error (Pydantic).

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Internal server error.

```json
{
  "message": "Internal server error",
  "details": {
    "error": "Error message"
  }
}
```

## Complete Examples

### Complete Chat Flow

```bash
# 1. Send message
THREAD_ID=$(curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"query": "How many orders do we have?"}' \
  | jq -r '.thread_id')

# 2. Get history
curl "http://localhost:8000/api/v1/chat/history?thread_id=$THREAD_ID"

# 3. Send another message in the same thread
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is the total value?\", \"thread_id\": \"$THREAD_ID\"}"
```

The chat flow uses the LangGraph graph defined in [backend/app/graph/build.py](../../backend/app/graph/build.py) to route and process messages.

### Complete Document Flow

```bash
# 1. Upload
DOC_ID=$(curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf" \
  -F "type=commerce" \
  | jq -r '.document_id')

# 2. Check status
curl "http://localhost:8000/api/v1/documents/$DOC_ID"

# 3. Re-analyze
curl -X POST "http://localhost:8000/api/v1/documents/$DOC_ID/analyze"

# 4. Delete
curl -X DELETE "http://localhost:8000/api/v1/documents/$DOC_ID"
```

---

**← [Back to Documentation Index](../README.md)**
