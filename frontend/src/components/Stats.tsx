import { useState, useEffect } from 'preact/hooks';

export default function Stats() {
  const [stats, setStats] = useState<string>('');
  useEffect(() => {
    async function fetchStats() {
      try {
        const r = await fetch('/stats');
        const j = await r.json();
        setStats(`(${j.count} chunks indexed)`);
      } catch {}
    }
    fetchStats();
  }, []);
  return <small class="muted">{stats}</small>;
}
