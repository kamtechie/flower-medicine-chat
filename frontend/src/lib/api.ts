// Centralized API module for Zenji frontend
// All backend calls should go through here

export async function fetchStats() {
  const res = await fetch("/api/stats");
  if (!res.ok) await handleErrorResponse(res, "Failed to fetch stats");
  return res.json();
}

export async function ingestPdf(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/ingest/pdf", {
    method: "POST",
    body: formData,
  });
  if (!res.ok) await handleErrorResponse(res, "Failed to ingest PDF");
  return res.json();
}

export async function chatStep(session_id: string, message: string) {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, message }),
  });
  if (!res.ok) await handleErrorResponse(res, "Chat step failed");
  return res.json();
}

async function handleErrorResponse(res: Response, details: string) {
    let json;
    try {
        json = await res.json();
    } catch {
        throw new Error("Failed to parse error response");
    }

    if (res.status === 401) {
        throw new Error("Invalid session, please refresh the page.");
    } else if (res.status === 500) {
        console.error("Server error:", json);
        throw new Error("Server error");
    } else {
        console.error("Unknown error:", json);
        throw new Error(details ?? "Unknown error");
    }
}
// Add more API functions as needed
