import { useState } from "preact/hooks";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import { Card } from "./ui/card.tsx";
import { Loader2Icon } from "lucide-react";

type Citation = { n: string; source: string };

export default function Ask() {
  const [question, setQuestion] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
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
    setLoading(false);
  }

  function askButtonDisabled(): boolean {
    return !question.trim() || loading;
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
        <Button
          onClick={ask}
          disabled={askButtonDisabled()}
          className="w-full py-6 text-lg font-semibold flex items-center justify-center gap-2"
        >
          {loading && <Loader2Icon className="animate-spin" />}
          {loading ? "Loading..." : "Ask"}
        </Button>
      </div>
      <div id="answer" className="mt-4">
        {answer && (
            <Card className="border-2 transition-all duration-500 ease-out transform opacity-100 translate-y-0 animate-slideup">
            <div className="p-4">
              <pre className="whitespace-pre-wrap mb-2">{answer}</pre>
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
        )}
      </div>
    </section>
  );
}
