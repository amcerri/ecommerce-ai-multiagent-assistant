/**
 * Message content component (markdown rendering with syntax highlighting).
 *
 * Overview
 *   Renders message content with markdown support, syntax highlighting for SQL,
 *   and formatted tables. Uses react-markdown with plugins for GitHub Flavored
 *   Markdown and code highlighting.
 *
 * Design
 *   - **Markdown Rendering**: Uses react-markdown for markdown parsing.
 *   - **SQL Highlighting**: Syntax highlighting for SQL code blocks when agent is "analytics".
 *   - **GFM Support**: GitHub Flavored Markdown for tables, strikethrough, etc.
 *   - **Code Blocks**: Syntax highlighting for code blocks using rehype-highlight.
 *
 * Integration
 *   - Consumes: Message content string and optional agent name.
 *   - Returns: Rendered React component with formatted content.
 *   - Used by: MessageBubble component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <MessageContent content="Hello **world**" agent="knowledge" />
 */

"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

interface MessageContentProps {
  content: string;
  agent?: "knowledge" | "analytics" | "commerce" | "triage";
}

export function MessageContent({ content, agent }: MessageContentProps) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={agent === "analytics" ? [rehypeHighlight] : []}
        components={{
          // Custom code block styling
          code({ node, inline, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const isSQL = match && match[1] === "sql";
            const isAnalytics = agent === "analytics" && isSQL;

            return !inline && match ? (
              <pre
                className={`rounded-md p-4 overflow-x-auto ${
                  isAnalytics
                    ? "bg-slate-900 text-slate-100"
                    : "bg-muted text-foreground"
                }`}
                {...props}
              >
                <code className={className} {...props}>
                  {children}
                </code>
              </pre>
            ) : (
              <code
                className="rounded bg-muted px-1.5 py-0.5 text-sm font-mono"
                {...props}
              >
                {children}
              </code>
            );
          },
          // Custom table styling
          table({ children }) {
            return (
              <div className="overflow-x-auto my-4">
                <table className="min-w-full divide-y divide-border border border-border rounded-md">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return <thead className="bg-muted">{children}</thead>;
          },
          th({ children }) {
            return (
              <th className="px-4 py-2 text-left text-sm font-semibold">
                {children}
              </th>
            );
          },
          td({ children }) {
            return <td className="px-4 py-2 text-sm border-t border-border">{children}</td>;
          },
          // Custom link styling
          a({ children, href }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                {children}
              </a>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

