export type PipelineStatus =
  | 'queued'
  | 'uploading'
  | 'uploaded'
  | 'extracting_text'
  | 'ai_formatting'
  | 'generating_markdown'
  | 'ready'
  | 'failed'
  | 'cancelled';

export type PipelineStepId =
  | 'queued'
  | 'uploading'
  | 'uploaded'
  | 'extracting_text'
  | 'ai_formatting'
  | 'generating_markdown'
  | 'ready';

export type UploadFileStatus = 'selected' | 'invalid' | 'queued' | 'uploading' | 'processing' | 'ready' | 'failed' | 'cancelled';

export interface PipelineStep {
  id: PipelineStepId;
  label: string;
}

export interface UploadFile {
  id: string;
  file: File;
  fileName: string;
  extension: 'pdf' | 'docx' | 'txt' | string;
  size: number;
  uploadTime: string;
  status: UploadFileStatus;
  validationErrors: string[];
  jobId?: string;
}

export interface UploadJob {
  jobId: string;
  fileName: string;
  status: PipelineStatus;
  progress: number;
  currentStep: string;
  estimatedTime: string;
  outputFile?: string;
  errorMessage?: string;
  logs: string[];
  timeline: PipelineTimelineItem[];
}

export interface PipelineTimelineItem {
  step: PipelineStatus;
  label: string;
  timestamp: string;
  state: 'complete' | 'active' | 'pending' | 'failed' | 'cancelled';
}

export interface UploadResponse {
  job_id: string;
  status: PipelineStatus;
}

export interface PipelineResponse {
  job_id: string;
  status: PipelineStatus;
  progress: number;
  current_step: string;
  estimated_time: string;
  output_file?: string;
  error_message?: string;
  logs: string[];
  timeline: PipelineTimelineItem[];
}

export interface UploadValidationConfig {
  maxFileSizeBytes: number;
  supportedExtensions: string[];
}
