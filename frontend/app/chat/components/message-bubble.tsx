/**
 * Message bubble component (user or assistant message bubble).
 *
 * Overview
 *   Displays a message bubble with different styling for user and assistant
 *   messages. Includes avatar, content, timestamp, and agent badge for assistant
 *   messages. Uses date-fns for relative time formatting.
 *
 * Design
 *   - **User Messages**: Right-aligned, blue background, user avatar.
 *   - **Assistant Messages**: Left-aligned, gray background, assistant avatar.
 *   - **Agent Badges**: Color-coded badges for different agents.
 *   - **Timestamps**: Relative time ("há 2 minutos") with absolute time on hover.
 *
 * Integration
 *   - Consumes: Message object with content, role, agent, timestamp.
 *   - Returns: Rendered message bubble component.
 *   - Used by: MessageList component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <MessageBubble message={message} isUser={message.role === "user"} />
 */

"use client";

import { formatDistanceToNow } from "date-fns";
import { ptBR, enUS } from "date-fns/locale";
import { User, Bot } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { MessageContent } from "./message-content";
import type { Message } from "@/types/chat";

interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
}

const agentColors: Record<
  "knowledge" | "analytics" | "commerce" | "triage",
  "default" | "secondary" | "destructive" | "outline"
> = {
  knowledge: "default",
  analytics: "secondary",
  commerce: "destructive",
  triage: "outline",
};

const agentLabels: Record<
  "knowledge" | "analytics" | "commerce" | "triage",
  string
> = {
  knowledge: "Knowledge",
  analytics: "Analytics",
  commerce: "Commerce",
  triage: "Triage",
};

export function MessageBubble({ message, isUser }: MessageBubbleProps) {
  const createdAt = new Date(message.created_at);
  const relativeTime = formatDistanceToNow(createdAt, {
    addSuffix: true,
    locale: message.answer?.language?.startsWith("pt") ? ptBR : enUS,
  });

  return (
    <div
      className={`flex gap-3 mb-4 ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback className={isUser ? "bg-primary text-primary-foreground" : "bg-muted"}>
          {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
        </AvatarFallback>
      </Avatar>

      {/* Message Content */}
      <div
        className={`flex flex-col gap-1 max-w-[80%] ${
          isUser ? "items-end" : "items-start"
        }`}
      >
        {/* Agent Badge (assistant only) */}
        {!isUser && message.agent && (
          <Badge
            variant={agentColors[message.agent]}
            className="text-xs self-start"
          >
            {agentLabels[message.agent]}
          </Badge>
        )}

        {/* Message Bubble */}
        <div
          className={`rounded-lg px-4 py-2 ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-muted text-foreground"
          }`}
        >
          <MessageContent
            content={message.content}
            agent={message.agent}
          />
        </div>

        {/* Timestamp */}
        <span
          className="text-xs text-muted-foreground"
          title={createdAt.toLocaleString()}
        >
          {relativeTime}
        </span>
      </div>
    </div>
  );
}

