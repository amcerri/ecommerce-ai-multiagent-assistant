/**
 * Citation tooltip component (hover information for citations).
 *
 * Overview
 *   Displays citation information in a tooltip when hovering over highlighted
 *   text. Shows document title, file name, page/chunk, preview, and similarity score.
 *
 * Design
 *   - **Tooltip**: Uses shadcn/ui Tooltip component.
 *   - **Delay**: 300ms before appearing, 100ms before disappearing.
 *   - **Positioning**: Intelligent positioning to avoid screen edges.
 *   - **Content**: Document info, preview, similarity score, date.
 *
 * Integration
 *   - Consumes: Citation object and children (highlighted text).
 *   - Returns: Wrapped children with tooltip.
 *   - Used by: HighlightedText component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <CitationTooltip citation={citation}>
 *   ...   <span>Highlighted text</span>
 *   ... </CitationTooltip>
 */

"use client";

import { formatDistanceToNow } from "date-fns";
import { ptBR, enUS } from "date-fns/locale";
import { FileText, ExternalLink } from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { Citation } from "@/types/chat";

interface CitationTooltipProps {
  citation: Citation;
  children: React.ReactNode;
  language?: string;
}

export function CitationTooltip({
  citation,
  children,
  language = "pt-BR",
}: CitationTooltipProps) {
  const preview = citation.content.slice(0, 200);
  const similarityScore = citation.similarity_score || 0;
  const similarityPercentage = Math.round(similarityScore * 100);

  // Format date if available (assuming citation has created_at or similar)
  const dateLocale = language.startsWith("pt") ? ptBR : enUS;

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent
          side="top"
          className="max-w-md p-4 space-y-3"
          sideOffset={5}
        >
          {/* Header */}
          <div className="space-y-1">
            <div className="flex items-start gap-2">
              <FileText className="h-4 w-4 mt-0.5 shrink-0" />
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-sm truncate">
                  {citation.document_title || "Untitled Document"}
                </h4>
                <p className="text-xs text-muted-foreground truncate">
                  {citation.file_name}
                </p>
              </div>
            </div>
          </div>

          {/* Page/Chunk Info */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {citation.page_number && (
              <Badge variant="outline" className="text-xs">
                Page {citation.page_number}
              </Badge>
            )}
            <Badge variant="outline" className="text-xs">
              Chunk {citation.chunk_index}
            </Badge>
          </div>

          {/* Preview */}
          <div className="space-y-1">
            <p className="text-xs font-medium">Preview:</p>
            <p className="text-xs text-muted-foreground line-clamp-3">
              {preview}
              {citation.content.length > 200 && "..."}
            </p>
          </div>

          {/* Similarity Score */}
          {citation.similarity_score !== undefined && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium">Similarity:</span>
                <span className="text-muted-foreground">
                  {similarityPercentage}%
                </span>
              </div>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all"
                  style={{ width: `${similarityPercentage}%` }}
                />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="pt-2 border-t">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-xs h-8"
              onClick={() => {
                // TODO: Open document modal/viewer
                console.log("Open document:", citation.document_id);
              }}
            >
              <ExternalLink className="h-3 w-3 mr-2" />
              View full document
            </Button>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

