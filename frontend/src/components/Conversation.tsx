import { ArrowUp } from "lucide-react";
import { useEffect, useState } from "react";
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

type ChatOut = { reply: string; stage: string };
export default function Conversation() {
  const [sid, setSid] = useState<string>("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<
    { role: "user" | "bot"; text: string }[]
  >([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // create a session on mount
    start();
  }, []);

  async function start() {
    const r = await fetch("/api/session", { method: "POST" });
    const j = await r.json();
    setSid(j.session_id);
    push("bot", j.message);
  }

  function push(role: "user" | "bot", text: string) {
    setMessages((m) => [...m, { role, text }]);
  }

  async function send() {
    if (!sid || !input.trim()) return;
    const text = input.trim();
    setInput("");
    push("user", text);
    setBusy(true);
    try {
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sid, message: text }),
      });
      const j: ChatOut = await r.json();
      push("bot", j.reply || "");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col overflow-hidden flex-1">
      <ChatContainerRoot className="relative flex-1">
        <ChatContainerContent className="space-y-4 p-4">
          {messages.map((message, index) => {
            const isBot = message.role === "bot";

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
                </div>
              </Message>
            );
          })}
        </ChatContainerContent>
      </ChatContainerRoot>
      <div className="flex gap-2 mt-2">
        <PromptInput
          value={input}
          onValueChange={(value) => setInput(value)}
          isLoading={busy}
          onSubmit={() => send()}
          className="inset-x-0 bottom-0 mx-auto w-full max-w-(--breakpoint-md)"
        >
          <PromptInputTextarea placeholder="Type a message" />
          <PromptInputActions className="justify-end pt-2">
            <PromptInputAction
              tooltip={busy ? "Stop generation" : "Send message"}
            >
              <Button
                variant="default"
                size="icon"
                className="h-8 w-8 rounded-full"
                onClick={send}
                disabled={busy || !sid}
              >
                <ArrowUp className="size-5" />
              </Button>
            </PromptInputAction>
          </PromptInputActions>
        </PromptInput>
      </div>
      <p className="text-xs text-muted-foreground text-center my-1">
        Note: educational only; not medical advice.
      </p>
      {!sid && <button onClick={start}>Start new session</button>}
      
    </div>
  );
}
