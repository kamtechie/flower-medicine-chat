import { useState, useEffect } from 'react';

export default function Stats() {
  const [stats, setStats] = useState<string>('');
  useEffect(() => {
    async function fetchStats() {
      try {
        const r = await fetch('/api/stats');
        const j = await r.json();
        setStats(`(${j.count} chunks indexed)`);
      } catch { /* empty */ }
    }
    fetchStats();
  }, []);
  return <small className="muted">{stats}</small>;
}
