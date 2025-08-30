import { useState, type FormEvent } from 'react';
import Stats from './Stats.tsx';
import { ingestPdf } from '../lib/api';

export default function Ingest() {
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function ingest(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fileInput = (e.currentTarget.elements.namedItem('pdf') as HTMLInputElement);
    const file = fileInput?.files?.[0];
    if (!file) return;
    setLoading(true);
    setMsg('Uploading…');
    try {
      const j = await ingestPdf(file);
      setMsg(j.ok ? `Ingested ${j.chunks} chunks in ${j.seconds ?? '?'}s` : (j.msg || 'Error'));
    } catch (err) {
      setMsg('Upload failed');
    }
    setLoading(false);
  }

  return (
    <section>
      <h3>Upload a PDF</h3>
      <form id="uploadForm" onSubmit={ingest}>
        <input type="file" name="pdf" accept="application/pdf" required disabled={loading} />
        <button type="submit" disabled={loading}>Ingest PDF</button>
      </form>
      <p id="uploadMsg" className="muted">{msg}</p>
      <Stats />
    </section>
  );
}
