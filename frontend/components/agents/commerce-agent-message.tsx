/**
 * Commerce agent message component (message display for Commerce Agent).
 *
 * Overview
 *   Displays messages from the Commerce Agent with document schema visualization,
 *   extracted fields, risk analysis, and confidence scores. Shows structured
 *   document information.
 *
 * Design
 *   - **Schema Visualization**: Tree view of detected document schema.
 *   - **Extracted Fields**: Key-value display of extracted data.
 *   - **Risk Analysis**: Badges for risk severity levels.
 *   - **Confidence Score**: Progress bar showing extraction confidence.
 *
 * Integration
 *   - Consumes: Message object with Answer containing document metadata.
 *   - Returns: Rendered Commerce Agent message.
 *   - Used by: MessageBubble or MessageList components.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <CommerceAgentMessage message={message} />
 */

"use client";

import { FileText, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { MetadataPanel } from "@/components/chat/metadata-panel";
import { MessageContent } from "@/app/chat/components/message-content";
import type { Message } from "@/types/chat";

interface CommerceAgentMessageProps {
  message: Message;
}

function getRiskBadge(risk: string) {
  const riskLower = risk.toLowerCase();
  if (riskLower.includes("high") || riskLower.includes("critical")) {
    return (
      <Badge variant="destructive" className="gap-1">
        <XCircle className="h-3 w-3" />
        High Risk
      </Badge>
    );
  } else if (riskLower.includes("medium") || riskLower.includes("moderate")) {
    return (
      <Badge variant="outline" className="gap-1 border-orange-500 text-orange-600">
        <AlertTriangle className="h-3 w-3" />
        Medium Risk
      </Badge>
    );
  } else {
    return (
      <Badge variant="outline" className="gap-1 border-green-500 text-green-600">
        <CheckCircle className="h-3 w-3" />
        Low Risk
      </Badge>
    );
  }
}

export function CommerceAgentMessage({
  message,
}: CommerceAgentMessageProps) {
  const answer = message.answer;
  if (!answer) {
    return null;
  }

  const documentMeta = answer.document_metadata;

  return (
    <div className="space-y-3">
      {/* Badge and Icon */}
      <div className="flex items-center gap-2">
        <Badge variant="destructive" className="bg-orange-600 hover:bg-orange-700">
          <FileText className="h-3 w-3 mr-1" />
          Commerce
        </Badge>
        {documentMeta?.analysis_results &&
          typeof documentMeta.analysis_results === "object" &&
          "risk_level" in documentMeta.analysis_results &&
          getRiskBadge(String(documentMeta.analysis_results.risk_level))}
      </div>

      {/* Content */}
      <div className="prose prose-sm dark:prose-invert max-w-none">
        <MessageContent content={answer.text} agent="commerce" />
      </div>

      {/* Metadata Panel with Document Info */}
      <MetadataPanel metadata={answer} agent="commerce" />
    </div>
  );
}

