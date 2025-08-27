import { useState } from "preact/hooks";
import { Button } from "./ui/button.tsx";
import { Textarea } from "./ui/textarea.tsx";
import { Card } from "./ui/card.tsx";
import { Loader2Icon } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { toast, Toaster } from "sonner";

export default function Ask() {
  const [question, setQuestion] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [answer, setAnswer] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  async function ask() {
    if (!question.trim()) return;
  setLoading(true);
  setAnswer("");
    try {
      const r = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!r.ok) {
        let errorMsg = "An error occurred.";
        try {
          const err = await r.json();
          console.error(err);
          errorMsg = err.detail.msg || err.msg || errorMsg;
        } catch {
          errorMsg = r.statusText || errorMsg;
        }
        toast(errorMsg);
        setLoading(false);
        return;
      }
  const j = await r.json();
  setAnswer(j.answer || "");
    } catch (err) {
      toast("Network error or server unavailable.");
    } finally {
      setLoading(false);
    }
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
      </div>
      <Toaster />
    </section>
  );
}
