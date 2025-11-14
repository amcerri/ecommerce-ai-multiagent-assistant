/**
 * Knowledge agent message component (message display for Knowledge Agent).
 *
 * Overview
 *   Displays messages from the Knowledge Agent with citation highlighting,
 *   tooltips, and metadata panel. Shows document legend and chunk information.
 *
 * Design
 *   - **Citation Highlighting**: Uses HighlightedText for citation highlighting.
 *   - **Tooltips**: CitationTooltip on hover for citation details.
 *   - **Legend**: Shows document-color mapping for citations.
 *   - **Metadata**: MetadataPanel with chunks used.
 *
 * Integration
 *   - Consumes: Message object with Answer containing citations.
 *   - Returns: Rendered Knowledge Agent message.
 *   - Used by: MessageBubble or MessageList components.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <KnowledgeAgentMessage message={message} />
 */

"use client";

import { useMemo } from "react";
import { BookOpen } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { HighlightedText } from "@/components/chat/highlighted-text";
import { MetadataPanel } from "@/components/chat/metadata-panel";
import type { Message } from "@/types/chat";

interface KnowledgeAgentMessageProps {
  message: Message;
}

const CITATION_COLORS = [
  { bg: "bg-yellow-100 dark:bg-yellow-900/30", border: "border-yellow-300 dark:border-yellow-700" },
  { bg: "bg-blue-100 dark:bg-blue-900/30", border: "border-blue-300 dark:border-blue-700" },
  { bg: "bg-green-100 dark:bg-green-900/30", border: "border-green-300 dark:border-green-700" },
  { bg: "bg-purple-100 dark:bg-purple-900/30", border: "border-purple-300 dark:border-purple-700" },
  { bg: "bg-pink-100 dark:bg-pink-900/30", border: "border-pink-300 dark:border-pink-700" },
  { bg: "bg-orange-100 dark:bg-orange-900/30", border: "border-orange-300 dark:border-orange-700" },
];

export function KnowledgeAgentMessage({
  message,
}: KnowledgeAgentMessageProps) {
  const answer = message.answer;
  if (!answer || !answer.citations) {
    return null;
  }

  // Create document-color mapping for legend
  const documentLegend = useMemo(() => {
    const map = new Map<string, { document: string; colorIndex: number }>();
    let colorIndex = 0;
    answer.citations!.forEach((citation) => {
      if (!map.has(citation.document_id)) {
        map.set(citation.document_id, {
          document: citation.document_title || citation.file_name,
          colorIndex: colorIndex % CITATION_COLORS.length,
        });
        colorIndex++;
      }
    });
    return Array.from(map.values());
  }, [answer.citations]);

  return (
    <div className="space-y-3">
      {/* Badge and Icon */}
      <div className="flex items-center gap-2">
        <Badge variant="default" className="bg-green-600 hover:bg-green-700">
          <BookOpen className="h-3 w-3 mr-1" />
          Knowledge
        </Badge>
      </div>

      {/* Content with Citations */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <HighlightedText text={answer.text} citations={answer.citations} />
      </div>

      {/* Document Legend */}
      {documentLegend.length > 0 && (
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="text-muted-foreground">Citations:</span>
          {documentLegend.map((item, index) => {
            const color = CITATION_COLORS[item.colorIndex];
            return (
              <div
                key={index}
                className={`flex items-center gap-1 px-2 py-0.5 rounded border ${color.bg} ${color.border}`}
              >
                <div
                  className={`w-2 h-2 rounded-full ${color.bg.replace("bg-", "bg-").split(" ")[0]}`}
                />
                <span className="truncate max-w-[150px]">
                  {item.document}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* Metadata Panel */}
      <MetadataPanel metadata={answer} agent="knowledge" />
    </div>
  );
}

