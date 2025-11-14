/**
 * Metadata panel component (expandable technical metadata display).
 *
 * Overview
 *   Displays technical metadata in an expandable accordion panel. Shows
 *   agent-specific sections: chunks (Knowledge), SQL (Analytics), document
 *   schema (Commerce), routing decision, and performance metrics.
 *
 * Design
 *   - **Accordion**: Uses shadcn/ui Accordion for expandable sections.
 *   - **Agent-Specific**: Different sections based on agent type.
 *   - **Performance Metrics**: Shows processing time, tokens, cost.
 *   - **SQL Highlighting**: Syntax highlighting for SQL queries.
 *
 * Integration
 *   - Consumes: Message metadata and agent name.
 *   - Returns: Rendered metadata panel.
 *   - Used by: Agent-specific message components.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <MetadataPanel metadata={message.answer} agent={message.agent} />
 */

"use client";

import { useState } from "react";
import { Copy, Check, Database, FileText, BarChart3, Zap } from "lucide-react";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { Answer } from "@/types/chat";

interface MetadataPanelProps {
  metadata: Answer;
  agent: "knowledge" | "analytics" | "commerce" | "triage";
}

export function MetadataPanel({ metadata, agent }: MetadataPanelProps) {
  const [copiedSql, setCopiedSql] = useState(false);

  const handleCopySql = async (sql: string) => {
    await navigator.clipboard.writeText(sql);
    setCopiedSql(true);
    setTimeout(() => setCopiedSql(false), 2000);
  };

  return (
    <Accordion type="single" collapsible className="w-full">
      {/* Knowledge Agent: Chunks Utilizados */}
      {agent === "knowledge" && metadata.citations && (
        <AccordionItem value="chunks">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              <span>Chunks Utilizados ({metadata.citations.length})</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3">
              {metadata.citations.map((citation, index) => (
                <div
                  key={index}
                  className="p-3 rounded-md border bg-muted/50 space-y-2"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {citation.document_title || citation.file_name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Chunk {citation.chunk_index}
                        {citation.page_number && ` • Page ${citation.page_number}`}
                      </p>
                    </div>
                    {citation.similarity_score !== undefined && (
                      <Badge variant="secondary" className="ml-2">
                        {Math.round(citation.similarity_score * 100)}%
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2">
                    {citation.content}
                  </p>
                </div>
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {/* Analytics Agent: SQL Gerado */}
      {agent === "analytics" && metadata.sql_metadata && (
        <AccordionItem value="sql">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              <span>SQL Gerado</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-3">
              <div className="relative">
                <pre className="p-3 rounded-md border bg-slate-900 text-slate-100 text-xs overflow-x-auto">
                  <code>{metadata.sql_metadata.sql}</code>
                </pre>
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute top-2 right-2 h-7 w-7 p-0"
                  onClick={() => handleCopySql(metadata.sql_metadata!.sql)}
                >
                  {copiedSql ? (
                    <Check className="h-3 w-3" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
              </div>
              <div className="text-xs text-muted-foreground">
                <p>{metadata.sql_metadata.explanation}</p>
              </div>
              {metadata.sql_metadata.execution_time_ms !== undefined && (
                <div className="flex items-center gap-2 text-xs">
                  <Zap className="h-3 w-3" />
                  <span>
                    Execution time: {metadata.sql_metadata.execution_time_ms}ms
                  </span>
                </div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {/* Commerce Agent: Documento Processado */}
      {agent === "commerce" && metadata.document_metadata && (
        <AccordionItem value="document">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              <span>Documento Processado</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-4">
              {/* Schema Detectado */}
              {metadata.document_metadata.schema_detected && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Schema Detectado:</p>
                  <pre className="p-3 rounded-md border bg-muted text-xs overflow-x-auto">
                    {JSON.stringify(
                      metadata.document_metadata.schema_detected,
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}

              {/* Campos Extraídos */}
              {metadata.document_metadata.fields_extracted && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Campos Extraídos:</p>
                  <div className="space-y-1">
                    {Object.entries(
                      metadata.document_metadata.fields_extracted
                    ).map(([key, value]) => (
                      <div
                        key={key}
                        className="flex items-start gap-2 p-2 rounded-md border bg-muted/50"
                      >
                        <span className="text-xs font-medium min-w-[100px]">
                          {key}:
                        </span>
                        <span className="text-xs text-muted-foreground flex-1">
                          {String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Análise de Riscos */}
              {metadata.document_metadata.analysis_results && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Análise de Riscos:</p>
                  <pre className="p-3 rounded-md border bg-muted text-xs overflow-x-auto">
                    {JSON.stringify(
                      metadata.document_metadata.analysis_results,
                      null,
                      2
                    )}
                  </pre>
                </div>
              )}

              {/* Confiança */}
              {metadata.document_metadata.confidence_score !== undefined && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">Confiança da Extração:</span>
                    <Badge variant="secondary">
                      {Math.round(metadata.document_metadata.confidence_score * 100)}%
                    </Badge>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{
                        width: `${metadata.document_metadata.confidence_score * 100}%`,
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {/* Performance Metrics (All Agents) */}
      {metadata.performance_metrics && (
        <AccordionItem value="performance">
          <AccordionTrigger>
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              <span>Performance Metrics</span>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Total Time:</span>
                <span className="font-medium">
                  {metadata.performance_metrics.total_time_ms}ms
                </span>
              </div>
              {metadata.performance_metrics.retrieval_time_ms !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Retrieval Time:</span>
                  <span className="font-medium">
                    {metadata.performance_metrics.retrieval_time_ms}ms
                  </span>
                </div>
              )}
              {metadata.performance_metrics.generation_time_ms !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Generation Time:</span>
                  <span className="font-medium">
                    {metadata.performance_metrics.generation_time_ms}ms
                  </span>
                </div>
              )}
              {metadata.performance_metrics.tokens_used !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Tokens Used:</span>
                  <span className="font-medium">
                    {metadata.performance_metrics.tokens_used.toLocaleString()}
                  </span>
                </div>
              )}
              {metadata.performance_metrics.cost_estimate !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Cost Estimate:</span>
                  <span className="font-medium">
                    ${metadata.performance_metrics.cost_estimate.toFixed(4)}
                  </span>
                </div>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}
    </Accordion>
  );
}

