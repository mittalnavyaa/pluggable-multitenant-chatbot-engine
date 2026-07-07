import type { PipelineStatus, UploadFileStatus } from '../../types/upload';

interface StatusBadgeProps {
  status: PipelineStatus | UploadFileStatus | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const label = String(status).replace(/_/g, ' ');
  const className = String(status).replace(/_/g, '-');

  return <span className={`upload-status upload-status--${className}`}>{label}</span>;
}
