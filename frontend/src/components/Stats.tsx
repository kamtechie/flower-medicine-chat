import { useState, useEffect } from 'react';
import { fetchStats } from '../lib/api';

export default function Stats() {
  const [stats, setStats] = useState<string>('');
  useEffect(() => {
    async function getStats() {
      try {
        const j = await fetchStats();
        setStats(`(${j.count} chunks indexed)`);
      } catch { /* empty */ }
    }
    getStats();
  }, []);
  return <small className="muted">{stats}</small>;
}
