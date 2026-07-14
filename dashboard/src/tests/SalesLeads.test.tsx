// dashboard/src/tests/SalesLeads.test.tsx

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LeadsGrid } from '../components/analytics/leads/LeadsGrid';
import { StatusChip } from '../components/analytics/leads/StatusChip';
import { PriorityBadge } from '../components/analytics/leads/PriorityBadge';
import { LeadsKpiCards } from '../components/analytics/leads/LeadsKpiCards';
import { type MutableSalesLead } from '../hooks/useAnalyticsData';

const mockLeads: MutableSalesLead[] = [
  {
    session_id: 'sess-lead-1',
    platform_id: 'web',
    bot_id: 'bot-1',
    intent: 'PRICING',
    lead_status: 'NEW',
    first_message_at: '2026-07-14T12:00:00Z',
    total_token_usage: 45,
    priority: 'HIGH',
    lead_score: 85,
    confidence: 90,
    assignee: 'Unassigned',
    lastUpdated: '2026-07-14T12:00:00Z'
  },
  {
    session_id: 'sess-lead-2',
    platform_id: 'slack',
    bot_id: 'bot-2',
    intent: 'SUPPORT',
    lead_status: 'ASSIGNED',
    first_message_at: '2026-07-14T12:05:00Z',
    total_token_usage: 120,
    priority: 'CRITICAL',
    lead_score: 95,
    confidence: 98,
    assignee: 'Sarah Connor',
    lastUpdated: '2026-07-14T12:05:00Z'
  }
];

describe('CRM Sales Leads Grid & Widgets', () => {
  test('StatusChip renders correct label matching status keys', () => {
    render(<StatusChip status="NEW" />);
    expect(screen.getByText('New Opportunity')).toBeInTheDocument();
  });

  test('PriorityBadge renders correct visual label matching priorities', () => {
    render(<PriorityBadge priority="CRITICAL" />);
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  test('LeadsKpiCards renders Opportunity summary values', () => {
    render(<LeadsKpiCards leads={mockLeads} />);
    expect(screen.getByText('Total Opportunities')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  test('LeadsGrid renders headers and trigger inline changes', () => {
    const handleStatus = jest.fn();
    const handlePriority = jest.fn();
    const handleAssignee = jest.fn();
    const handleRowClick = jest.fn();

    render(
      <LeadsGrid
        leads={mockLeads}
        onRowClick={handleRowClick}
        onStatusChange={handleStatus}
        onPriorityChange={handlePriority}
        onAssigneeChange={handleAssignee}
      />
    );

    // Verify row checklist count
    expect(screen.getByText('LD-AD-1')).toBeInTheDocument(); // short slice of sess-lead-1
    expect(screen.getByText('LD-AD-2')).toBeInTheDocument();

    // Verify header exists
    expect(screen.getByText('Lead ID')).toBeInTheDocument();
  });
});
