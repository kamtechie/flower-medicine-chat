// Centralized API module for Zenji frontend
// All backend calls should go through here

export async function fetchStats() {
  const res = await fetch("/api/stats");
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function ingestPdf(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/ingest/pdf", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("Failed to ingest PDF");
  return res.json();
}

export async function chatStep(session_id: string, message: string) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, message }),
  });
  if (!res.ok) throw new Error("Chat step failed");
  return res.json();
}

// Add more API functions as needed
