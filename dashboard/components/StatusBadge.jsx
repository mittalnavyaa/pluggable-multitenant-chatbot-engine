export function StatusBadge({ status }) {
  const normalized = String(status).toLowerCase();
  return <span className={`status-badge status-badge--${normalized}`}>{status}</span>;
}
