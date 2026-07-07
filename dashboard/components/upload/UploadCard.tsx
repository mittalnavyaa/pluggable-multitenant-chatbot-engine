import type { UploadFile } from '../../types/upload';
import { formatFileSize, formatTimestamp } from '../../utils/uploadFormatting';
import { RetryButton } from './RetryButton';
import { StatusBadge } from './StatusBadge';

interface UploadCardProps {
  uploadFile: UploadFile;
  onRemove: (fileId: string) => void;
  onRetry: (fileId: string) => void;
  onUpload: (fileId: string) => void;
  onSelect: (fileId: string) => void;
  isUploadDisabled?: boolean;
}

export function UploadCard({ uploadFile, onRemove, onRetry, onUpload, onSelect, isUploadDisabled = false }: UploadCardProps) {
  const canUpload = uploadFile.status === 'selected' && uploadFile.validationErrors.length === 0 && !isUploadDisabled;
  const canRetry = uploadFile.status === 'failed';

  return (
    <article className="upload-card">
      <button className="upload-card__body" type="button" onClick={() => onSelect(uploadFile.id)}>
        <div>
          <h3>{uploadFile.fileName}</h3>
          <span>{uploadFile.extension.toUpperCase()} · {formatFileSize(uploadFile.size)}</span>
        </div>
        <StatusBadge status={uploadFile.status} />
      </button>
      <dl>
        <div><dt>Upload Time</dt><dd>{formatTimestamp(uploadFile.uploadTime)}</dd></div>
        <div><dt>Extension</dt><dd>{uploadFile.extension.toUpperCase()}</dd></div>
      </dl>
      {uploadFile.validationErrors.length > 0 ? (
        <ul className="upload-card__errors">
          {uploadFile.validationErrors.map((error) => <li key={error}>{error}</li>)}
        </ul>
      ) : null}
      <div className="upload-card__actions">
        <button className="upload-link-button" type="button" onClick={() => onRemove(uploadFile.id)}>Remove</button>
        <RetryButton onRetry={() => onRetry(uploadFile.id)} disabled={!canRetry} />
        {canUpload ? <button className="upload-button" type="button" onClick={() => onUpload(uploadFile.id)}>Upload</button> : null}
      </div>
    </article>
  );
}
