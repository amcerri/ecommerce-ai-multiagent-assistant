/**
 * Analytics agent message component (message display for Analytics Agent).
 *
 * Overview
 *   Displays messages from the Analytics Agent with formatted tables, SQL
 *   queries, and performance metrics. Shows SQL in metadata panel with copy
 *   functionality.
 *
 * Design
 *   - **Table Formatting**: Formats tabular results from SQL queries.
 *   - **SQL Display**: Shows generated SQL in metadata panel.
 *   - **Performance Metrics**: Displays execution time and query metrics.
 *   - **Copy SQL**: Button to copy SQL query to clipboard.
 *
 * Integration
 *   - Consumes: Message object with Answer containing SQL metadata.
 *   - Returns: Rendered Analytics Agent message.
 *   - Used by: MessageBubble or MessageList components.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <AnalyticsAgentMessage message={message} />
 */

"use client";

import { BarChart3 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { MetadataPanel } from "@/components/chat/metadata-panel";
import { MessageContent } from "@/app/chat/components/message-content";
import type { Message } from "@/types/chat";

interface AnalyticsAgentMessageProps {
  message: Message;
}

export function AnalyticsAgentMessage({
  message,
}: AnalyticsAgentMessageProps) {
  const answer = message.answer;
  if (!answer) {
    return null;
  }

  return (
    <div className="space-y-3">
      {/* Badge and Icon */}
      <div className="flex items-center gap-2">
        <Badge variant="secondary" className="bg-blue-600 hover:bg-blue-700">
          <BarChart3 className="h-3 w-3 mr-1" />
          Analytics
        </Badge>
      </div>

      {/* Content with Table Formatting */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <MessageContent content={answer.text} agent="analytics" />
      </div>

      {/* Metadata Panel with SQL */}
      <MetadataPanel metadata={answer} agent="analytics" />
    </div>
  );
}

