// dashboard/pages/AnalyticsWorkspace.tsx

import React, { useState, useEffect, useMemo } from 'react';
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

// CRM Leads Dashboard imports
import { LeadsKpiCards } from '../components/analytics/leads/LeadsKpiCards';
import { LeadFilters, type LeadFilterState } from '../components/analytics/leads/LeadFilters';
import { LeadsGrid } from '../components/analytics/leads/LeadsGrid';
import { LeadDetailsPanel } from '../components/analytics/leads/LeadDetailsPanel';
import { LeadsActivityTimeline } from '../components/analytics/leads/LeadsActivityTimeline';

export const AnalyticsWorkspace: React.FC = () => {
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<string>('7d');

  // Workspace tab switcher
  const [activeTab, setActiveTab] = useState<'overview' | 'leads'>('overview');

  // Selected lead for detail panel drawer
  const [selectedLeadSessionId, setSelectedLeadSessionId] = useState<string | null>(null);

  // Leads Grid filters state
  const [leadFilters, setLeadFilters] = useState<LeadFilterState>({
    search: '',
    tenant: 'all',
    platform: 'all',
    priority: 'all',
    status: 'all',
    assignee: 'all',
    minScore: 0,
    maxScore: 100,
    minConfidence: 0,
    maxConfidence: 100
  });

  // Load products list on mount
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
    refresh,
    updateLeadStatus,
    updateLeadPriority,
    updateLeadAssignee
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
      recent_activity: recentActivity
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

  // Filtering leads on client side
  const filteredLeads = useMemo(() => {
    return salesLeads.filter((lead) => {
      // 1. Text search
      if (leadFilters.search.trim()) {
        const q = leadFilters.search.toLowerCase();
        const matchesSearch =
          lead.session_id.toLowerCase().includes(q) ||
          lead.intent.toLowerCase().includes(q) ||
          (lead.platform_id && lead.platform_id.toLowerCase().includes(q));
        if (!matchesSearch) return false;
      }

      // 2. Tenant matching (maps bot_id if product matching is active)
      if (leadFilters.tenant !== 'all') {
        const matchingBot = bots.find((b) => b.product_id === leadFilters.tenant);
        if (matchingBot && lead.bot_id !== matchingBot.id) return false;
      }

      // 3. Dropdowns selectors
      if (leadFilters.platform !== 'all' && lead.platform_id !== leadFilters.platform) return false;
      if (leadFilters.priority !== 'all' && lead.priority !== leadFilters.priority) return false;
      if (leadFilters.status !== 'all' && lead.lead_status !== leadFilters.status) return false;
      if (leadFilters.assignee !== 'all' && lead.assignee !== leadFilters.assignee) return false;

      // 4. Ranges
      if (lead.lead_score < leadFilters.minScore || lead.lead_score > leadFilters.maxScore) return false;
      if (lead.confidence < leadFilters.minConfidence || lead.confidence > leadFilters.maxConfidence) return false;

      return true;
    });
  }, [salesLeads, leadFilters, bots]);

  const selectedLead = useMemo(() => {
    return salesLeads.find((l) => l.session_id === selectedLeadSessionId) || null;
  }, [salesLeads, selectedLeadSessionId]);

  return (
    <div className="page-stack" style={{ padding: '4px 0 24px' }}>
      
      {/* Workspace Tab Switcher Header */}
      <div
        className="analytics-tabs-header"
        style={{
          display: 'flex',
          gap: '12px',
          borderBottom: '1px solid var(--color-border)',
          marginBottom: '20px',
          paddingBottom: '2px'
        }}
      >
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'overview' ? '3px solid var(--color-primary)' : '3px solid transparent',
            color: activeTab === 'overview' ? 'var(--color-text)' : 'var(--color-text-muted)',
            fontWeight: activeTab === 'overview' ? 700 : 500,
            fontSize: '15px',
            padding: '8px 16px',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          aria-pressed={activeTab === 'overview'}
        >
          Overview Dashboard
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('leads')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'leads' ? '3px solid var(--color-primary)' : '3px solid transparent',
            color: activeTab === 'leads' ? 'var(--color-text)' : 'var(--color-text-muted)',
            fontWeight: activeTab === 'leads' ? 700 : 500,
            fontSize: '15px',
            padding: '8px 16px',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
          aria-pressed={activeTab === 'leads'}
        >
          Sales Leads Manager
        </button>
      </div>

      {activeTab === 'overview' ? (
        <>
          {/* Overviews Tab: Filters, KPIs and Charts */}
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

          {error && (
            <div className="kpi-card kpi-card--error" style={{ marginBottom: '24px', minHeight: 'auto' }}>
              <div className="kpi-card__error-msg">Ingestion Connection Issue Detected</div>
              <span className="kpi-card__detail" style={{ color: 'var(--badge-danger-text)' }}>
                {error}. Falling back to cached operations schema.
              </span>
            </div>
          )}

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

          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
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

            <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '24px' }}>
              <ChartContainer title="LLM Latency Percentiles (P50, P95, P99)" loading={loading}>
                <LatencyChart data={liveLatencyPoints} height={180} />
              </ChartContainer>

              <ChartContainer title="Sales Lead Funnel Progression" loading={loading}>
                <LeadAnalyticsChart leadsCount={salesLeads.length} height={180} />
              </ChartContainer>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.6fr 1fr', gap: '24px' }}>
              <ConversationTable bots={bots} selectedProductId={selectedProductId} loading={loading} />
              <LiveActivityTimeline events={timelineEvents} loading={loading} />
            </div>

            <HealthPanel wsStatus={wsStatus} loading={loading} />
          </div>
        </>
      ) : (
        <>
          {/* CRM Leads Workspace Tab View */}
          <LeadsKpiCards leads={salesLeads} loading={loading} />
          
          {/* Advanced Query Selector Toolbar */}
          <LeadFilters products={products} onFiltersChange={setLeadFilters} />

          {/* Table Data Grid & Leads Activity Timeline log splits */}
          <div style={{ display: 'grid', gridTemplateColumns: '2.5fr 1fr', gap: '24px', alignItems: 'start' }}>
            <LeadsGrid
              leads={filteredLeads}
              onRowClick={(lead) => setSelectedLeadSessionId(lead.session_id)}
              onStatusChange={updateLeadStatus}
              onPriorityChange={updateLeadPriority}
              onAssigneeChange={updateLeadAssignee}
            />

            <LeadsActivityTimeline events={timelineEvents} loading={loading} />
          </div>

          {/* Slide-out detail inspector panel */}
          <LeadDetailsPanel
            lead={selectedLead}
            onClose={() => setSelectedLeadSessionId(null)}
            onStatusChange={(status) => selectedLead && updateLeadStatus(selectedLead.session_id, status)}
            onPriorityChange={(priority) => selectedLead && updateLeadPriority(selectedLead.session_id, priority)}
            onAssigneeChange={(assignee) => selectedLead && updateLeadAssignee(selectedLead.session_id, assignee)}
          />
        </>
      )}
    </div>
  );
};
export default AnalyticsWorkspace;
