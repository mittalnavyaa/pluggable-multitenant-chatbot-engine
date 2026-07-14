// dashboard/src/tests/AnalyticsWorkspace.test.tsx

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { AnalyticsWorkspace } from '../pages/AnalyticsWorkspace';
import * as useAnalyticsDataHook from '../hooks/useAnalyticsData';
import * as productServiceHook from '../services/productService';

// Mock the hooks and services
jest.mock('../hooks/useAnalyticsData');
jest.mock('../services/productService');

const mockUseAnalyticsData = useAnalyticsDataHook.useAnalyticsData as jest.Mock;
const mockFetchProducts = productServiceHook.fetchProducts as jest.Mock;

const mockProducts = [
  { id: 'tensor', uuid: 'uuid-tensor', name: 'Tensor Product', status: 'active', createdDate: '2026-06-18', serviceTokenStatus: 'active', serviceTokenMasked: 'svc_tensor_***', logoInitials: 'TE', branding: {} as any },
  { id: 'hr-portal', uuid: 'uuid-hr', name: 'HR Portal', status: 'active', createdDate: '2026-06-23', serviceTokenStatus: 'active', serviceTokenMasked: 'svc_hr_***', logoInitials: 'HR', branding: {} as any }
];

const mockVolume = [
  { timestamp: '2026-07-14T00:00:00Z', conversation_count: 15, message_count: 60 }
];

const mockResolution = {
  total_conversations: 25,
  resolved_conversations: 20,
  resolution_rate_percent: 80.0
};

const mockDistribution = [
  { intent: 'PRICING', count: 12 },
  { intent: 'SUPPORT', count: 8 }
];

const mockLeads = [
  { session_id: 'sess-1', platform_id: 'web', bot_id: 'bot-1', intent: 'PRICING', lead_status: 'NEW', first_message_at: '2026-07-14T12:00:00Z', total_token_usage: 45 }
];

const mockPlatform = [
  { platform_id: 'web', bot_id: 'bot-1', total_conversations: 25, total_messages: 100, average_latency_ms: 220.0, resolved_conversations: 20, sales_leads: 1 }
];

const mockActivity = [
  { id: 'act-1', timestamp: '2026-07-14T12:00:00Z', document_name: 'terms.pdf', product_id: 'tensor', event_type: 'COMPLETED', description: 'Processed' }
];

describe('AnalyticsWorkspace View', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFetchProducts.mockResolvedValue(mockProducts);
  });

  test('renders loading skeleton state initially', () => {
    mockUseAnalyticsData.mockReturnValue({
      loading: true,
      refreshing: false,
      error: null,
      wsStatus: 'connecting',
      knowledgeMetrics: null,
      conversationVolume: [],
      resolutionRate: null,
      intentDistribution: [],
      salesLeads: [],
      platformSummary: [],
      recentActivity: [],
      bots: [],
      refresh: jest.fn()
    });

    render(<AnalyticsWorkspace />);
    
    // Check loading grids
    const totalConvCard = screen.getByLabelText(/Loading Total Conversations/);
    expect(totalConvCard).toBeInTheDocument();
  });

  test('renders KPI cards and filters when data loads successfully', async () => {
    mockUseAnalyticsData.mockReturnValue({
      loading: false,
      refreshing: false,
      error: null,
      wsStatus: 'connected',
      knowledgeMetrics: { total_chunks: 120, total_vectors: 120, average_chunks_per_document: 12, total_storage_bytes: 737280, validation_success_rate_percent: 100, vectorization_success_rate_percent: 100, average_processing_time_ms: 1200, average_embedding_time_ms: 480, queue_length: 0 },
      conversationVolume: mockVolume,
      resolutionRate: mockResolution,
      intentDistribution: mockDistribution,
      salesLeads: mockLeads,
      platformSummary: mockPlatform,
      recentActivity: mockActivity,
      bots: [],
      refresh: jest.fn()
    });

    render(<AnalyticsWorkspace />);

    // Verify KPI summary counts
    expect(screen.getByText('Total Conversations')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();

    expect(screen.getByText('Avg Response Time')).toBeInTheDocument();
    expect(screen.getByText('220ms')).toBeInTheDocument();

    expect(screen.getByText('Resolution Rate')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();

    expect(screen.getByText('Qualified Sales Leads')).toBeInTheDocument();

    // Verify filter displays
    expect(screen.getByLabelText('Select Tenant Workspace')).toBeInTheDocument();
    expect(screen.getByLabelText('Select Date Range Filter')).toBeInTheDocument();
  });

  test('displays error banner on analytics API load failure', () => {
    mockUseAnalyticsData.mockReturnValue({
      loading: false,
      refreshing: false,
      error: 'Failed to connect to database query pipeline: HTTP 503',
      wsStatus: 'polling',
      knowledgeMetrics: null,
      conversationVolume: [],
      resolutionRate: null,
      intentDistribution: [],
      salesLeads: [],
      platformSummary: [],
      recentActivity: [],
      bots: [],
      refresh: jest.fn()
    });

    render(<AnalyticsWorkspace />);

    expect(screen.getByText(/Failed to connect to database query pipeline: HTTP 503/)).toBeInTheDocument();
  });

  test('filters change event fires callback', () => {
    mockUseAnalyticsData.mockReturnValue({
      loading: false,
      refreshing: false,
      error: null,
      wsStatus: 'connected',
      knowledgeMetrics: null,
      conversationVolume: [],
      resolutionRate: mockResolution,
      intentDistribution: [],
      salesLeads: [],
      platformSummary: [],
      recentActivity: [],
      bots: [],
      refresh: jest.fn()
    });

    render(<AnalyticsWorkspace />);

    const tenantSelect = screen.getByLabelText('Select Tenant Workspace') as HTMLSelectElement;
    fireEvent.change(tenantSelect, { target: { value: 'tensor' } });
    expect(tenantSelect.value).toBe('tensor');
  });
});
