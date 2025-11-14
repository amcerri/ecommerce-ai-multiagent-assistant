/**
 * Message list component (scrollable list of messages with auto-scroll).
 *
 * Overview
 *   Displays a scrollable list of messages with automatic scrolling to the
 *   latest message. Uses ScrollArea component for smooth scrolling and
 *   performance optimization. Supports virtual scrolling for large message lists.
 *
 * Design
 *   - **Scroll Area**: Uses shadcn/ui ScrollArea for smooth scrolling.
 *   - **Auto-scroll**: Automatically scrolls to bottom when new messages arrive.
 *   - **Virtual Scrolling**: Optional virtual scrolling for performance (future enhancement).
 *   - **Animations**: Fade-in animations for new messages.
 *
 * Integration
 *   - Consumes: Array of Message objects and thread ID.
 *   - Returns: Rendered scrollable message list.
 *   - Used by: ChatInterface component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <MessageList messages={messages} threadId={threadId} />
 */

"use client";

import { useEffect, useRef } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import type { Message } from "@/types/chat";

interface MessageListProps {
  messages: Message[];
  threadId: string;
}

export function MessageList({ messages, threadId }: MessageListProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <p>No messages yet. Start a conversation!</p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 h-full">
      <div ref={scrollRef} className="p-4 space-y-4">
        {messages.map((message) => (
          <MessageBubble
            key={message.message_id}
            message={message}
            isUser={message.role === "user"}
          />
        ))}
      </div>
    </ScrollArea>
  );
}

