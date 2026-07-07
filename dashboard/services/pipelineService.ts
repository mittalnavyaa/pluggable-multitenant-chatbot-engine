import type { PipelineResponse, PipelineStatus, PipelineTimelineItem } from '../types/upload';

const API_BASE_URL = (import.meta.env.VITE_UPLOAD_API_BASE_URL as string | undefined) || '/uploads';

const terminalStatuses: PipelineStatus[] = ['ready', 'failed', 'cancelled'];

export function isTerminalPipelineStatus(status: PipelineStatus): boolean {
  return terminalStatuses.includes(status);
}

export async function getPipelineStatus(jobId: string): Promise<PipelineResponse> {
  const url = `${API_BASE_URL}/${jobId}`;
  console.log('[pipelineService] GET', url);

  const response = await fetch(url);

  console.log('[pipelineService] GET response status:', response.status, 'for job:', jobId);

  if (!response.ok) {
    const text = await response.text().catch(() => '');
    throw new Error(`Pipeline status request failed with HTTP ${response.status}: ${text}`);
  }

  const data = await response.json() as PipelineResponse;
  console.log('[pipelineService] Job', jobId, '→ status:', data.status, 'progress:', data.progress);
  return data;
}

export function getOutputDownloadUrl(jobId: string): string {
  return `${API_BASE_URL}/${jobId}/download`;
}
