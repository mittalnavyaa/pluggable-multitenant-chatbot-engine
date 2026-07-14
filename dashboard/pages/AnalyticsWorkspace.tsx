// dashboard/pages/AnalyticsWorkspace.tsx

import React, { useState, useEffect } from 'react';
import { useAnalyticsData } from '../hooks/useAnalyticsData';
import { fetchProducts, type ProductInfo } from '../services/productService';
import { DashboardFilters } from '../components/analytics/DashboardFilters';
import { KpiCard } from '../components/analytics/KpiCard';
import { ConversationTable } from '../components/analytics/ConversationTable';
import { HealthPanel } from '../components/analytics/HealthPanel';

// Visualization modules imports
import { ChartContainer } from '../components/analytics/charts/ChartContainer';
import { LineChart } from '../components/analytics/charts/LineChart';
import { AreaChart } from '../components/analytics/charts/AreaChart';
import { BarChart } from '../components/analytics/charts/BarChart';
import { PieDonutChart } from '../components/analytics/charts/PieDonutChart';
import { IntentHeatmap } from '../components/analytics/charts/IntentHeatmap';
import { LatencyChart } from '../components/analytics/charts/LatencyChart';
import { LeadAnalyticsChart } from '../components/analytics/charts/LeadAnalyticsChart';
import { LiveActivityTimeline } from '../components/analytics/charts/LiveActivityTimeline';

