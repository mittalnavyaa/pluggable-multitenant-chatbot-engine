// dashboard/components/analytics/leads/LeadsKpiCards.tsx

import React from 'react';
import { type MutableSalesLead } from '../../../hooks/useAnalyticsData';
import { KpiCard } from '../KpiCard';

interface LeadsKpiCardsProps {
  leads: MutableSalesLead[];
  loading?: boolean;
}

export const LeadsKpiCards: React.FC<LeadsKpiCardsProps> = ({
  leads = [],
  loading = false
}) => {
  const total = leads.length;
  const hotLeads = leads.filter((l) => l.priority === 'CRITICAL' || l.priority === 'HIGH').length;
  const qualified = leads.filter((l) => l.lead_status === 'QUALIFIED').length;
  const converted = leads.filter((l) => l.lead_status === 'CONVERTED').length;
  const pending = leads.filter((l) => l.lead_status === 'NEW' || l.lead_status === 'ASSIGNED').length;

  const avgScore = total > 0 ? Math.round(leads.reduce((sum, l) => sum + l.lead_score, 0) / total) : 0;
  const avgConfidence = total > 0 ? Math.round(leads.reduce((sum, l) => sum + l.confidence, 0) / total) : 0;

  return (
    <section className="kpi-grid" aria-label="Sales Leads Key Metrics Summary" style={{ marginBottom: '24px' }}>
      {/* Total Leads */}
      <KpiCard
        label="Total Opportunities"
        value={total}
        loading={loading}
        icon={
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M7.5 10.5l2 2 3.5-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        }
        detail="High intent chats flagged"
      />

      {/* Hot Opportunities */}
      <KpiCard
        label="Hot Leads (Crit/High)"
        value={hotLeads}
        loading={loading}
        icon={
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M17.5 11.5c-.8-1.5-2.2-2.5-3.8-2.8a4 4 0 0 0-7.4 0c-1.6.3-3 1.3-3.8 2.8M10 17v-4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        }
        detail="Leads requiring immediate action"
      />

      {/* Average Lead Score */}
      <KpiCard
        label="Avg Lead Score"
        value={loading ? undefined : `${avgScore}%`}
        loading={loading}
        icon={
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M10 5v5l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        }
        detail="Mean opportunity score"
      />

      {/* Average Confidence */}
      <KpiCard
        label="Avg Confidence"
        value={loading ? undefined : `${avgConfidence}%`}
        loading={loading}
        icon={
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M13 8.5L9.5 12 7 9.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        }
        detail="Intent classifier confidence"
      />

      {/* Pending Outreach */}
      <KpiCard
        label="Pending Outreach"
        value={pending}
        loading={loading}
        icon={
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M2 15.5l5.5-6.5 4 4L18 5.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
        }
        detail="New or unassigned statuses"
      />
    </section>
  );
};
export default LeadsKpiCards;
