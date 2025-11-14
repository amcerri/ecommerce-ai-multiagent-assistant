/**
 * Chat API types (TypeScript types for chat API responses).
 *
 * These types match the Pydantic schemas defined in the backend API.
 */

export interface ChatRequest {
  query: string;
  thread_id?: string;
  attachment?: {
    filename: string;
    content: string;
    mime_type: string;
  };
}

export interface Citation {
  document_id: string;
  document_title: string;
  file_name: string;
  chunk_index: number;
  page_number?: number;
  content: string;
  similarity_score?: number;
  start_char: number;
  end_char: number;
}

export interface Answer {
  text: string;
  agent: "knowledge" | "analytics" | "commerce" | "triage";
  language: string;
  citations?: Citation[];
  sql_metadata?: {
    sql: string;
    explanation: string;
    execution_time_ms?: number;
  };
  document_metadata?: {
    schema_detected: Record<string, unknown>;
    fields_extracted: Record<string, unknown>;
    analysis_results: Record<string, unknown>;
    confidence_score?: number;
  };
  performance_metrics?: {
    total_time_ms: number;
    retrieval_time_ms?: number;
    generation_time_ms?: number;
    tokens_used?: number;
    cost_estimate?: number;
  };
}

export interface ChatResponse {
  message_id: string;
  thread_id: string;
  response: Answer;
  language: string;
  metadata?: Record<string, unknown>;
}

export interface ChatHistoryResponse {
  thread_id: string;
  messages: Array<{
    message_id: string;
    role: "user" | "assistant";
    content: string;
    agent?: string;
    created_at: string;
  }>;
  total: number;
  limit: number;
}

export interface Message {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  agent?: "knowledge" | "analytics" | "commerce" | "triage";
  created_at: string;
  answer?: Answer;
}