export const AnalyticsWorkspace: React.FC = () => {
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<string>('7d');

  // Load products selector options on mount
  useEffect(() => {
    fetchProducts()
      .then((data) => {
        setProducts(data);
        setSelectedProductId(null);
      })
      .catch((err) => console.error('Failed to load products selector:', err));
  }, []);

  // Ingest live data hook
  const {
    loading,
    refreshing,
    error,
    wsStatus,
    knowledgeMetrics,
    conversationVolume,
    resolutionRate,
    intentDistribution,
    salesLeads,
    platformSummary,
    recentActivity,
    bots,
    timelineEvents,
    liveLatencyPoints,
    liveVolumePoints,
    refresh
  } = useAnalyticsData(selectedProductId, dateRange);

  // Compute average response latency from summary
  const totalConversations = platformSummary.reduce((acc, curr) => acc + curr.total_conversations, 0);
  const avgLatency =
    totalConversations > 0
      ? platformSummary.reduce((acc, curr) => acc + curr.average_latency_ms * curr.total_conversations, 0) /
        totalConversations
      : 320.0;

  // Handle data export action to JSON file
  const handleExport = () => {
    const reportData = {
      tenant: selectedProductId || 'all_tenants',
      timeframe: dateRange,
      generatedAt: new Date().toISOString(),
      metrics: {
        total_conversations: resolutionRate?.total_conversations || 0,
        resolved_conversations: resolutionRate?.resolved_conversations || 0,
        resolution_rate_percent: resolutionRate?.resolution_rate_percent || 100.0,
        average_latency_ms: avgLatency,
        knowledge_chunks: knowledgeMetrics?.total_chunks || 0,
        sales_leads_count: salesLeads.length
      },
      conversation_volume: conversationVolume,
      intent_distribution: intentDistribution,
      sales_leads: salesLeads,
      platform_summary: platformSummary,
      recent_activity: recentActivity,
      live_telemetry: {
        latency_stream: liveLatencyPoints,
        volume_stream: liveVolumePoints,
        timeline_stream: timelineEvents
      }
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics_report_${selectedProductId || 'all'}_${dateRange}_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Convert platform summary to simple array shape for BarChart
  const activePlatformsBarData = platformSummary.map((p) => ({
    platform: p.platform_id.toUpperCase(),
    conversations: p.total_conversations
  }));

  return (
    <div className="page-stack" style={{ padding: '4px 0 24px' }}>
      {/* Filters Toolbar */}
      <DashboardFilters
        products={products}
        selectedProductId={selectedProductId}
        onTenantChange={setSelectedProductId}
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        wsStatus={wsStatus}
        refreshing={refreshing}
        onRefresh={refresh}
        onExport={handleExport}
      />

      {/* Error Banner */}
      {error && (
        <div className="kpi-card kpi-card--error" style={{ marginBottom: '24px', minHeight: 'auto' }}>
          <div className="kpi-card__error-msg">Ingestion Connection Issue Detected</div>
          <span className="kpi-card__detail" style={{ color: 'var(--badge-danger-text)' }}>
            {error}. Falling back to cached operations schema.
          </span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <section className="kpi-grid" aria-label="KPI Performance Summary">
        <KpiCard
          label="Total Conversations"
          value={resolutionRate?.total_conversations}
          loading={loading}
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M7.5 10.5l2 2 3.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          }
          trend={{ value: 12.8, isPositive: true }}
          detail="Total live chatbot sessions"
        />

        <KpiCard
          label="Avg Response Time"
          value={loading ? undefined : `${avgLatency.toFixed(0)}ms`}
          loading={loading}
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2v4l2.5 2.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
              <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5"/>
            </svg>
          }
          trend={{ value: 4.5, isPositive: true }}
          detail="First-token generation time"
        />

        <KpiCard
          label="Resolution Rate"
          value={resolutionRate ? `${resolutionRate.resolution_rate_percent.toFixed(1)}%` : undefined}
          loading={loading}
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M13 8.5L9.5 12 7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          }
          trend={{ value: 1.2, isPositive: true }}
          detail="Solved sessions without handoff"
        />

        <KpiCard
          label="Knowledge Base Chunks"
          value={knowledgeMetrics?.total_chunks}
          loading={loading}
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <rect x="4" y="2" width="12" height="16" rx="2" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M7 6h6M7 10h6M7 14h3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          }
          detail="Total vectorized context segments"
        />

        <KpiCard
          label="Qualified Sales Leads"
          value={salesLeads.length}
          loading={loading}
          icon={
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M2 15.5l5.5-6.5 4 4L18 5.5m-3 0h3v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          }
          trend={{ value: 24.0, isPositive: true }}
          detail="Inquiries flagged for outreach"
        />
      </section>

      {/* Visualizations Panels Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* ROW 1: Real-Time Stream (Line) + Intent Segment (Pie) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1.6fr 1fr))', gap: '24px' }}>
          <div style={{ gridColumn: 'span 2' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '24px' }}>
              <ChartContainer title="Live Stream: Conversations per Minute" loading={loading} onExport={handleExport}>
                <LineChart
                  data={liveVolumePoints}
                  series={[{ key: 'count', color: 'var(--color-primary)', label: 'Conversations / min' }]}
                  xKey="time"
                  height={180}
                />
              </ChartContainer>

              <ChartContainer title="User Intent Ratios" loading={loading}>
                <PieDonutChart
                  data={intentDistribution}
                  dataKey="count"
                  nameKey="intent"
                  height={180}
                />
              </ChartContainer>
            </div>
          </div>
        </div>

        {/* ROW 2: Activity Heatmap + Channels Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          <ChartContainer title="Intent Activity Weekday Heatmap" loading={loading}>
            <IntentHeatmap data={intentDistribution} loading={loading} />
          </ChartContainer>

          <ChartContainer title="Most Active Channels" loading={loading}>
            <BarChart
              data={activePlatformsBarData}
              dataKey="conversations"
              nameKey="platform"
              horizontal={true}
              color="var(--badge-success-text)"
              height={180}
            />
          </ChartContainer>
        </div>

        {/* ROW 3: Latency Percentiles + Funnel */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '24px' }}>
          <ChartContainer title="LLM Latency Percentiles (P50, P95, P99)" loading={loading}>
            <LatencyChart data={liveLatencyPoints} height={180} />
          </ChartContainer>

          <ChartContainer title="Sales Lead Funnel Progression" loading={loading}>
            <LeadAnalyticsChart leadsCount={salesLeads.length} height={180} />
          </ChartContainer>
        </div>

        {/* ROW 4: Table logs + Live Activity Timeline */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '24px' }}>
          <ConversationTable bots={bots} selectedProductId={selectedProductId} loading={loading} />
          <LiveActivityTimeline events={timelineEvents} loading={loading} />
        </div>

        {/* Health status */}
        <HealthPanel wsStatus={wsStatus} loading={loading} />
      </div>
    </div>
  );
};
export default AnalyticsWorkspace;
