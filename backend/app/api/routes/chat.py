"""
Chat API routes (REST and WebSocket endpoints for chat).

Overview
  Provides REST and WebSocket endpoints for chat interactions. Handles message
  sending, response streaming, and conversation history management. Integrates
  with LangGraph for message processing and persists messages in the database.

Design
  - **REST Endpoints**: POST /message, GET /history, DELETE /history.
  - **WebSocket Endpoint**: /stream for real-time streaming.
  - **LangGraph Integration**: Uses assistant.invoke() for message processing.
  - **Message Persistence**: Saves all messages to database for history.
  - **Thread Management**: Generates thread_id automatically if not provided.

Integration
  - Consumes: LangGraph assistant, database models, dependencies.
  - Returns: ChatResponse, ChatHistoryResponse, WebSocket messages.
  - Used by: Frontend Next.js application.
  - Observability: Logs all requests, responses, and errors.

Usage
  >>> POST /api/v1/chat/message
  >>> {"query": "How many orders?", "thread_id": "..."}
  >>> {"message_id": "...", "thread_id": "...", "response": {...}}
"""

import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AssistantDep, DBDep, LanguageDetectorDep
from app.api.schemas.chat import ChatHistoryResponse, ChatRequest, ChatResponse
from app.config.exceptions import ValidationException
from app.graph.state import GraphState
from app.infrastructure.database.models.conversation import Conversation, Message

logger = logging.getLogger(__name__)

