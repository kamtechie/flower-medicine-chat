import { useState } from "preact/hooks";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import { Card } from "./ui/card.tsx";

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
      <div className="grid gap-2">
        <Textarea
          value={question}
          onInput={(e) => setQuestion((e.target as HTMLTextAreaElement).value)}
          placeholder='Ask a question - e.g. "what are the indications for Rescue Remedy?"'
          disabled={loading}
        />
        <Button onClick={ask} disabled={loading}>
          Send message
        </Button>
      </div>
      <div id="answer" className="mt-4">
        <Card className="border-2">
          <div className="p-4">
            {loading && <p className="muted">{status}</p>}
            {answer && (
              <>
                <pre className="whitespace-pre-wrap mb-2">{answer}</pre>
              </>
            )}
            {citations.length > 0 && (
              <>
                <h4 className="font-semibold mb-2">Citations</h4>
                <pre className="whitespace-pre-wrap">
                  {citations.map((c) => `[${c.n}] ${c.source}`).join("\n")}
                </pre>
              </>
            )}
          </div>
        </Card>
      </div>
    </section>
  );
}
