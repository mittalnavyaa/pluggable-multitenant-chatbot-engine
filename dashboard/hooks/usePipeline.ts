import { useCallback, useMemo, useState } from 'react';
import { getPipelineStatus, isTerminalPipelineStatus } from '../services/pipelineService';
import type { PipelineResponse, UploadJob } from '../types/upload';
import { usePolling } from './usePolling';

function normalizePipelineResponse(response: PipelineResponse, fileName: string): UploadJob {
  return {
    jobId: response.job_id,
    fileName,
    status: response.status,
    progress: response.progress,
    currentStep: response.current_step,
    estimatedTime: response.estimated_time,
    outputFile: response.output_file,
    errorMessage: response.error_message,
    logs: response.logs,
    timeline: response.timeline
  };
}

export function usePipeline(activeJobId?: string, fileName = '') {
  const [job, setJob] = useState<UploadJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [pollError, setPollError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!activeJobId) return;

    setLoading(true);
    try {
      const response = await getPipelineStatus(activeJobId);
      setJob(normalizePipelineResponse(response, fileName));
      setPollError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error('[usePipeline] Poll failed for job', activeJobId, ':', message);
      setPollError(message);
    } finally {
      setLoading(false);
    }
  }, [activeJobId, fileName]);

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
