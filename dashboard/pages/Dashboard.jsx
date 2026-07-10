import { SettingsCard } from '../components/SettingsCard.jsx';
import { StatsCard } from '../components/StatsCard.jsx';

export function Dashboard({ data }) {
  const { metrics, recentActivity, settings } = data;

  return (
    <div className="page-stack">
      <p className="dashboard-welcome">Good morning — here's your platform overview.</p>
      <section className="stats-grid">
        <StatsCard label="Total Products" value={metrics.totalProducts} detail="Registered internal products" />
        <StatsCard label="Active Products" value={metrics.activeProducts} detail="Available for chatbot requests" variant="success" />
        <StatsCard label="Inactive Products" value={metrics.inactiveProducts} detail="Blocked from service access" variant="danger" />
        <StatsCard label="Uploaded Documents" value={metrics.uploadedDocuments} detail="Source files in ingestion scope" />
        <StatsCard label="Markdown Files" value={metrics.markdownFiles} detail="Cleaned files ready for chunking" variant="info" />
      </section>
      <section className="content-grid">
        <div className="panel">
          <div className="panel__header">
            <h2>Recent Activity</h2>
            <a href="/uploads" className="panel__link">View all</a>
          </div>
          <ol className="activity-feed">
            {recentActivity.length === 0 ? (
              <li className="activity-feed__empty">No recent activity.</li>
            ) : recentActivity.map((item) => (
              <li key={item.id} className={`activity-feed__item activity-feed__item--${item.type}`}>
                <span className="activity-feed__dot" aria-hidden="true" />
                <div className="activity-feed__body">
                  <span className="activity-feed__text">{item.text}</span>
                  <time className="activity-feed__time">{item.time}</time>
                </div>
              </li>
            ))}
          </ol>
        </div>
        <div className="panel">
          <div className="panel__header">
            <h2>Platform Health</h2>
            <a href="/settings" className="panel__link">View all</a>
          </div>
          <div className="settings-grid">
            {settings.length === 0 ? (
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>No settings data available.</p>
            ) : settings.slice(0, 3).map((setting) => <SettingsCard key={setting.name} setting={setting} />)}
          </div>
        </div>
      </section>
    </div>
  );
}
