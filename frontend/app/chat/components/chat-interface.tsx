/**
 * Chat interface component (main chat container with WebSocket streaming).
 *
 * Overview
 *   Main container component for the chat interface. Manages message state,
 *   WebSocket connection for streaming, and API integration for message sending
 *   and history. Handles loading states, errors, and real-time message updates.
 *
 * Design
 *   - **State Management**: Uses useState for messages and thread ID.
 *   - **WebSocket Streaming**: Uses useWebSocket hook for real-time streaming.
 *   - **API Integration**: Uses chat API client for REST endpoints.
 *   - **Message Persistence**: Loads and saves message history.
 *   - **Error Handling**: Displays error messages to user.
 *
 * Integration
 *   - Consumes: useWebSocket hook, chat API client, MessageList, MessageInput.
 *   - Returns: Rendered chat interface component.
 *   - Used by: Chat page (app/chat/page.tsx).
 *   - Observability: Logs errors and connection status.
 *
 * Usage
 *   >>> <ChatInterface />
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";

import { useWebSocket } from "@/lib/hooks/use-websocket";
import { sendMessage, getChatHistory, clearChatHistory } from "@/lib/api/chat";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import type { ChatResponse, Message } from "@/types/chat";

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((data: unknown) => {
    try {
      // Handle streaming message updates
      if (typeof data === "object" && data !== null) {
        const messageData = data as Partial<ChatResponse>;
        if (messageData.response) {
          // Update or add assistant message
          setMessages((prev) => {
            const existingIndex = prev.findIndex(
              (msg) => msg.message_id === messageData.message_id
            );

            if (existingIndex >= 0) {
              // Update existing message
              const updated = [...prev];
              updated[existingIndex] = {
                ...updated[existingIndex],
                content: messageData.response.text,
                answer: messageData.response,
              };
              return updated;
            } else {
              // Add new message
              return [
                ...prev,
                {
                  message_id: messageData.message_id || generateUUID(),
                  role: "assistant",
                  content: messageData.response.text,
                  agent: messageData.response.agent,
                  created_at: new Date().toISOString(),
                  answer: messageData.response,
                },
              ];
            }
          });
        }
      }
    } catch (err) {
      console.error("Error handling WebSocket message:", err);
    }
  }, []);

  // WebSocket error handler
  const handleWebSocketError = useCallback((error: Error) => {
    console.error("WebSocket error:", error);
    setError(`Connection error: ${error.message}`);
  }, []);

  // Initialize WebSocket connection
  const { send: sendWebSocket, connected } = useWebSocket(
    undefined, // Use default URL from env
    handleWebSocketMessage,
    handleWebSocketError
  );

  // Load chat history on mount or threadId change
  useEffect(() => {
    if (threadId) {
      getChatHistory(threadId)
        .then((history) => {
          const formattedMessages: Message[] = history.messages.map((msg) => ({
            message_id: msg.message_id,
            role: msg.role,
            content: msg.content,
            agent: msg.agent as Message["agent"],
            created_at: msg.created_at,
          }));
          setMessages(formattedMessages);
        })
        .catch((err) => {
          console.error("Error loading chat history:", err);
          setError(`Failed to load chat history: ${err.message}`);
        });
    }
  }, [threadId]);

  // Handle message send
  const handleSend = useCallback(
    async (query: string, file?: File) => {
      if (!query.trim() && !file) return;

      setIsLoading(true);
      setError(null);

      try {
        // Generate thread ID if not exists
        const currentThreadId = threadId || generateUUID();
        if (!threadId) {
          setThreadId(currentThreadId);
        }

        // Add user message to UI immediately
        const userMessage: Message = {
          message_id: generateUUID(),
          role: "user",
          content: query,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, userMessage]);

        // Send via REST API (for now, WebSocket will be used for streaming in future)
        const response = await sendMessage(query, currentThreadId, file);

        // Add assistant response
        const assistantMessage: Message = {
          message_id: response.message_id,
          role: "assistant",
          content: response.response.text,
          agent: response.response.agent,
          created_at: new Date().toISOString(),
          answer: response.response,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        console.error("Error sending message:", err);
        setError(
          err instanceof Error ? err.message : "Failed to send message"
        );
        // Remove user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setIsLoading(false);
      }
    },
    [threadId]
  );

  // Handle clear history
  const handleClearHistory = useCallback(async () => {
    if (!threadId) return;

    try {
      await clearChatHistory(threadId);
      setMessages([]);
      setThreadId(null);
      setError(null);
    } catch (err) {
      console.error("Error clearing history:", err);
      setError(
        err instanceof Error ? err.message : "Failed to clear history"
      );
    }
  }, [threadId]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <h1 className="text-xl font-semibold">Chat</h1>
        <div className="flex items-center gap-2">
          {connected ? (
            <span className="text-xs text-muted-foreground">Connected</span>
          ) : (
            <span className="text-xs text-destructive">Disconnected</span>
          )}
          {threadId && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClearHistory}
              disabled={isLoading}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear
            </Button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 text-destructive px-4 py-2 text-sm">
          {error}
        </div>
      )}

      {/* Message List */}
      <MessageList messages={messages} threadId={threadId || ""} />

      {/* Message Input */}
      <MessageInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}

