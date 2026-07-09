// dashboard/hooks/useKnowledgeSync.ts

import { useState, useEffect, useCallback, useRef } from 'react';
import { triggerKnowledgeSync } from '../services/knowledgeService';

export type SyncState = 'idle' | 'confirming' | 'synchronizing' | 'completed' | 'failed';

export const PIPELINE_SYNC_STEPS = [
  { id: 'queued', label: 'Queued' },
  { id: 'loading_docs', label: 'Loading Documents' },
  { id: 'chunking', label: 'Semantic Chunking' },
  { id: 'embeddings', label: 'Embedding Generation' },
  { id: 'uploading_vectors', label: 'Vector Upload' },
  { id: 'completed', label: 'Knowledge Updated' }
];

export function useKnowledgeSync(onCompleted?: () => void) {
  const [syncState, setSyncState] = useState<SyncState>('idle');
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);
  const [duration, setDuration] = useState<number>(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingDocsCount, setPendingDocsCount] = useState<number>(0);
  const [pendingDocs, setPendingDocs] = useState<string[]>([]);

  const timerRef = useRef<number | null>(null);
  const stepTimerRef = useRef<number | null>(null);

  const cleanupTimers = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (stepTimerRef.current) {
      clearInterval(stepTimerRef.current);
      stepTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return cleanupTimers;
  }, [cleanupTimers]);

  // Phase 1: Show confirmation screen
  const startSyncConfirm = useCallback((docs: { id: string; status: string }[]) => {
    // Count docs in a non-terminal status
    const pendingList = docs.filter(
      d => !['ready', 'completed', 'failed', 'validation_failed'].includes(d.status.toLowerCase())
    );
    setPendingDocs(pendingList.map(d => d.id));
    setPendingDocsCount(pendingList.length);
    setSyncState('confirming');
    setError(null);
  }, []);

  // Phase 2: Send trigger sync request to API
  const confirmSync = useCallback(async () => {
    setSyncState('synchronizing');
    setCurrentStep(0);
    setProgress(0);
    setDuration(0);
    setError(null);

    try {
      const response = await triggerKnowledgeSync(pendingDocs);
      setJobId(response.job_id);

      // Start duration elapsed timer
      const startTime = Date.now();
      timerRef.current = window.setInterval(() => {
        setDuration(Math.round((Date.now() - startTime) / 1000));
      }, 1000);

      // Start pipeline step progression simulation (every 2.5 seconds, advance a step)
      let stepIndex = 0;
      stepTimerRef.current = window.setInterval(() => {
        stepIndex++;
        if (stepIndex < PIPELINE_SYNC_STEPS.length) {
          setCurrentStep(stepIndex);
          setProgress(Math.round((stepIndex / (PIPELINE_SYNC_STEPS.length - 1)) * 100));
        } else {
          // Sync completed successfully
          cleanupTimers();
          setSyncState('completed');
          onCompleted?.();
        }
      }, 2500);

    } catch (err) {
      cleanupTimers();
      setSyncState('failed');
      setError(err instanceof Error ? err.message : 'Failed to trigger chatbot brain synchronization.');
    }
  }, [pendingDocs, cleanupTimers, onCompleted]);

  const cancelSync = useCallback(() => {
    cleanupTimers();
    setSyncState('idle');
    setJobId(null);
    setError(null);
  }, [cleanupTimers]);

  const resetSync = useCallback(() => {
    cleanupTimers();
    setSyncState('idle');
    setJobId(null);
    setError(null);
    setProgress(0);
    setDuration(0);
  }, [cleanupTimers]);

  return {
    syncState,
    currentStep,
    progress,
    duration,
    jobId,
    error,
    pendingDocsCount,
    startSyncConfirm,
    confirmSync,
    cancelSync,
    resetSync
  };
}
