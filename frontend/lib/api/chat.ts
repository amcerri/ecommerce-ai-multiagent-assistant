/**
 * Chat API client (HTTP client for chat endpoints).
 *
 * Overview
 *   Provides functions for interacting with chat API endpoints. Handles
 *   message sending, history retrieval, and history deletion. Uses axios
 *   for HTTP requests with proper error handling.
 *
 * Design
 *   - **REST API**: Uses axios for HTTP requests.
 *   - **Error Handling**: Converts HTTP errors to TypeScript errors.
 *   - **Type Safety**: Full TypeScript types matching backend schemas.
 *   - **Base URL**: Reads from NEXT_PUBLIC_API_URL environment variable.
 *
 * Integration
 *   - Consumes: Backend API endpoints (/api/v1/chat/*).
 *   - Returns: Typed responses (ChatResponse, ChatHistoryResponse).
 *   - Used by: Chat components and hooks.
 *   - Observability: Error logging for failed requests.
 *
 * Usage
 *   >>> import { sendMessage, getChatHistory } from "@/lib/api/chat";
 *   >>> const response = await sendMessage("Hello", "thread-123");
 *   >>> const history = await getChatHistory("thread-123");
 */

import axios, { AxiosError } from "axios";

import type {
  ChatHistoryResponse,
  ChatRequest,
  ChatResponse,
} from "@/types/chat";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Send chat message via REST API.
 *
 * Sends a message to the chat API and returns the response. Supports
 * optional thread ID for conversation continuity and optional file attachment
 * for commerce document processing.
 *
 * @param query - User query text.
 * @param threadId - Optional conversation thread ID.
 * @param attachment - Optional file attachment.
 * @returns Promise resolving to ChatResponse.
 * @throws Error if request fails.
 */
export async function sendMessage(
  query: string,
  threadId?: string,
  attachment?: File
): Promise<ChatResponse> {
  try {
    // If attachment is provided, use FormData
    if (attachment) {
      const formData = new FormData();
      formData.append("query", query);

      if (threadId) {
        formData.append("thread_id", threadId);
      }

      formData.append("file", attachment);

      const response = await apiClient.post<ChatResponse>(
        "/chat/message",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      return response.data;
    } else {
      // Otherwise, use JSON
      const requestBody: ChatRequest = {
        query,
        thread_id: threadId,
      };

      const response = await apiClient.post<ChatResponse>(
        "/chat/message",
        requestBody
      );

      return response.data;
    }
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      throw new Error(
        axiosError.response?.data?.detail ||
          `Failed to send message: ${axiosError.message}`
      );
    }
    throw new Error(`Failed to send message: ${String(error)}`);
  }
}

/**
 * Get chat history for a conversation thread.
 *
 * Retrieves message history for a specific thread with optional pagination.
 *
 * @param threadId - Conversation thread ID.
 * @param limit - Optional limit for number of messages (default: 50).
 * @returns Promise resolving to ChatHistoryResponse.
 * @throws Error if request fails.
 */
export async function getChatHistory(
  threadId: string,
  limit: number = 50
): Promise<ChatHistoryResponse> {
  try {
    const response = await apiClient.get<ChatHistoryResponse>(
      "/chat/history",
      {
        params: {
          thread_id: threadId,
          limit,
        },
      }
    );

    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      throw new Error(
        axiosError.response?.data?.detail ||
          `Failed to get chat history: ${axiosError.message}`
      );
    }
    throw new Error(`Failed to get chat history: ${String(error)}`);
  }
}

/**
 * Clear chat history for a conversation thread.
 *
 * Deletes all messages and conversation record for a thread.
 *
 * @param threadId - Conversation thread ID.
 * @returns Promise resolving to void.
 * @throws Error if request fails.
 */
export async function clearChatHistory(threadId: string): Promise<void> {
  try {
    await apiClient.delete("/chat/history", {
      params: {
        thread_id: threadId,
      },
    });
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<{ detail: string }>;
      throw new Error(
        axiosError.response?.data?.detail ||
          `Failed to clear chat history: ${axiosError.message}`
      );
    }
    throw new Error(`Failed to clear chat history: ${String(error)}`);
  }
}