# Create router
chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("/message", response_model=ChatResponse)
async def send_message(
    request_body: ChatRequest,
    request: Request,
    db: DBDep,
    assistant: AssistantDep,
    language_detector: LanguageDetectorDep,
) -> ChatResponse:
    """Send chat message and get response.

    Processes user message through LangGraph and returns agent response.
    Saves message and response to database for history.

    Args:
        request_body: Chat request with query and optional thread_id.
        request: FastAPI request (for language detection).
        db: Database session.
        assistant: LangGraph assistant instance.
        language_detector: Language detector instance.

    Returns:
        ChatResponse with message_id, thread_id, response, language, metadata.

    Raises:
        ValidationException: If request is invalid.
        HTTPException: If processing fails.
    """
    try:
        # Step 1: Validate request
        if not request_body.query or not request_body.query.strip():
            raise ValidationException(
                message="Query cannot be empty",
                details={"query": request_body.query},
            )

        # Step 2: Detect language
        language = getattr(request.state, "language", None)
        if not language:
            # Fallback: detect from request
            ip_address = request.client.host if request.client else None
            accept_language = request.headers.get("Accept-Language")
            language = await language_detector.detect(ip_address, accept_language)

        # Step 3: Generate IDs
        message_id = str(uuid.uuid4())
        thread_id = request_body.thread_id or str(uuid.uuid4())

        # Step 4: Load conversation history if thread_id exists
        conversation_history: List[Dict[str, Any]] = []
        if request_body.thread_id:
            # Check if conversation exists
            result = await db.execute(
                select(Conversation).where(Conversation.thread_id == thread_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                # Load messages
                messages_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc())
                )
                messages = messages_result.scalars().all()

                # Build conversation history
                for msg in messages:
                    conversation_history.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        }
                    )

        # Step 5: Create GraphState
        state: GraphState = {
            "thread_id": thread_id,
            "user_id": None,  # TODO: Get from authentication when implemented
            "query": request_body.query,
            "language": language,
            "conversation_history": conversation_history,
            "router_decision": None,
            "agent_response": None,
            "metadata": {},
            "interrupts": {},
        }

        # Step 6: Execute graph
        logger.info(
            f"Processing message: {message_id} in thread: {thread_id}",
            extra={"message_id": message_id, "thread_id": thread_id, "query": request_body.query[:100]},
        )

        # Invoke LangGraph (use ainvoke if available, otherwise invoke)
        if hasattr(assistant, "ainvoke"):
            final_state = await assistant.ainvoke(state)
        else:
            # Fallback for sync invoke (shouldn't happen, but graceful degradation)
            import asyncio
            final_state = await asyncio.to_thread(assistant.invoke, state)

        # Step 7: Get response from state
        agent_response = final_state.get("agent_response")
        if not agent_response:
            raise ValidationException(
                message="No response generated from agent",
                details={"thread_id": thread_id, "message_id": message_id},
            )

        # Step 8: Save messages to database
        try:
            # Get or create conversation
            result = await db.execute(
                select(Conversation).where(Conversation.thread_id == thread_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                conversation = Conversation(
                    thread_id=thread_id,
                    user_id=None,  # TODO: Get from authentication
                )
                db.add(conversation)
                await db.flush()  # Get conversation.id

            # Save user message
            user_message = Message(
                conversation_id=conversation.id,
                role="user",
                content=request_body.query,
                message_id=message_id,
            )
            db.add(user_message)

            # Save agent response
            agent_message_id = str(uuid.uuid4())
            agent_message = Message(
                conversation_id=conversation.id,
                role="assistant",
                content=agent_response.text if hasattr(agent_response, "text") else str(agent_response),
                message_id=agent_message_id,
                meta={"agent": agent_response.agent if hasattr(agent_response, "agent") else None},
            )
            db.add(agent_message)

            await db.commit()

        except Exception as e:
            logger.error(f"Failed to save messages to database: {e}", exc_info=True)
            await db.rollback()
            # Continue even if save fails (graceful degradation)

        # Step 9: Create response
        metadata: Dict[str, Any] = {}
        if hasattr(agent_response, "citations") and agent_response.citations:
            metadata["citations"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in agent_response.citations]
        if hasattr(agent_response, "sql_metadata") and agent_response.sql_metadata:
            metadata["sql"] = agent_response.sql_metadata.model_dump() if hasattr(agent_response.sql_metadata, "model_dump") else agent_response.sql_metadata
        if hasattr(agent_response, "performance_metrics") and agent_response.performance_metrics:
            metadata["performance"] = agent_response.performance_metrics.model_dump() if hasattr(agent_response.performance_metrics, "model_dump") else agent_response.performance_metrics

        response = ChatResponse(
            message_id=message_id,
            thread_id=thread_id,
            response=agent_response.model_dump() if hasattr(agent_response, "model_dump") else agent_response,
            language=language,
            metadata=metadata if metadata else None,
        )

        logger.info(
            f"Message processed successfully: {message_id}",
            extra={"message_id": message_id, "thread_id": thread_id, "agent": agent_response.agent if hasattr(agent_response, "agent") else None},
        )

        return response

    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise ValidationException(
            message="Failed to process message",
            details={"error": str(e)},
        ) from e


@chat_router.websocket("/stream")
async def stream_chat(
    websocket: WebSocket,
    db: DBDep,
    assistant: AssistantDep,
    language_detector: LanguageDetectorDep,
) -> None:
    """WebSocket endpoint for streaming chat responses.

    Processes messages and streams responses in real-time via WebSocket.
    Sends status updates and incremental response chunks.

    Args:
        websocket: WebSocket connection.
    """
    from app.api.dependencies import get_db, get_assistant, get_language_detector

    await websocket.accept()

    # Get dependencies (WebSocket doesn't support Depends, so we get them manually)
    db_gen = get_db()
    db = await db_gen.__anext__()
    assistant = get_assistant()
    language_detector = get_language_detector()

    try:
        # Receive initial message
        data = await websocket.receive_text()
        request_data = json.loads(data)

        query = request_data.get("query", "")
        thread_id = request_data.get("thread_id") or str(uuid.uuid4())
        language = request_data.get("language", "pt-BR")

        if not query:
            await websocket.send_json({"error": "Query cannot be empty"})
            await websocket.close()
            return

        # Generate message ID
        message_id = str(uuid.uuid4())

        # Send status: processing
        await websocket.send_json({"status": "processing", "message_id": message_id, "thread_id": thread_id})

        # Load conversation history
        conversation_history: List[Dict[str, Any]] = []
        if request_data.get("thread_id"):
            result = await db.execute(
                select(Conversation).where(Conversation.thread_id == thread_id)
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                messages_result = await db.execute(
                    select(Message)
                    .where(Message.conversation_id == conversation.id)
                    .order_by(Message.created_at.asc())
                )
                messages = messages_result.scalars().all()

                for msg in messages:
                    conversation_history.append(
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        }
                    )

        # Create GraphState
        state: GraphState = {
            "thread_id": thread_id,
            "user_id": None,
            "query": query,
            "language": language,
            "conversation_history": conversation_history,
            "router_decision": None,
            "agent_response": None,
            "metadata": {},
            "interrupts": {},
        }

        # Send status: routing
        await websocket.send_json({"status": "routing", "thread_id": thread_id})

        # Execute graph (use ainvoke if available, otherwise invoke)
        if hasattr(assistant, "ainvoke"):
            final_state = await assistant.ainvoke(state)
        else:
            # Fallback for sync invoke
            import asyncio
            final_state = await asyncio.to_thread(assistant.invoke, state)

        # Send status: complete
        await websocket.send_json({"status": "complete", "thread_id": thread_id})

        # Get response
        agent_response = final_state.get("agent_response")
        if agent_response:
            # Send response
            response_data = {
                "message_id": message_id,
                "thread_id": thread_id,
                "response": agent_response.model_dump() if hasattr(agent_response, "model_dump") else agent_response,
                "language": language,
            }
            await websocket.send_json(response_data)

            # Save messages (similar to POST endpoint)
            try:
                result = await db.execute(
                    select(Conversation).where(Conversation.thread_id == thread_id)
                )
                conversation = result.scalar_one_or_none()

                if not conversation:
                    conversation = Conversation(thread_id=thread_id, user_id=None)
                    db.add(conversation)
                    await db.flush()

                user_message = Message(
                    conversation_id=conversation.id,
                    role="user",
                    content=query,
                    message_id=message_id,
                )
                db.add(user_message)

                agent_message = Message(
                    conversation_id=conversation.id,
                    role="assistant",
                    content=agent_response.text if hasattr(agent_response, "text") else str(agent_response),
                    message_id=str(uuid.uuid4()),
                    meta={"agent": agent_response.agent if hasattr(agent_response, "agent") else None},
                )
                db.add(agent_message)

                await db.commit()
            except Exception as e:
                logger.error(f"Failed to save messages: {e}", exc_info=True)
                await db.rollback()

        await websocket.close()

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({"error": "Internal server error"})
            await websocket.close()
        except Exception:
            pass
    finally:
        # Close database session
        try:
            await db_gen.aclose()
        except Exception:
            pass


@chat_router.get("/history", response_model=ChatHistoryResponse)
async def get_history(
    thread_id: str,
    db: DBDep,
    limit: int = 50,
) -> ChatHistoryResponse:
    """Get conversation history.

    Retrieves message history for a conversation thread.

    Args:
        thread_id: Conversation thread ID.
        limit: Maximum number of messages to return (default: 50).

    Returns:
        ChatHistoryResponse with thread_id, messages, and total count.

    Raises:
        ValidationException: If thread_id not provided or thread not found.
    """
    if not thread_id:
        raise ValidationException(
            message="thread_id is required",
            details={"thread_id": thread_id},
        )

    # Find conversation
    result = await db.execute(
        select(Conversation).where(Conversation.thread_id == thread_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ValidationException(
            message="Conversation not found",
            details={"thread_id": thread_id},
        )

    # Get messages
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = messages_result.scalars().all()

    # Format messages
    formatted_messages = []
    for msg in messages:
        formatted_messages.append(
            {
                "message_id": msg.message_id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "metadata": msg.meta if msg.meta else {},
            }
        )

    # Get total count
    total_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    total = len(total_result.scalars().all())

    return ChatHistoryResponse(
        thread_id=thread_id,
        messages=formatted_messages,
        total=total,
        limit=limit,
    )


@chat_router.delete("/history")
async def delete_history(
    thread_id: str,
    db: DBDep,
) -> Dict[str, bool]:
    """Delete conversation history.

    Deletes all messages and conversation record for a thread.

    Args:
        thread_id: Conversation thread ID.

    Returns:
        JSON with success: true.

    Raises:
        ValidationException: If thread_id not provided or thread not found.
    """
    if not thread_id:
        raise ValidationException(
            message="thread_id is required",
            details={"thread_id": thread_id},
        )

    # Find conversation
    result = await db.execute(
        select(Conversation).where(Conversation.thread_id == thread_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise ValidationException(
            message="Conversation not found",
            details={"thread_id": thread_id},
        )

    # Delete messages
    await db.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    messages_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation.id)
    )
    messages = messages_result.scalars().all()
    for msg in messages:
        await db.delete(msg)

    # Delete conversation
    await db.delete(conversation)
    await db.commit()

    return {"success": True}

