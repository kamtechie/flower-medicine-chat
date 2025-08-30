import { ArrowUp } from "lucide-react";
import { useEffect, useState, useCallback, useRef } from "react";
import { Button } from "./ui/button.tsx";
import {
  PromptInput,
  PromptInputTextarea,
  PromptInputActions,
  PromptInputAction,
} from "./ui/prompt-input.tsx";
import {
  ChatContainerContent,
  ChatContainerRoot,
} from "./ui/chat-container.tsx";
import { Markdown } from "./ui/markdown.tsx";
import { Message, MessageContent } from "./ui/message.tsx";

export default function Conversation() {
  type ChatOut = { reply?: string; stage?: string; error?: string };
  type SessionResponse = {
    session_id?: string;
    message?: string;
    error?: string;
  };
  type ChatMessage = { role: "user" | "bot"; text: string };
  const [sessionId, setSessionId] = useState<string>("");
  const [input, setInput] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  const push = useCallback((role: "user" | "bot", text: string) => {
    setMessages((m) => [...m, { role, text }]);
  }, []);

  const start = useCallback(async () => {
    setError("");
    try {
      const r = await fetch("/api/session", { method: "POST" });
      if (!r.ok) {
        setError("Failed to start session.");
        return;
      }
      const j: SessionResponse = await r.json();
      if (j.error || !j.session_id || !j.message) {
        setError(j.error || "Invalid session response.");
        return;
      }
      setSessionId(j.session_id);
      push("bot", j.message);
    } catch (e) {
      setError("Network error starting session.");
    }
  }, [push]);

  useEffect(() => {
    start();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = useCallback(async () => {
    if (!sessionId || !input.trim()) return;
    setError("");
    const text = input.trim();
    setInput("");
    push("user", text);
    setBusy(true);
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: text }),
      });
      if (!r.ok) {
        setError("Failed to get reply.");
        return;
      }
      const j: ChatOut = await r.json();
      if (j.error) {
        setError(j.error);
        return;
      }
      push("bot", j.reply || "");
    } catch (e) {
      setError("Network error sending message.");
    } finally {
      setBusy(false);
    }
  }, [sessionId, input, push]);

  // Auto-scroll to bottom on new message
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  // MessageList component
  function MessageList({
    messages,
    busy,
  }: {
    messages: ChatMessage[];
    busy: boolean;
  }) {
    return (
      <>
        {messages.map((message, index) => {
          const isBot = message.role === "bot";
          const isUserLatestMessage =
            message.role === "user" && index === messages.length - 1;
          return (
            <Message
              key={index}
              className={
                message.role === "user" ? "justify-end" : "justify-start"
              }
            >
              <div className="max-w-[70%] flex-1 sm:max-w-[65%]">
                {isBot ? (
                  <div className="bg-secondary text-foreground prose rounded-lg p-2">
                    <Markdown>{message.text}</Markdown>
                  </div>
                ) : (
                  <MessageContent className="bg-primary text-primary-foreground">
                    {message.text}
                  </MessageContent>
                )}
                {busy && isUserLatestMessage && (
                  <p className="text-muted-foreground">Thinking...</p>
                )}
              </div>
            </Message>
          );
        })}
        <div ref={chatEndRef} />
      </>
    );
  }

  return (
    <div className="flex flex-col overflow-hidden flex-1">
      <ChatContainerRoot className="relative flex-1">
        <ChatContainerContent className="space-y-4 p-4">
          <MessageList messages={messages} busy={busy} />
        </ChatContainerContent>
      </ChatContainerRoot>
      <div className="flex gap-2 mt-2">
        <PromptInput
          value={input}
          onValueChange={(value) => setInput(value)}
          isLoading={busy}
          onSubmit={send}
          className="inset-x-0 bottom-0 mx-auto w-full max-w-(--breakpoint-md)"
        >
          <PromptInputTextarea placeholder="Type a message" disabled={busy} />
          <PromptInputActions className="justify-end pt-2">
            <PromptInputAction
              tooltip={busy ? "Stop generation" : "Send message"}
            >
              <Button
                variant="default"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={send}
                disabled={busy || !sessionId}
              >
                <ArrowUp className="size-5" />
              </Button>
            </PromptInputAction>
          </PromptInputActions>
        </PromptInput>
      </div>
      {error && (
        <p className="text-xs text-red-500 text-center my-1">{error}</p>
      )}
      <p className="text-xs text-muted-foreground text-center my-1">
        Note: educational only; not medical advice.
      </p>
      {!sessionId && <button onClick={start}>Start new session</button>}
    </div>
  );
}
