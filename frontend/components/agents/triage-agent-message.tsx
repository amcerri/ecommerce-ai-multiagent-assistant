/**
 * Triage agent message component (message display for Triage Agent).
 *
 * Overview
 *   Displays messages from the Triage Agent with guidance, suggestions, and
 *   follow-up questions. Provides helpful navigation and suggestions.
 *
 * Design
 *   - **Guidance Message**: Clear guidance text.
 *   - **Suggestions**: List of suggested actions or queries.
 *   - **Follow-up Questions**: Clickable follow-up questions.
 *   - **Help Icons**: Visual indicators for help content.
 *
 * Integration
 *   - Consumes: Message object with Answer containing suggestions.
 *   - Returns: Rendered Triage Agent message.
 *   - Used by: MessageBubble or MessageList components.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <TriageAgentMessage message={message} />
 */

"use client";

import { HelpCircle, ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MessageContent } from "@/app/chat/components/message-content";
import type { Message } from "@/types/chat";

interface TriageAgentMessageProps {
  message: Message;
  onSuggestionClick?: (suggestion: string) => void;
}

export function TriageAgentMessage({
  message,
  onSuggestionClick,
}: TriageAgentMessageProps) {
  const answer = message.answer;
  if (!answer) {
    return null;
  }

  // Extract suggestions from metadata or answer text
  const suggestions = answer.metadata?.suggestions as string[] | undefined;

  return (
    <div className="space-y-3">
      {/* Badge and Icon */}
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="border-purple-500 text-purple-600">
          <HelpCircle className="h-3 w-3 mr-1" />
          Triage
        </Badge>
      </div>

      {/* Content */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <MessageContent content={answer.text} agent="triage" />
      </div>

      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            Suggestions:
          </p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => onSuggestionClick?.(suggestion)}
              >
                {suggestion}
                <ArrowRight className="h-3 w-3 ml-1" />
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

