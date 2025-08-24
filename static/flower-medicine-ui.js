// flower-medicine-ui.js

// Utility to refresh stats
async function refreshStats() {
  try {
    const r = await fetch('/stats');
    const j = await r.json();
    const statsElem = document.getElementById('stats') || document.getElementById('uploadMsg');
    if (statsElem) {
      statsElem.textContent = `(${j.count} chunks indexed)`;
    }
  } catch { /* ignore */ }
}

// Ingest PDF logic
function setupIngestUI() {
  refreshStats();
  const uploadForm = document.getElementById('uploadForm');
  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const file = document.getElementById('pdf').files[0];
      if (!file) return;
      const fd = new FormData();
      fd.append('file', file);
      const r = await fetch('/ingest/pdf', { method: 'POST', body: fd });
      const j = await r.json();
      const msgElem = document.getElementById('uploadMsg');
      if (msgElem) {
        msgElem.textContent = j.ok ? `Ingested ${j.chunks} chunks in ${j.seconds || '?'}s` : (j.msg || 'Error');
      }
      refreshStats();
    });
  }
}

// Ask logic
function setupAskUI() {
  refreshStats();
  const askBtn = document.getElementById('askBtn');
  if (askBtn) {
    askBtn.addEventListener('click', async () => {
      const q = document.getElementById('q').value.trim();
      if (!q) return;
      document.getElementById('answer').innerHTML = '<p class="muted">Thinking…</p>';
      const r = await fetch('/ask', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ question: q })
      });
      const j = await r.json();
      const cites = (j.citations || []).map(c => `[${c.n}] ${c.source}`).join('\n');
      document.getElementById('answer').innerHTML =
        `<h4>Answer</h4><pre>${j.answer || ''}</pre>` +
        (cites ? `<h4>Citations</h4><pre>${cites}</pre>` : '');
    });
  }
}
