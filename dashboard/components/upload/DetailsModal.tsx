import type { UploadJob } from '../../types/upload';

interface DetailsModalProps {
  job: UploadJob | null;
  onClose: () => void;
}

export function DetailsModal({ job, onClose }: DetailsModalProps) {
  if (!job) return null;

  return (
    <div className="upload-modal" role="dialog" aria-modal="true" aria-label="Upload details">
      <div className="upload-modal__content">
        <div className="upload-modal__header">
          <h2>{job.fileName}</h2>
          <button className="upload-link-button" type="button" onClick={onClose}>Close</button>
        </div>
        <pre>{JSON.stringify(job, null, 2)}</pre>
      </div>
    </div>
  );
}
