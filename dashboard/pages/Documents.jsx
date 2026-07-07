import { DocumentTable } from '../components/DocumentTable.jsx';
import { SearchBar } from '../components/SearchBar.jsx';

export function Documents({ documents }) {
  return (
    <div className="page-stack">
      <div className="page-toolbar">
        <SearchBar placeholder="Search uploaded or markdown files" />
        <span>{documents.length} document records</span>
      </div>
      <DocumentTable documents={documents} />
    </div>
  );
}
