import { StatusBadge } from './StatusBadge.jsx';

export function DocumentTable({ documents }) {
  return (
    <div className="table-wrap">
      <table className="document-table">
        <thead>
          <tr>
            <th>Uploaded File</th>
            <th>Markdown File</th>
            <th>Chunks</th>
            <th>Embedding Status</th>
            <th>Upload Date</th>
            <th>Owner</th>
            <th>Classification</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.id}>
              <td>{document.fileName}</td>
              <td>{document.markdownFile}</td>
              <td>{document.chunkCount}</td>
              <td><StatusBadge status={document.embeddingStatus} /></td>
              <td>{document.uploadDate}</td>
              <td>{document.owner}</td>
              <td>{document.classification}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
