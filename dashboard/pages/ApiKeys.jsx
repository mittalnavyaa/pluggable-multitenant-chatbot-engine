import { KeyCard } from '../components/KeyCard.jsx';

export function ApiKeys({ keyRecords }) {
  return (
    <section className="key-grid">
      {keyRecords.map((record) => <KeyCard key={record.id} record={record} />)}
    </section>
  );
}
