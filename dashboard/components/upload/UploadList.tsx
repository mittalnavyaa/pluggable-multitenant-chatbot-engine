import type { UploadFile } from '../../types/upload';
import { EmptyState } from './EmptyState';
import { UploadCard } from './UploadCard';

interface UploadListProps {
  files: UploadFile[];
  onRemove: (fileId: string) => void;
  onRetry: (fileId: string) => void;
  onUpload: (fileId: string) => void;
  onSelect: (fileId: string) => void;
}

export function UploadList({ files, onRemove, onRetry, onUpload, onSelect }: UploadListProps) {
  if (files.length === 0) {
    return <EmptyState title="No files selected" description="Upload source documents to start the processing pipeline." />;
  }

  return (
    <section className="upload-list" aria-label="Selected files">
      {files.map((file) => (
        <UploadCard
          key={file.id}
          uploadFile={file}
          onRemove={onRemove}
          onRetry={onRetry}
          onUpload={onUpload}
          onSelect={onSelect}
        />
      ))}
    </section>
  );
}
