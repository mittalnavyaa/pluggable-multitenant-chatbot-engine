import { StatusBadge } from './StatusBadge.jsx';

export function KeyCard({ record }) {
  return (
    <article className="key-card">
      <div>
        <h3>{record.product}</h3>
        <p>{record.maskedKey}</p>
      </div>
      <StatusBadge status={record.status} />
      <dl className="metadata-list metadata-list--inline">
        <div>
          <dt>Created</dt>
          <dd>{record.created}</dd>
        </div>
        <div>
          <dt>Last Rotated</dt>
          <dd>{record.lastRotated}</dd>
        </div>
      </dl>
      <div className="action-row">
        <button className="button button--secondary" type="button">Rotate</button>
        <button className="button button--danger" type="button">Disable</button>
        <button className="button" type="button">Generate</button>
      </div>
    </article>
  );
}
