import React from 'react';
import { EmptyState } from '../components/scaffold/States';

export const ConversationsPlaceholder: React.FC = () => {
  return (
    <div className="page-stack" style={{ padding: '24px' }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '40px 20px',
        display: 'grid',
        placeItems: 'center',
        minHeight: '400px'
      }}>
        <EmptyState
          title="Live Chat Conversations"
          description="The conversation logs and human operator handover console will be rendered here. Active sessions can be queried in real-time."
          icon={
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          }
        />
      </div>
    </div>
  );
};

export const KnowledgeBasePlaceholder: React.FC = () => {
  return (
    <div className="page-stack" style={{ padding: '24px' }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '40px 20px',
        display: 'grid',
        placeItems: 'center',
        minHeight: '400px'
      }}>
        <EmptyState
          title="Knowledge base Articles & Qdrant Chunks"
          description="Vector embedding pipelines, semantic similarity queries, chunk editing and document ingestion status queues will be rendered here."
          icon={
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
            </svg>
          }
        />
      </div>
    </div>
  );
};

export const SalesLeadsPlaceholder: React.FC = () => {
  return (
    <div className="page-stack" style={{ padding: '24px' }}>
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '40px 20px',
        display: 'grid',
        placeItems: 'center',
        minHeight: '400px'
      }}>
        <EmptyState
          title="Sales Lead Integration & CRM Hub"
          description="Purchase intent classification filters, CRM webhook sync history, lead scoring details and assignee assignments will be rendered here."
          icon={
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          }
        />
      </div>
    </div>
  );
};

export const PlatformsPlaceholder: React.FC = () => {
  const [channels, setChannels] = React.useState([
    { id: 'web', name: 'Web Chat Widget', active: true, status: 'healthy', icon: '💬', count: '18.4K queries' },
    { id: 'slack', name: 'Slack Integration', active: true, status: 'healthy', icon: '🔌', count: '5.2K queries' },
    { id: 'discord', name: 'Discord Webhook Hub', active: true, status: 'healthy', icon: '🤖', count: '1.2K queries' },
    { id: 'telegram', name: 'Telegram Gateway', active: true, status: 'warning', icon: '✈️', count: '348 queries' },
    { id: 'teams', name: 'MS Teams Sync', active: false, status: 'offline', icon: '👥', count: '0 queries' },
    { id: 'whatsapp', name: 'WhatsApp Business API', active: false, status: 'offline', icon: '📱', count: '0 queries' }
  ]);

  const [testResult, setTestResult] = React.useState<string | null>(null);
  const [testingId, setTestingId] = React.useState<string | null>(null);

  const toggleChannel = (id: string) => {
    setChannels(prev => prev.map(ch => {
      if (ch.id === id) {
        const nextActive = !ch.active;
        return {
          ...ch,
          active: nextActive,
          status: nextActive ? 'healthy' : 'offline' as 'healthy' | 'warning' | 'offline'
        };
      }
      return ch;
    }));
  };

  const testConnection = (id: string, name: string) => {
    setTestingId(id);
    setTestResult(null);
    setTimeout(() => {
      setTestingId(null);
      setTestResult(`Successfully pinged ${name} gateway. Latency: 48ms.`);
    }, 1000);
  };

  return (
    <div className="page-stack" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <header>
        <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-text)' }}>
          Messaging Integration Gateway
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
          Configure webhooks, verify communication channels, and manage platform distribution keys.
        </p>
      </header>

      {/* Grid of integrations */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {channels.map((ch) => (
          <div key={ch.id} style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '20px' }} aria-hidden="true">{ch.icon}</span>
                <div>
                  <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700, color: 'var(--color-text)' }}>{ch.name}</h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-faint)' }}>{ch.count}</span>
                </div>
              </div>
              <button
                onClick={() => toggleChannel(ch.id)}
                type="button"
                style={{
                  background: ch.active ? 'var(--color-primary)' : 'var(--color-bg)',
                  color: ch.active ? 'var(--color-text-inverted)' : 'var(--color-text-muted)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '16px',
                  padding: '4px 12px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  transition: 'all 0.15s'
                }}
              >
                {ch.active ? 'Active' : 'Disabled'}
              </button>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              background: 'var(--color-bg)',
              padding: '8px 12px',
              borderRadius: '8px',
              fontSize: '0.75rem'
            }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Status:</span>
              <span style={{
                fontWeight: 700,
                color:
                  ch.status === 'healthy' ? 'var(--badge-success-text)' :
                  ch.status === 'warning' ? 'var(--badge-warning-text)' :
                  'var(--badge-danger-text)'
              }}>
                ● {ch.status.toUpperCase()}
              </span>
            </div>

            {ch.active && (
              <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                <button
                  onClick={() => testConnection(ch.id, ch.name)}
                  disabled={testingId !== null}
                  type="button"
                  style={{
                    flex: 1,
                    background: 'transparent',
                    border: '1px solid var(--color-border)',
                    borderRadius: '8px',
                    padding: '6px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    color: 'var(--color-text)'
                  }}
                >
                  {testingId === ch.id ? 'Testing...' : 'Test Connection'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Configuration settings form placeholder */}
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
      }}>
        <h3 style={{ margin: '0 0 16px', fontSize: '0.9375rem', fontWeight: 700, color: 'var(--color-text)' }}>
          Global Webhook configurations (Scaffold)
        </h3>
        
        {testResult && (
          <div style={{
            background: 'var(--color-primary-bg)',
            color: 'var(--color-primary)',
            padding: '10px 14px',
            borderRadius: '8px',
            fontSize: '0.8125rem',
            fontWeight: 500,
            marginBottom: '16px'
          }}>
            {testResult}
          </div>
        )}

        <form style={{ display: 'grid', gap: '16px', maxWidth: '600px' }} onSubmit={(e) => e.preventDefault()}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
              WEBHOOK OUTGOING URL
            </label>
            <input
              type="text"
              defaultValue="https://api.envoyai.internal/v1/webhooks/incoming"
              style={{
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                padding: '10px',
                fontSize: '0.875rem',
                color: 'var(--color-text)'
              }}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)' }}>
              VERIFICATION TOKEN (HMAC SECRET)
            </label>
            <input
              type="password"
              defaultValue="••••••••••••••••••••••••••••••••"
              style={{
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)',
                borderRadius: '8px',
                padding: '10px',
                fontSize: '0.875rem',
                color: 'var(--color-text)'
              }}
            />
          </div>
          <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
            <button
              type="submit"
              style={{
                background: 'var(--color-primary)',
                color: 'var(--color-text-inverted)',
                border: 'none',
                borderRadius: '8px',
                padding: '10px 20px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              Save Configurations
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
