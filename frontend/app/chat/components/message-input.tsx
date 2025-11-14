/**
 * Message input component (text input with file upload and send button).
 *
 * Overview
 *   Provides a text input area with file upload capability and send button.
 *   Supports multi-line input with Enter to send and Shift+Enter for new line.
 *   Includes file preview and validation.
 *
 * Design
 *   - **Textarea**: Expandable textarea for multi-line input.
 *   - **File Upload**: Support for PDF, DOCX, TXT, and image files.
 *   - **File Preview**: Shows attached file name with remove option.
 *   - **Send Button**: Disabled when input is empty, shows loading state.
 *   - **Keyboard Shortcuts**: Enter to send, Shift+Enter for new line.
 *
 * Integration
 *   - Consumes: onSend callback function and optional disabled state.
 *   - Returns: Rendered input component.
 *   - Used by: ChatInterface component.
 *   - Observability: N/A (presentation only).
 *
 * Usage
 *   >>> <MessageInput
 *   ...   onSend={(query, file) => handleSend(query, file)}
 *   ...   disabled={isLoading}
 *   ... />
 */

"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Send, Paperclip, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

interface MessageInputProps {
  onSend: (query: string, file?: File) => void;
  disabled?: boolean;
}

const MAX_FILE_SIZE_MB = 10;
const SUPPORTED_FILE_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "image/png",
  "image/jpeg",
  "image/jpg",
];

export function MessageInput({ onSend, disabled = false }: MessageInputProps) {
  const [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (query.trim() || file) {
      onSend(query.trim(), file || undefined);
      setQuery("");
      setFile(null);
      setError(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    if (!SUPPORTED_FILE_TYPES.includes(selectedFile.type)) {
      setError(
        `File type not supported. Supported types: PDF, DOCX, TXT, PNG, JPG`
      );
      return;
    }

    // Validate file size
    const fileSizeMB = selectedFile.size / (1024 * 1024);
    if (fileSizeMB > MAX_FILE_SIZE_MB) {
      setError(`File size exceeds maximum: ${MAX_FILE_SIZE_MB}MB`);
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setQuery(e.target.value);
    // Auto-resize textarea
    e.target.style.height = "auto";
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  return (
    <div className="border-t bg-background p-4">
      {error && (
        <div className="mb-2 text-sm text-destructive">{error}</div>
      )}

      {file && (
        <div className="mb-2 flex items-center gap-2">
          <Badge variant="secondary" className="gap-2">
            <Paperclip className="h-3 w-3" />
            {file.name}
            <button
              type="button"
              onClick={handleRemoveFile}
              className="ml-1 hover:text-destructive"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        </div>
      )}

      <div className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={query}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            disabled={disabled}
            rows={1}
            className="w-full min-h-[40px] max-h-[200px] resize-none rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.png,.jpg,.jpeg"
          onChange={handleFileSelect}
          className="hidden"
          id="file-upload"
        />

        <Button
          variant="outline"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          type="button"
        >
          <Paperclip className="h-4 w-4" />
          <span className="sr-only">Upload file</span>
        </Button>

        <Button
          onClick={handleSend}
          disabled={disabled || (!query.trim() && !file)}
          size="icon"
        >
          <Send className="h-4 w-4" />
          <span className="sr-only">Send message</span>
        </Button>
      </div>
    </div>
  );
}

