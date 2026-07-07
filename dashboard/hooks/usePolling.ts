import { useEffect, useRef } from 'react';

interface UsePollingOptions {
  enabled: boolean;
  intervalMs: number;
  onPoll: () => Promise<void> | void;
}

export function usePolling({ enabled, intervalMs, onPoll }: UsePollingOptions) {
  const pollRef = useRef(onPoll);

  useEffect(() => {
    pollRef.current = onPoll;
  }, [onPoll]);

  useEffect(() => {
    if (!enabled) return undefined;

    let cancelled = false;

    async function poll() {
      if (!cancelled) {
        await pollRef.current();
      }
    }

    poll();
    const timer = window.setInterval(poll, intervalMs);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [enabled, intervalMs]);
}
