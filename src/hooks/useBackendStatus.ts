// src/hooks/useBackendStatus.ts
import { useState, useEffect, useCallback } from "react";
import { checkBackend, getStats } from "../api/lyzeClient";

export interface BackendStatus {
  connected: boolean;
  checking: boolean;
  totalChunks: number;
  recheck: () => void;
}

export function useBackendStatus(): BackendStatus {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking]   = useState(true);
  const [totalChunks, setTotal]   = useState(0);

  const recheck = useCallback(async () => {
    setChecking(true);
    const ok = await checkBackend();
    setConnected(ok);
    if (ok) {
      try {
        const stats = await getStats();
        setTotal(stats.total_chunks);
      } catch { /* ignore */ }
    }
    setChecking(false);
  }, []);

  useEffect(() => {
    recheck();
    // Re-check every 30s
    const id = setInterval(recheck, 30_000);
    return () => clearInterval(id);
  }, [recheck]);

  return { connected, checking, totalChunks, recheck };
}
