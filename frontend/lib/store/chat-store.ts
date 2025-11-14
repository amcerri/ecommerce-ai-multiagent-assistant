/**
 * Chat store (Zustand store for chat state management).
 *
 * Overview
 *   Manages global chat state including messages, thread ID, loading states,
 *   errors, and streaming status. Persists thread ID to localStorage and
 *   provides actions for message management.
 *
 * Design
 *   - **State Management**: Uses Zustand for global state.
 *   - **Persistence**: Persists threadId to localStorage.
 *   - **Actions**: Add/clear messages, set loading/error states.
 *   - **Selectors**: Get messages by thread, get last message.
 *
 * Integration
 *   - Consumes: Message types from @/types/chat.
 *   - Returns: Zustand store hook (useChatStore).
 *   - Used by: ChatInterface and message components.
 *   - Observability: N/A (state management only).
 *
 * Usage
 *   >>> const { messages, addMessage, setThreadId } = useChatStore();
 *   >>> addMessage(newMessage);
 *   >>> setThreadId("thread-123");
 */

"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { Message } from "@/types/chat";

interface ChatState {
  // State
  messages: Message[];
  threadId: string | null;
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;

  // Actions
  addMessage: (message: Message) => void;
  setMessages: (messages: Message[]) => void;
  setThreadId: (threadId: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setStreaming: (streaming: boolean) => void;
  clearMessages: () => void;
  clearError: () => void;

  // Selectors (computed)
  getMessagesByThread: (threadId: string) => Message[];
  getLastMessage: () => Message | undefined;
}

const STORAGE_KEY = "chat-store";

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      // Initial state
      messages: [],
      threadId: null,
      isLoading: false,
      error: null,
      isStreaming: false,

      // Actions
      addMessage: (message: Message) => {
        set((state) => ({
          messages: [...state.messages, message],
        }));
      },

      setMessages: (messages: Message[]) => {
        set({ messages });
      },

      setThreadId: (threadId: string | null) => {
        set({ threadId });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setStreaming: (streaming: boolean) => {
        set({ isStreaming: streaming });
      },

      clearMessages: () => {
        set({ messages: [] });
      },

      clearError: () => {
        set({ error: null });
      },

      // Selectors
      getMessagesByThread: (threadId: string) => {
        const state = get();
        return state.messages.filter(
          (msg) => msg.role === "user" || msg.role === "assistant"
        );
        // Note: In a real implementation, messages would be filtered by threadId
        // For now, we return all messages since threadId is managed at store level
      },

      getLastMessage: () => {
        const state = get();
        return state.messages[state.messages.length - 1];
      },
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({
        // Only persist threadId, not messages (too large)
        threadId: state.threadId,
      }),
    }
  )
);

