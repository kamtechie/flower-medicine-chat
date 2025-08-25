import { useState } from "preact/hooks";
import Stats from "./Stats.tsx";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";

type Citation = { n: string; source: string };

export default function Ask() {
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>("");

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
    setStatus("Thinking…");
    setAnswer("");
    setCitations([]);
    const r = await fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const j = await r.json();
    setAnswer(j.answer || "");
    setCitations(j.citations || []);
    setStatus("");
    setLoading(false);
  }

  return (
    <section>
      <div class="row">
        <h3>Ask a question</h3>
        <Stats />
      </div>
      <div className="grid w-full gap-2">
        <Textarea
          value={question}
          onInput={(e) => setQuestion((e.target as HTMLTextAreaElement).value)}
          placeholder="e.g., What are the indications for Rescue Remedy?"
          disabled={loading}
        />
        <Button onClick={ask} disabled={loading}>
          Send message
        </Button>
      </div>
      <div id="answer">
        {loading && <p className="muted">{status}</p>}
        {answer && (
          <>
            <h4>Answer</h4>
            <pre>{answer}</pre>
          </>
        )}
        {citations.length > 0 && (
          <>
            <h4>Citations</h4>
            <pre>
              {citations.map((c) => `[${c.n}] ${c.source}`).join("\n")}
            </pre>
          </>
        )}
      </div>
    </section>
  );
}
