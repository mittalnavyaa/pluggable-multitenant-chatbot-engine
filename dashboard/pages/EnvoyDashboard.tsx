import React, { useState } from 'react';
import '../styles/scaffold.css';
import {
  mockKPIMetrics,
  mockSalesLeads,
  mockConversations,
  mockKnowledgeMetrics,
  mockPlatformHealth,
  mockLineChartData,
  mockAreaChartData,
  mockBarChartData,
  mockPieChartData,
  mockHeatmapData,
  mockTimelineEvents
} from '../mock/dashboardMockData';
import { KPICard } from '../components/scaffold/KPICard';
import { ChartPlaceholder } from '../components/scaffold/ChartPlaceholder';
import { LeadTable } from '../components/scaffold/LeadTable';
import { ActivityFeed } from '../components/scaffold/ActivityFeed';
import { KnowledgeMetricsWidget } from '../components/scaffold/KnowledgeMetricsWidget';
import { PlatformHealthWidget } from '../components/scaffold/PlatformHealthWidget';

export const EnvoyDashboard: React.FC = () => {
  // Scaffolding UI states toggles (for developer preview)
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);
  const [empty, setEmpty] = useState(false);

  const handleRetry = () => {
    setError(false);
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 800);
  };

  return (
    <div className="page-stack scaffold-grid">
      {/* Welcome Banner and State Preview Controller */}
      <header
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          paddingBottom: '8px',
          borderBottom: '1px solid var(--color-border)'
        }}
      >
        <div>
          <p className="dashboard-welcome" style={{ margin: 0 }}>
            Good morning — here is your Envoy AI operations control panel.
          </p>
          <h2 style={{ margin: '4px 0 0', fontSize: '1.25rem', fontWeight: 800, color: 'var(--color-text)' }}>
            System Analytics Canvas
          </h2>
        </div>

        {/* State Preview Toggle Bar */}
        <div
          className="scaffold-controls"
          style={{
            display: 'flex',
            gap: '8px',
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            padding: '6px 12px',
            borderRadius: '10px',
            alignItems: 'center'
          }}
        >
          <span style={{ fontSize: '0.6875rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--color-text-muted)', marginRight: '4px' }}>
            Scaffold Controls:
          </span>
          <button
            onClick={() => setLoading(!loading)}
            style={{
              background: loading ? 'var(--color-primary)' : 'var(--color-bg)',
              color: loading ? 'var(--color-text-inverted)' : 'var(--color-text)',
              border: '1px solid var(--color-border)',
              padding: '4px 8px',
              fontSize: '0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            {loading ? 'Skeletons ON' : 'Show Skeletons'}
          </button>
          <button
            onClick={() => setError(!error)}
            style={{
              background: error ? 'var(--badge-danger-text)' : 'var(--color-bg)',
              color: error ? 'var(--color-text-inverted)' : 'var(--color-text)',
              border: '1px solid var(--color-border)',
              padding: '4px 8px',
              fontSize: '0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            {error ? 'Errors ON' : 'Show Errors'}
          </button>
          <button
            onClick={() => setEmpty(!empty)}
            style={{
              background: empty ? 'var(--color-primary-dark)' : 'var(--color-bg)',
              color: empty ? 'var(--color-text-inverted)' : 'var(--color-text)',
              border: '1px solid var(--color-border)',
              padding: '4px 8px',
              fontSize: '0.75rem',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            {empty ? 'Empty States ON' : 'Show Empty'}
          </button>
        </div>
      </header>

      {/* KPI CARDS ROW */}
      <section className="kpi-row" aria-label="Key Performance Indicators">
        {mockKPIMetrics.map((metric) => (
          <KPICard
            key={metric.id}
            title={metric.title}
            value={metric.value}
            trend={metric.trend}
            trendLabel={metric.trendLabel}
            tooltip={metric.tooltip}
            loading={loading}
          />
        ))}
      </section>

      {/* CHARTS SECTION */}
      <section aria-label="Analytical Visualizations">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 14px' }}>Reporting Graphs</h3>
        <div className="chart-grid">
          <ChartPlaceholder
            title="Conversations Load (Hourly)"
            type="line"
            badgeText="Line Chart"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockLineChartData}
          />

          <ChartPlaceholder
            title="Operator Handoff vs AI Resolution"
            type="area"
            badgeText="Area Chart"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockAreaChartData}
          />

          <ChartPlaceholder
            title="Interaction Volume by Channel"
            type="bar"
            badgeText="Bar Chart"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockBarChartData}
          />

          <ChartPlaceholder
            title="Customer Request Intent Distribution"
            type="pie"
            badgeText="Pie Chart"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockPieChartData}
          />

          <ChartPlaceholder
            title="Channel Request Density Profile"
            type="heatmap"
            badgeText="Heatmap"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockHeatmapData}
          />

          <ChartPlaceholder
            title="Operational System Alerts Timeline"
            type="timeline"
            badgeText="Timeline Logs"
            loading={loading}
            error={error}
            empty={empty}
            onRetry={handleRetry}
            data={mockTimelineEvents}
          />
        </div>
      </section>

      {/* SALES LEADS & LIVE CONVERSATION FEED */}
      <section className="secondary-grid" aria-label="Operational Live Feeds">
        {/* Sales Leads Queue Panel */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '14px', minHeight: '380px' }}>
          <div className="panel__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: 0 }}>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700 }}>CRM Sales Leads Queue</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Real-time Hot Classified</span>
          </div>
          <div style={{ flex: 1 }}>
            <LeadTable
              leads={empty ? [] : mockSalesLeads}
              loading={loading}
              error={error}
              onRetry={handleRetry}
            />
          </div>
        </div>

        {/* Live Conversation Feed Panel */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '14px', minHeight: '380px' }}>
          <div className="panel__header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', margin: 0 }}>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700 }}>Conversation Telemetry Feed</h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--badge-success-text)', fontWeight: 600 }}>● Active</span>
          </div>
          <div style={{ flex: 1, overflowY: 'auto' }}>
            {error ? (
              <div style={{ height: '100%', position: 'relative' }}>
                <ChartPlaceholder title="" type="stream" loading={false} error={true} onRetry={handleRetry} />
              </div>
            ) : (
              <ActivityFeed
                conversations={empty ? [] : mockConversations}
                loading={loading}
              />
            )}
          </div>
        </div>
      </section>

      {/* KNOWLEDGE INDEX & PLATFORM HEALTH */}
      <section className="tertiary-grid" aria-label="System Metrics & Integration Health">
        {/* Knowledge Metrics Panel */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="panel__header" style={{ margin: 0 }}>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700 }}>Knowledge Base Indexing Profile</h3>
          </div>
          <KnowledgeMetricsWidget
            metrics={mockKnowledgeMetrics}
            loading={loading}
          />
        </div>

        {/* Platforms Connection Health */}
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div className="panel__header" style={{ margin: 0 }}>
            <h3 style={{ margin: 0, fontSize: '0.9375rem', fontWeight: 700 }}>Platform Connection Status</h3>
          </div>
          <PlatformHealthWidget
            platforms={mockPlatformHealth}
            loading={loading}
          />
        </div>
      </section>
    </div>
  );
};
