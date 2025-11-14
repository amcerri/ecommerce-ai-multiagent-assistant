import type { Metadata } from "next";

import { ChatInterface } from "./components/chat-interface";

export const metadata: Metadata = {
  title: "Chat | E-Commerce AI Multi-Agent Assistant",
  description: "Chat with AI assistant",
};

export default function ChatPage() {
  return (
    <div className="flex h-screen flex-col">
      <ChatInterface />
    </div>
  );
}

