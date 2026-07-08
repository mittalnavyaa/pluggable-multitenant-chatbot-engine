import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getPipelineStatus, isTerminalPipelineStatus } from '../services/pipelineService';
import type { PipelineResponse, UploadJob, PipelineStatus } from '../types/upload';
import { usePolling } from './usePolling';

function normalizePipelineResponse(response: PipelineResponse, fileName: string): UploadJob {
  // Normalize backend status to lowercase PipelineStatus
  const rawStatus = (response.status || 'queued').toLowerCase();
  const status = (rawStatus === 'completed' ? 'ready' : rawStatus) as PipelineStatus;

  // Set default progress and current step based on status
  let defaultProgress = 0;
  let defaultStep = 'Queued';
  if (status === 'uploading') {
    defaultProgress = 20;
    defaultStep = 'Uploading File';
  } else if (status === 'uploaded') {
    defaultProgress = 40;
    defaultStep = 'Uploaded';
  } else if (status === 'extracting_text') {
    defaultProgress = 60;
    defaultStep = 'Extracting Text';
  } else if (status === 'ai_formatting') {
    defaultProgress = 80;
    defaultStep = 'AI Formatting';
  } else if (status === 'generating_markdown') {
    defaultProgress = 90;
    defaultStep = 'Generating Markdown';
  } else if (status === 'ready') {
    defaultProgress = 100;
    defaultStep = 'Processing Complete';
  } else if (status === 'failed') {
    defaultProgress = 100;
    defaultStep = 'Processing Failed';
  } else if (status === 'queued') {
    defaultProgress = 10;
    defaultStep = 'Queued';
  }

  // Create a fallback timeline if not provided
  const timelineSteps: { step: PipelineStatus; label: string }[] = [
    { step: 'queued', label: 'Queued' },
    { step: 'uploading', label: 'Uploading' },
    { step: 'uploaded', label: 'Uploaded to Storage' },
    { step: 'extracting_text', label: 'Text Extraction' },
    { step: 'ai_formatting', label: 'AI Refinement' },
    { step: 'generating_markdown', label: 'Markdown Generation' },
    { step: 'ready', label: 'Ready' }
  ];

  const defaultTimeline = timelineSteps.map((s, idx) => {
    let state: 'complete' | 'active' | 'pending' | 'failed' | 'cancelled' = 'pending';
    if (status === 'failed') {
      state = 'failed';
    } else if (status === 'cancelled') {
      state = 'cancelled';
    } else {
      const currentIdx = timelineSteps.findIndex(x => x.step === status);
      if (currentIdx !== -1) {
        if (idx < currentIdx) {
          state = 'complete';
        } else if (idx === currentIdx) {
          state = 'active';
        }
      }
    }
    return {
      step: s.step,
      label: s.label,
      timestamp: '',
      state
    };
  });

  return {
    jobId: response.job_id,
    fileName,
    status,
    progress: response.progress !== undefined ? response.progress : defaultProgress,
    currentStep: response.current_step || defaultStep,
    estimatedTime: response.estimated_time || 'Unknown',
    outputFile: response.output_file,
    errorMessage: response.error_message,
    logs: response.logs || [],
    timeline: response.timeline || defaultTimeline
  };
}

export function usePipeline(activeJobId?: string, fileName = '') {
  const [job, setJob] = useState<UploadJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);
  const fileNameRef = useRef(fileName);

  useEffect(() => {
    fileNameRef.current = fileName;
  }, [fileName]);

  // Reset job when the active job changes
  useEffect(() => {
    setJob(null);
    setPollError(null);
  }, [activeJobId]);

  const refresh = useCallback(async () => {
    if (!activeJobId) return;

    setLoading(true);
    try {
      const response = await getPipelineStatus(activeJobId);
      setJob(normalizePipelineResponse(response, fileNameRef.current));
      setPollError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error('[usePipeline] Poll failed for job', activeJobId, ':', message);
      setPollError(message);
    } finally {
      setLoading(false);
    }
  }, [activeJobId]);

  const shouldPoll = useMemo(
    () => Boolean(activeJobId && (!job || !isTerminalPipelineStatus(job.status))),
    [activeJobId, job]
  );

  usePolling({
    enabled: shouldPoll,
    intervalMs: 1500,
    onPoll: refresh
  });

  return { job, loading, pollError, refresh };
}
