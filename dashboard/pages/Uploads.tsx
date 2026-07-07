import { useEffect, useState } from 'react';
import { DetailsModal } from '../components/upload/DetailsModal';
import { DropZone } from '../components/upload/DropZone';
import { PipelineTracker } from '../components/upload/PipelineTracker';
import { UploadButton } from '../components/upload/UploadButton';
import { UploadHistoryTable } from '../components/upload/UploadHistoryTable';
import { UploadList } from '../components/upload/UploadList';
import { usePipeline } from '../hooks/usePipeline';
import { useUpload } from '../hooks/useUpload';
import { getOutputDownloadUrl } from '../services/pipelineService';
import '../styles/upload.css';

export function Uploads() {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const {
    files,
    activeFile,
    addFiles,
    removeFile,
    retryUpload,
    startUpload,
    startAllUploads,
    syncPipelineStatus,
    setActiveFileId
  } = useUpload();

  const { job, loading, pollError } = usePipeline(activeFile?.jobId, activeFile?.fileName);

  useEffect(() => {
    if (activeFile && job) {
      syncPipelineStatus(activeFile.id, job.status);
    }
  }, [activeFile, job, syncPipelineStatus]);

  const downloadUrl = job?.status === 'ready' && job.jobId ? getOutputDownloadUrl(job.jobId) : null;

  return (
    <div className="upload-page">
      <section className="upload-page__main">
        <DropZone onFilesSelected={addFiles} />
        <div className="upload-page__toolbar">
          <div>
            <h2>Selected Files</h2>
            <p>Files are validated locally before upload submission.</p>
          </div>
          <UploadButton
            label="Upload All Valid Files"
            onClick={startAllUploads}
            disabled={files.filter((f) => ['selected', 'failed'].includes(f.status) && f.validationErrors.length === 0).length === 0}
          />
        </div>
        <UploadList
          files={files}
          onRemove={removeFile}
          onRetry={retryUpload}
          onUpload={startUpload}
          onSelect={setActiveFileId}
        />
        <section className="upload-page__history">
          <h2>Upload History</h2>
          <UploadHistoryTable files={files} />
        </section>
      </section>
      <aside className="upload-page__side">
        <PipelineTracker job={job} loading={loading} />
        {pollError ? (
          <div className="upload-page__error">
            <strong>Connection error:</strong> {pollError}
          </div>
        ) : null}
        <div className="upload-page__side-actions">
          <button className="upload-button upload-button--secondary" type="button" onClick={() => setDetailsOpen(true)} disabled={!job}>
            View Details
          </button>
          {downloadUrl ? (
            <a className="upload-button" href={downloadUrl} download>
              Download Markdown
            </a>
          ) : null}
        </div>
      </aside>
      {detailsOpen ? <DetailsModal job={job} onClose={() => setDetailsOpen(false)} /> : null}
    </div>
  );
}
