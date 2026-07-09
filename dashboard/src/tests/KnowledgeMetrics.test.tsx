// dashboard/src/tests/KnowledgeMetrics.test.tsx

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { KnowledgeMetrics } from '../pages/KnowledgeMetrics';
import * as useKnowledgeMetricsHook from '../hooks/useKnowledgeMetrics';

// Mock the useKnowledgeMetrics hook
jest.mock('../hooks/useKnowledgeMetrics');

const mockUseKnowledgeMetrics = useKnowledgeMetricsHook.useKnowledgeMetrics as jest.Mock;

const mockDocs = [
  {
    id: 'doc-1',
    fileName: 'test-doc-1.pdf',
    status: 'ready',
    botId: 'bot-1',
    productId: 'tensor',
    createdAt: '2026-07-08T12:00:00Z',
    owner: 'System Ingestion',
    classification: 'Internal',
    chunkCount: 25,
    vectorCount: 25,
    processingTimeMs: 1500,
    validationStatus: 'Passed' as const,
    vectorizationStatus: 'Passed' as const
  },
  {
    id: 'doc-2',
    fileName: 'test-doc-2.docx',
    status: 'failed',
    botId: 'bot-2',
    productId: 'hr-portal',
    createdAt: '2026-07-09T09:00:00Z',
    owner: 'System Ingestion',
    classification: 'Confidential',
    chunkCount: 0,
    vectorCount: 0,
    processingTimeMs: 300,
    validationStatus: 'Failed' as const,
    vectorizationStatus: 'Failed' as const
  }
];

const mockProducts = [
  { id: 'tensor', name: 'Tensor', status: 'active', createdDate: '2026-06-18', serviceTokenStatus: 'active', serviceTokenMasked: 'svc_tensor_***', logoInitials: 'TE', branding: {} as any },
  { id: 'hr-portal', name: 'HR Portal', status: 'active', createdDate: '2026-06-23', serviceTokenStatus: 'active', serviceTokenMasked: 'svc_hr_***', logoInitials: 'HR', branding: {} as any }
];

const mockSummary = {
  totalDocuments: 2,
  completedDocuments: 1,
  failedDocuments: 1,
  processingDocuments: 0,
  totalChunks: 25,
  totalVectors: 25,
  averageChunksPerDoc: 25,
  totalStorageBytes: 153600,
  averageDocSizeBytes: 76800,
  averageChunkSizeBytes: 6144,
  activeDocuments: 1,
  validationSuccessRate: 50,
  vectorizationSuccessRate: 50,
  averageProcessingTimeMs: 1500,
  averageEmbeddingTimeMs: 600,
  queueLength: 0
};

const mockActivityFeed = [
  { id: 'ready-doc-1', type: 'ready' as const, text: 'Document vectorization completed successfully', time: '1 hr ago', docName: 'test-doc-1.pdf', product: 'Tensor' },
  { id: 'failed-doc-2', type: 'failed' as const, text: 'Document ingestion failed during processing', time: '2 hr ago', docName: 'test-doc-2.docx', product: 'HR Portal' }
];

describe('KnowledgeMetrics Workspace View', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders loading skeleton state initially', () => {
    mockUseKnowledgeMetrics.mockReturnValue({
      documents: [],
      allDocumentsRaw: [],
      totalCount: 0,
      products: [],
      loading: true,
      refreshing: false,
      error: null,
      lastSync: '12:00:00 PM',
      summary: mockSummary,
      activityFeed: [],
      searchQuery: '',
      setSearchQuery: jest.fn(),
      statusFilter: 'all',
      setStatusFilter: jest.fn(),
      productFilter: 'all',
      setProductFilter: jest.fn(),
      sortField: 'createdAt',
      sortDirection: 'desc',
      handleSort: jest.fn(),
      currentPage: 1,
      setCurrentPage: jest.fn(),
      totalPages: 1,
      refresh: jest.fn()
    });

    render(<KnowledgeMetrics />);
    
    // Check for skeleton elements
    expect(screen.queryByText('Knowledge Metrics Workspace')).toBeInTheDocument();
    expect(screen.queryByText('Total Documents')).not.toBeInTheDocument();
  });

  test('renders KPI cards and table when data loading is complete', () => {
    mockUseKnowledgeMetrics.mockReturnValue({
      documents: mockDocs,
      allDocumentsRaw: mockDocs,
      totalCount: 2,
      products: mockProducts,
      loading: false,
      refreshing: false,
      error: null,
      lastSync: '12:00:00 PM',
      summary: mockSummary,
      activityFeed: mockActivityFeed,
      searchQuery: '',
      setSearchQuery: jest.fn(),
      statusFilter: 'all',
      setStatusFilter: jest.fn(),
      productFilter: 'all',
      setProductFilter: jest.fn(),
      sortField: 'createdAt',
      sortDirection: 'desc',
      handleSort: jest.fn(),
      currentPage: 1,
      setCurrentPage: jest.fn(),
      totalPages: 1,
      refresh: jest.fn()
    });

    render(<KnowledgeMetrics />);

    // KPI Cards check
    expect(screen.getByText('Total Documents')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Chunks')).toBeInTheDocument();
    expect(screen.getByText('Storage Footprint')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Health')).toBeInTheDocument();

    // Table document names check
    expect(screen.getByText('test-doc-1.pdf')).toBeInTheDocument();
    expect(screen.getByText('test-doc-2.docx')).toBeInTheDocument();
  });

  test('renders empty state when no documents match query', () => {
    mockUseKnowledgeMetrics.mockReturnValue({
      documents: [],
      allDocumentsRaw: [],
      totalCount: 0,
      products: mockProducts,
      loading: false,
      refreshing: false,
      error: null,
      lastSync: '12:00:00 PM',
      summary: mockSummary,
      activityFeed: [],
      searchQuery: 'non-existent',
      setSearchQuery: jest.fn(),
      statusFilter: 'all',
      setStatusFilter: jest.fn(),
      productFilter: 'all',
      setProductFilter: jest.fn(),
      sortField: 'createdAt',
      sortDirection: 'desc',
      handleSort: jest.fn(),
      currentPage: 1,
      setCurrentPage: jest.fn(),
      totalPages: 1,
      refresh: jest.fn()
    });

    render(<KnowledgeMetrics />);

    expect(screen.getByText('No documents found matching search/filter criteria.')).toBeInTheDocument();
  });

  test('displays error banner on API load failure', () => {
    mockUseKnowledgeMetrics.mockReturnValue({
      documents: [],
      allDocumentsRaw: [],
      totalCount: 0,
      products: [],
      loading: false,
      refreshing: false,
      error: 'Failed to fetch documents: HTTP 500',
      lastSync: '12:00:00 PM',
      summary: mockSummary,
      activityFeed: [],
      searchQuery: '',
      setSearchQuery: jest.fn(),
      statusFilter: 'all',
      setStatusFilter: jest.fn(),
      productFilter: 'all',
      setProductFilter: jest.fn(),
      sortField: 'createdAt',
      sortDirection: 'desc',
      handleSort: jest.fn(),
      currentPage: 1,
      setCurrentPage: jest.fn(),
      totalPages: 1,
      refresh: jest.fn()
    });

    render(<KnowledgeMetrics />);

    expect(screen.getByText(/Failed to fetch documents: HTTP 500/)).toBeInTheDocument();
  });
});
