import { useState } from 'preact/hooks';
import Stats from './Stats.tsx';

export default function Ingest() {
  const [msg, setMsg] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  async function ingest(e: Event) {
    e.preventDefault();
    const target = e.target as HTMLFormElement;
    const fileInput = target.pdf as HTMLInputElement;
    const file = fileInput.files?.[0];
    if (!file) return;
    setLoading(true);
    setMsg('Uploading…');
    const fd = new FormData();
    fd.append('file', file);
    const r = await fetch('/ingest/pdf', { method: 'POST', body: fd });
    const j = await r.json();
    setMsg(j.ok ? `Ingested ${j.chunks} chunks in ${j.seconds || '?'}s` : (j.msg || 'Error'));
    setLoading(false);
  }
  return (
    <section>
      <h3>Upload a PDF</h3>
      <form id="uploadForm" onSubmit={ingest}>
        <input type="file" name="pdf" accept="application/pdf" required disabled={loading} />
        <button type="submit" disabled={loading}>Ingest PDF</button>
      </form>
      <p id="uploadMsg" class="muted">{msg}</p>
      <Stats />
    </section>
  );
}
