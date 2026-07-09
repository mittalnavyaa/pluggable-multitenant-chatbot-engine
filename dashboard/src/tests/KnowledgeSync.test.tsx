// dashboard/src/tests/KnowledgeSync.test.tsx

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { KnowledgeMetrics } from '../pages/KnowledgeMetrics';
import * as useKnowledgeMetricsHook from '../hooks/useKnowledgeMetrics';
import * as useKnowledgeSyncHook from '../hooks/useKnowledgeSync';

jest.mock('../hooks/useKnowledgeMetrics');
jest.mock('../hooks/useKnowledgeSync');

const mockUseKnowledgeMetrics = useKnowledgeMetricsHook.useKnowledgeMetrics as jest.Mock;
const mockUseKnowledgeSync = useKnowledgeSyncHook.useKnowledgeSync as jest.Mock;

const mockDocs = [
  { id: '1', fileName: 'test-1.pdf', status: 'downloading', botId: 'bot-1', productId: 'tensor', createdAt: '2026-07-08T12:00:00Z', owner: 'System Ingestion', classification: 'Internal', chunkCount: 'Pending', vectorCount: 'Pending', processingTimeMs: null, validationStatus: 'Pending', vectorizationStatus: 'Pending' }
];

const defaultMetricsState = {
  documents: mockDocs,
  allDocumentsRaw: mockDocs,
  totalCount: 1,
  products: [],
  loading: false,
  refreshing: false,
  error: null,
  lastSync: '12:00:00 PM',
  summary: { totalDocuments: 1, completedDocuments: 0, failedDocuments: 0, processingDocuments: 1, totalChunks: 0, totalVectors: 0, averageChunksPerDoc: 0, totalStorageBytes: 0, averageDocSizeBytes: 0, averageChunkSizeBytes: 6144, activeDocuments: 0, validationSuccessRate: 100, vectorizationSuccessRate: 100, averageProcessingTimeMs: 0, averageEmbeddingTimeMs: 0, queueLength: 1 },
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
};

describe('KnowledgeSync UI Triggers', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseKnowledgeMetrics.mockReturnValue(defaultMetricsState);
  });

  test('renders Synchronize Brain button in idle state', () => {
    mockUseKnowledgeSync.mockReturnValue({
      syncState: 'idle',
      currentStep: 0,
      progress: 0,
      duration: 0,
      jobId: null,
      error: null,
      pendingDocsCount: 0,
      startSyncConfirm: jest.fn(),
      confirmSync: jest.fn(),
      cancelSync: jest.fn(),
      resetSync: jest.fn()
    });

    render(<KnowledgeMetrics />);
    
    const syncBtn = screen.getByRole('button', { name: /Synchronize Brain/ });
    expect(syncBtn).toBeInTheDocument();
    expect(syncBtn).not.toBeDisabled();
  });

  test('shows confirmation modal dialog when state transitions to confirming', () => {
    const startSyncConfirmMock = jest.fn();
    mockUseKnowledgeSync.mockReturnValue({
      syncState: 'confirming',
      currentStep: 0,
      progress: 0,
      duration: 0,
      jobId: null,
      error: null,
      pendingDocsCount: 1,
      startSyncConfirm: startSyncConfirmMock,
      confirmSync: jest.fn(),
      cancelSync: jest.fn(),
      resetSync: jest.fn()
    });

    render(<KnowledgeMetrics />);

    // Dialog heading
    expect(screen.getByText('Confirm Knowledge Sync')).toBeInTheDocument();
    expect(screen.getByText(/Pending Documents:/)).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
    
    // Confirm and Cancel action buttons
    expect(screen.getByRole('button', { name: 'Confirm Sync' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Cancel' })).toBeInTheDocument();
  });

  test('displays progress tracker panel during active synchronizing state', () => {
    mockUseKnowledgeSync.mockReturnValue({
      syncState: 'synchronizing',
      currentStep: 2, // Semantic Chunking step
      progress: 40,
      duration: 12,
      jobId: 'sync-job-xyz',
      error: null,
      pendingDocsCount: 1,
      startSyncConfirm: jest.fn(),
      confirmSync: jest.fn(),
      cancelSync: jest.fn(),
      resetSync: jest.fn()
    });

    render(<KnowledgeMetrics />);

    expect(screen.getByText('Synchronizing Chatbot Brain...')).toBeInTheDocument();
    expect(screen.getByText('Job ID: sync-job-xyz')).toBeInTheDocument();
    expect(screen.getByText('40%')).toBeInTheDocument();
    expect(screen.getByText('Elapsed Time: 0:12')).toBeInTheDocument();

    // Check step list
    expect(screen.getByText('Semantic Chunking')).toBeInTheDocument();
  });

  test('displays success notification banner on complete state', () => {
    const resetSyncMock = jest.fn();
    mockUseKnowledgeSync.mockReturnValue({
      syncState: 'completed',
      currentStep: 5,
      progress: 100,
      duration: 25,
      jobId: 'sync-job-xyz',
      error: null,
      pendingDocsCount: 1,
      startSyncConfirm: jest.fn(),
      confirmSync: jest.fn(),
      cancelSync: jest.fn(),
      resetSync: resetSyncMock
    });

    render(<KnowledgeMetrics />);

    expect(screen.getByText(/Chatbot brain synchronized successfully/)).toBeInTheDocument();
  });

  test('shows failure banner with retry action on failed state', () => {
    const confirmSyncMock = jest.fn();
    mockUseKnowledgeSync.mockReturnValue({
      syncState: 'failed',
      currentStep: 3,
      progress: 60,
      duration: 15,
      jobId: 'sync-job-xyz',
      error: 'API Gateway Timeout',
      pendingDocsCount: 1,
      startSyncConfirm: jest.fn(),
      confirmSync: confirmSyncMock,
      cancelSync: jest.fn(),
      resetSync: jest.fn()
    });

    render(<KnowledgeMetrics />);

    expect(screen.getByText(/Synchronization Failed: API Gateway Timeout/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument();
  });
});
