import { useCallback, useMemo, useState } from 'react';
import { toUploadFile, uploadFile } from '../services/uploadService';
import type { PipelineStatus, UploadFile, UploadFileStatus } from '../types/upload';

const pipelineToFileStatus: Partial<Record<PipelineStatus, UploadFileStatus>> = {
  queued: 'queued',
  uploading: 'uploading',
  uploaded: 'processing',
  extracting_text: 'processing',
  ai_formatting: 'processing',
  generating_markdown: 'processing',
  ready: 'ready',
  failed: 'failed',
  cancelled: 'cancelled'
};

export function useUpload() {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [activeFileId, setActiveFileId] = useState<string | undefined>();

  const activeFile = useMemo(() => files.find((file) => file.id === activeFileId) || files.find((file) => file.jobId), [activeFileId, files]);

  const addFiles = useCallback((incomingFiles: File[]) => {
    setFiles((currentFiles) => {
      const nextFiles = [...currentFiles];
      incomingFiles.forEach((file) => {
        nextFiles.push(toUploadFile(file, nextFiles));
      });
      return nextFiles;
    });
  }, []);

  const removeFile = useCallback((fileId: string) => {
    setFiles((currentFiles) => currentFiles.filter((file) => file.id !== fileId));
    setActiveFileId((current) => (current === fileId ? undefined : current));
  }, []);

  const startUpload = useCallback(async (fileId: string) => {
    const targetFile = files.find((file) => file.id === fileId);
    if (!targetFile) return;

    setFiles((currentFiles) => currentFiles.map((file) => file.id === fileId ? { ...file, status: 'uploading' } : file));

    try {
      const response = await uploadFile(targetFile);
      setFiles((currentFiles) => currentFiles.map((file) => (
        file.id === fileId
          ? { ...file, status: 'processing', jobId: response.job_id }
          : file
      )));
      setActiveFileId(fileId);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error('[useUpload] Upload failed for', targetFile.fileName, ':', message);
      setFiles((currentFiles) => currentFiles.map((file) => file.id === fileId ? { ...file, status: 'failed' } : file));
    }
  }, [files]);

  const retryUpload = useCallback((fileId: string) => {
    startUpload(fileId);
  }, [startUpload]);

  const startAllUploads = useCallback(() => {
    files
      .filter((file) => ['selected', 'failed'].includes(file.status) && file.validationErrors.length === 0)
      .forEach((file) => {
        startUpload(file.id);
      });
  }, [files, startUpload]);

  const syncPipelineStatus = useCallback((fileId: string, status: PipelineStatus) => {
    const nextStatus = pipelineToFileStatus[status];
    if (!nextStatus) return;

    setFiles((currentFiles) => currentFiles.map((file) => {
      if (file.id !== fileId || file.status === nextStatus) return file;
      return { ...file, status: nextStatus };
    }));
  }, []);

  return {
    files,
    activeFile,
    addFiles,
    removeFile,
    retryUpload,
    startUpload,
    startAllUploads,
    syncPipelineStatus,
    setActiveFileId
  };
}
