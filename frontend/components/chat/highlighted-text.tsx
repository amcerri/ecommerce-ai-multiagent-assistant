/**
 * Highlighted text component (citation highlighting with multiple colors).
 *
 * Overview
 *   Highlights citations in text using character positions. Supports multiple
 *   overlapping citations with different colors. Integrates with CitationTooltip
 *   for hover information.
 *
 * Design
 *   - **Character Positions**: Uses start_char and end_char for precise highlighting.
 *   - **Multiple Citations**: Supports overlapping citations with different colors.
 *   - **Color Assignment**: Assigns unique colors per document.
 *   - **Hover Effects**: Background intensifies on hover, cursor pointer.
 *   - **Animation**: Fade-in animation on load.
 *
 * Integration
 *   - Consumes: Text string and array of Citation objects.
 *   - Returns: Rendered text with highlighted citations.
 *   - Used by: KnowledgeAgentMessage component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <HighlightedText text={answer.text} citations={answer.citations} />
 */

"use client";

import { useMemo } from "react";
import { CitationTooltip } from "./citation-tooltip";
import type { Citation } from "@/types/chat";

interface HighlightedTextProps {
  text: string;
  citations: Citation[];
}

// Color palette for citations (one color per document)
const CITATION_COLORS = [
  "bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700",
  "bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700",
  "bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700",
  "bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700",
  "bg-pink-100 dark:bg-pink-900/30 border-pink-300 dark:border-pink-700",
  "bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700",
];

interface TextSegment {
  text: string;
  start: number;
  end: number;
  citations: Citation[];
}

export function HighlightedText({ text, citations }: HighlightedTextProps) {
  // Create a map of document IDs to colors
  const documentColorMap = useMemo(() => {
    const map = new Map<string, number>();
    let colorIndex = 0;
    citations.forEach((citation) => {
      if (!map.has(citation.document_id)) {
        map.set(citation.document_id, colorIndex % CITATION_COLORS.length);
        colorIndex++;
      }
    });
    return map;
  }, [citations]);

  // Build segments with overlapping citations
  const segments = useMemo(() => {
    if (citations.length === 0) {
      return [{ text, start: 0, end: text.length, citations: [] }];
    }

    // Create sorted list of all citation boundaries
    const boundaries = new Set<number>();
    citations.forEach((citation) => {
      boundaries.add(citation.start_char);
      boundaries.add(citation.end_char);
    });
    boundaries.add(0);
    boundaries.add(text.length);

    const sortedBoundaries = Array.from(boundaries).sort((a, b) => a - b);

    // Build segments
    const segments: TextSegment[] = [];
    for (let i = 0; i < sortedBoundaries.length - 1; i++) {
      const start = sortedBoundaries[i];
      const end = sortedBoundaries[i + 1];
      const segmentText = text.slice(start, end);

      // Find citations that overlap with this segment
      const overlappingCitations = citations.filter(
        (citation) =>
          citation.start_char < end && citation.end_char > start
      );

      segments.push({
        text: segmentText,
        start,
        end,
        citations: overlappingCitations,
      });
    }

    return segments;
  }, [text, citations]);

  if (citations.length === 0) {
    return <span>{text}</span>;
  }

  return (
    <span className="animate-in fade-in duration-300">
      {segments.map((segment, index) => {
        if (segment.citations.length === 0) {
          return <span key={index}>{segment.text}</span>;
        }

        // Get unique document IDs for this segment
        const documentIds = Array.from(
          new Set(segment.citations.map((c) => c.document_id))
        );

        // Use the first document's color (or combine if multiple)
        const firstCitation = segment.citations[0];
        const colorIndex = documentColorMap.get(firstCitation.document_id) || 0;
        const colorClass = CITATION_COLORS[colorIndex];

        // If multiple citations, show all in tooltip
        const tooltipCitation = segment.citations.length === 1
          ? firstCitation
          : firstCitation; // Use first for now, could be enhanced

        return (
          <CitationTooltip key={index} citation={tooltipCitation}>
            <span
              className={`relative px-0.5 rounded border-b-2 border-dashed transition-colors hover:opacity-80 cursor-pointer ${colorClass}`}
              style={{
                // Stack multiple colors if multiple citations
                background: segment.citations.length > 1
                  ? `linear-gradient(to right, ${segment.citations
                      .map((c) => {
                        const idx = documentColorMap.get(c.document_id) || 0;
                        return CITATION_COLORS[idx].split(" ")[0];
                      })
                      .join(", ")})`
                  : undefined,
              }}
            >
              {segment.text}
            </span>
          </CitationTooltip>
        );
      })}
    </span>
  );
}

