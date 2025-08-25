import { useState } from "preact/hooks";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card.tsx";
import { Loader2Icon } from "lucide-react";
import ReactMarkdown from "react-markdown";

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
          {loading ? ((<Loader2Icon className="animate-spin" />) as any) : null}
          {loading ? "Loading..." : "Ask"}
        </Button>
      </div>
      <div id="answer" className="mt-4">
        {answer ? (
          <Card className="border-2 transition-all duration-500 ease-out transform opacity-100 translate-y-0 animate-slideup mb-4">
            <div className="px-4">
              <p className="whitespace-pre-wrap mb-2">
                <ReactMarkdown>{answer}</ReactMarkdown>
              </p>
            </div>
          </Card>
        ) : null}
        {citations.length ? (
          <Card className="w-full mb-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {citations.length} citations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {citations.map((citation: Citation) => (
                  <div key={citation.n} className="flex gap-3 py-2">
                    <span className="text-sm font-medium text-muted-foreground min-w-[2rem]">
                      [{citation.n}]
                    </span>
                    <p className="text-sm leading-relaxed text-foreground break-words">{citation.source}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ) : null}
      </div>
    </section>
  );
}
