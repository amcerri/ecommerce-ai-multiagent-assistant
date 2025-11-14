/**
 * WebSocket hook (React hook for WebSocket connection and streaming).
 *
 * Overview
 *   Provides a React hook for managing WebSocket connections using socket.io-client.
 *   Handles connection, reconnection, message sending, and cleanup. Designed for
 *   real-time chat streaming from the backend.
 *
 * Design
 *   - **Socket.IO**: Uses socket.io-client for WebSocket connection.
 *   - **Auto-reconnect**: Automatically reconnects on disconnect.
 *   - **Message Handling**: Calls onMessage callback when messages are received.
 *   - **Error Handling**: Calls onError callback on connection errors.
 *   - **Cleanup**: Properly disconnects on component unmount.
 *
 * Integration
 *   - Consumes: WebSocket URL from NEXT_PUBLIC_WS_URL environment variable.
 *   - Returns: send function, connected status, disconnect function.
 *   - Used by: ChatInterface component for real-time streaming.
 *   - Observability: Logs connection status and errors.
 *
 * Usage
 *   >>> const { send, connected, disconnect } = useWebSocket(
 *   ...   "ws://localhost:8000",
 *   ...   (data) => console.log("Message:", data),
 *   ...   (error) => console.error("Error:", error)
 *   ... );
 *   >>> send({ query: "Hello", thread_id: "..." });
 */

"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { io, Socket } from "socket.io-client";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export interface UseWebSocketReturn {
  send: (data: unknown) => void;
  connected: boolean;
  disconnect: () => void;
}

/**
 * React hook for WebSocket connection and streaming.
 *
 * Manages Socket.IO connection with automatic reconnection, message handling,
 * and cleanup. Provides send function for sending messages and connected status
 * for UI feedback.
 *
 * @param url - WebSocket URL (optional, defaults to NEXT_PUBLIC_WS_URL).
 * @param onMessage - Callback called when message is received.
 * @param onError - Optional callback called on connection errors.
 * @returns Object with send function, connected status, and disconnect function.
 */
export function useWebSocket(
  url: string = WS_BASE_URL,
  onMessage: (data: unknown) => void,
  onError?: (error: Error) => void
): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onErrorRef.current = onError;
  }, [onMessage, onError]);

  // Initialize socket connection
  useEffect(() => {
    // Create socket connection
    const socket = io(url, {
      transports: ["websocket"],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    socketRef.current = socket;

    // Connection event handlers
    socket.on("connect", () => {
      setConnected(true);
    });

    socket.on("disconnect", () => {
      setConnected(false);
    });

    socket.on("connect_error", (error: Error) => {
      setConnected(false);
      if (onErrorRef.current) {
        onErrorRef.current(error);
      }
    });

    // Message event handler
    socket.on("message", (data: unknown) => {
      if (onMessageRef.current) {
        onMessageRef.current(data);
      }
    });

    // Error event handler
    socket.on("error", (error: Error) => {
      if (onErrorRef.current) {
        onErrorRef.current(error);
      }
    });

    // Cleanup on unmount
    return () => {
      socket.disconnect();
      socketRef.current = null;
      setConnected(false);
    };
  }, [url]);

  // Send function
  const send = useCallback(
    (data: unknown) => {
      if (socketRef.current && connected) {
        socketRef.current.emit("message", data);
      } else {
        if (onErrorRef.current) {
          onErrorRef.current(
            new Error("Cannot send message: WebSocket not connected")
          );
        }
      }
    },
    [connected]
  );

  // Disconnect function
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setConnected(false);
    }
  }, []);

  return { send, connected, disconnect };
}

