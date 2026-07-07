import type { UploadFile } from '../../types/upload';
import { formatFileSize, formatTimestamp } from '../../utils/uploadFormatting';
import { StatusBadge } from './StatusBadge';

interface UploadHistoryTableProps {
  files: UploadFile[];
}

export function UploadHistoryTable({ files }: UploadHistoryTableProps) {
  return (
    <div className="upload-history">
      <table>
        <thead>
          <tr>
            <th>File Name</th>
            <th>Extension</th>
            <th>File Size</th>
            <th>Upload Time</th>
            <th>Status</th>
            <th>Job ID</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.id}>
              <td>{file.fileName}</td>
              <td>{file.extension.toUpperCase()}</td>
              <td>{formatFileSize(file.size)}</td>
              <td>{formatTimestamp(file.uploadTime)}</td>
              <td><StatusBadge status={file.status} /></td>
              <td>{file.jobId || 'Not submitted'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
