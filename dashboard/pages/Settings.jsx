import { SettingsCard } from '../components/SettingsCard.jsx';

export function Settings({ settings }) {
  return (
    <section className="settings-grid settings-grid--large">
      {settings.map((setting) => <SettingsCard key={setting.name} setting={setting} />)}
    </section>
  );
}
