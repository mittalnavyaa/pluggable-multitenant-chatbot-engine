import { StatusBadge } from './StatusBadge.jsx';

export function SettingsCard({ setting }) {
  return (
    <section className="settings-card">
      <div>
        <span>{setting.name}</span>
        <strong>{setting.value}</strong>
        <p>{setting.detail}</p>
      </div>
      <StatusBadge status={setting.status} />
    </section>
  );
}
