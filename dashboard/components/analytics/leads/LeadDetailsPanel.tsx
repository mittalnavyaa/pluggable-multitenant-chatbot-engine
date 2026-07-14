// dashboard/components/analytics/leads/LeadDetailsPanel.tsx

import React from 'react';
import { type MutableSalesLead } from '../../../hooks/useAnalyticsData';
import { StatusChip } from './StatusChip';
import { PriorityBadge } from './PriorityBadge';

interface LeadDetailsPanelProps {
  lead: MutableSalesLead | null;
  onClose: () => void;
  onStatusChange: (status: string) => void;
  onPriorityChange: (priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW') => void;
  onAssigneeChange: (assignee: string) => void;
}

export const LeadDetailsPanel: React.FC<LeadDetailsPanelProps> = ({
  lead,
  onClose,
  onStatusChange,
  onPriorityChange,
  onAssigneeChange
}) => {
  if (!lead) return null;

  const leadIdShort = `LD-${lead.session_id.slice(-4).toUpperCase()}`;

  // Mock conversation transcript timeline
  const mockTranscript = [
    { sender: 'user', text: 'Hi, I need pricing information for the multi-tenant chatbot system.', time: '12:01' },
    { sender: 'bot', text: 'Hello! Our multi-tenant engine pricing starts at $499/mo with dedicated Redis pipelines and metadata scoping for complete data isolation. Would you like a demo?', time: '12:02' },
    { sender: 'user', text: 'Yes, I would like to schedule a custom demo for my engineering team of 80.', time: '12:04' }
  ];

  return (
    <div
      className="lead-details-overlay"
      style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '450px',
        maxWidth: '100%',
        height: '100vh',
        background: 'var(--color-surface)',
        borderLeft: '1px solid var(--color-border)',
        boxShadow: '-8px 0 24px rgba(15, 23, 42, 0.15)',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        animation: 'slide-in-kf 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        outline: 'none'
      }}
      role="dialog"
      aria-modal="true"
      aria-label={`Lead details for ${leadIdShort}`}
    >
      {/* Panel Header */}
      <div
        style={{
          padding: '16px 20px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: 'var(--color-text)' }}>
            {leadIdShort} Details
          </h3>
          <span style={{ fontSize: '11px', color: 'var(--color-text-faint)' }}>
            Session ID: {lead.session_id}
          </span>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close Inspector drawer"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-muted)',
            cursor: 'pointer',
            fontSize: '20px',
            padding: '4px'
          }}
        >
          &times;
        </button>
      </div>

      {/* Panel Body */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* KPI Score widgets */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
          <div style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Lead Score</span>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--color-primary)', marginTop: '4px' }}>
              {lead.lead_score}%
            </div>
          </div>
          <div style={{ background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: '8px', padding: '12px', textAlign: 'center' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Confidence</span>
            <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--badge-success-text)', marginTop: '4px' }}>
              {lead.confidence}%
            </div>
          </div>
        </div>

        {/* Status Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Actions</h4>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }}>
            {/* Status select */}
            <div>
              <label htmlFor="inspector-status" style={{ fontSize: '10px', color: 'var(--color-text-faint)' }}>STATUS</label>
              <select
                id="inspector-status"
                className="filter-select"
                value={lead.lead_status || 'NEW'}
                onChange={(e) => onStatusChange(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              >
                <option value="NEW">New</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="CONTACTED">Contacted</option>
                <option value="FOLLOW_UP_SCHEDULED">Follow-up</option>
                <option value="QUALIFIED">Qualified</option>
                <option value="CONVERTED">Converted</option>
                <option value="CLOSED">Closed</option>
                <option value="LOST">Lost</option>
              </select>
            </div>

            {/* Owner select */}
            <div>
              <label htmlFor="inspector-assignee" style={{ fontSize: '10px', color: 'var(--color-text-faint)' }}>OWNER</label>
              <select
                id="inspector-assignee"
                className="filter-select"
                value={lead.assignee}
                onChange={(e) => onAssigneeChange(e.target.value)}
                style={{ width: '100%', marginTop: '4px' }}
              >
                <option value="Unassigned">Unassigned</option>
                <option value="Sarah Connor">Sarah Connor</option>
                <option value="John Doe">John Doe</option>
                <option value="Alice Smith">Alice Smith</option>
                <option value="Bob Johnson">Bob Johnson</option>
              </select>
            </div>
          </div>
        </div>

        {/* Lead Metadata parameters */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Metadata Parameters</h4>
          <div style={{ border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--color-border)', fontSize: '12px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Channel Platform</span>
              <span style={{ fontWeight: 600, color: 'var(--color-text)', textTransform: 'uppercase' }}>{lead.platform_id}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--color-border)', fontSize: '12px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Intent Class</span>
              <span style={{ fontWeight: 600, color: 'var(--color-primary)' }}>{lead.intent}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', borderBottom: '1px solid var(--color-border)', fontSize: '12px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Lead Priority</span>
              <span><PriorityBadge priority={lead.priority} /></span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', fontSize: '12px' }}>
              <span style={{ color: 'var(--color-text-muted)' }}>Tokens Consumed</span>
              <span style={{ fontWeight: 600 }}>{lead.total_token_usage} tokens</span>
            </div>
          </div>
        </div>

        {/* Conversation summary explanation */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Lead Qualification Context</h4>
          <p style={{ margin: 0, fontSize: '12px', lineHeight: 1.5, color: 'var(--color-text-muted)' }}>
            Qualified via prompt orchestrator telemetry parser checking keywords containing: <strong>pricing, purchasing, demo</strong>. Lead score aggregates user size indicator keywords.
          </p>
        </div>

        {/* Message Transcript */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <h4 style={{ margin: 0, fontSize: '12px', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Dialogue History Log</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '10px 0' }}>
            {mockTranscript.map((t, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignSelf: t.sender === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%'
                }}
              >
                <div
                  style={{
                    background: t.sender === 'user' ? 'var(--color-primary)' : 'var(--color-bg)',
                    color: t.sender === 'user' ? '#ffffff' : 'var(--color-text)',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    fontSize: '12px',
                    border: t.sender === 'user' ? 'none' : '1px solid var(--color-border)',
                    lineHeight: 1.4
                  }}
                >
                  {t.text}
                </div>
                <span style={{ fontSize: '9px', color: 'var(--color-text-faint)', marginTop: '2px', textAlign: t.sender === 'user' ? 'right' : 'left' }}>
                  {t.time}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
export default LeadDetailsPanel;
