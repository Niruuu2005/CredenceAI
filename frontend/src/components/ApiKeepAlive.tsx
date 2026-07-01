import { useEffect } from "react";
import { api } from "@/lib/api";

const MIN_INTERVAL_MS = 30_000;
const MAX_INTERVAL_MS = 45_000;

function randomIntervalMs(): number {
  return (
    MIN_INTERVAL_MS +
    Math.floor(Math.random() * (MAX_INTERVAL_MS - MIN_INTERVAL_MS + 1))
  );
}

/**
 * Pings /api/health on a random 30–45s interval while the tab is open
 * so the Render free-tier API stays warm during active sessions.
 */
export function ApiKeepAlive() {
  useEffect(() => {
    let timer: ReturnType<typeof setTimeout>;
    let cancelled = false;

    const ping = async () => {
      if (cancelled) return;
      try {
        await api.checkHealth();
      } catch {
        // Ignore — API may be cold-starting
      }
      if (!cancelled) {
        timer = setTimeout(ping, randomIntervalMs());
      }
    };

    timer = setTimeout(ping, randomIntervalMs());
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  return null;
}
