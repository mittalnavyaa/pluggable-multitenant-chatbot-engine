import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  fetchLiveDocuments,
  fetchKnowledgeMetrics,
  fetchActivityFeed,
  type LiveDocumentInfo,
  type KnowledgeSummaryMetrics
} from '../services/knowledgeService';
import { fetchProducts, type ProductInfo } from '../services/productService';
import { usePolling } from './usePolling';

export function useKnowledgeMetrics() {
  const [documents, setDocuments] = useState<LiveDocumentInfo[]>([]);
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [backendSummary, setBackendSummary] = useState<KnowledgeSummaryMetrics | null>(null);
  const [backendActivity, setBackendActivity] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSync, setLastSync] = useState<string>(new Date().toLocaleTimeString());

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [productFilter, setProductFilter] = useState<string>('all');
  
  // Sort State
  const [sortField, setSortField] = useState<keyof LiveDocumentInfo>('createdAt');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  // Pagination State
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 5;

  const loadData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      const [docsData, prodsData, metricsData, activityData] = await Promise.all([
        fetchLiveDocuments(),
        fetchProducts(),
        fetchKnowledgeMetrics().catch(() => null),
        fetchActivityFeed().catch(() => [])
      ]);
      setDocuments(docsData);
      setProducts(prodsData);
      if (metricsData) {
        setBackendSummary(metricsData);
      }
      if (activityData && activityData.length > 0) {
        setBackendActivity(activityData);
      }
      setLastSync(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred while loading knowledge metrics.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Fetch initial data
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Dynamic Polling every 5 seconds to get updates on processing documents
  const hasProcessingDocs = useMemo(() => {
    return documents.some(
      (doc) => !['ready', 'failed', 'cancelled', 'validation_failed'].includes(doc.status.toLowerCase())
    );
  }, [documents]);

  usePolling({
    enabled: hasProcessingDocs,
    intervalMs: 5000,
    onPoll: () => loadData(true)
  });

  // Calculate dynamic metrics summary from live data
  const summary = useMemo<KnowledgeSummaryMetrics>(() => {
    const total = documents.length;
    const completed = documents.filter(d => ['ready', 'completed'].includes(d.status)).length;
    const failed = documents.filter(d => ['failed', 'validation_failed'].includes(d.status)).length;
    const processing = total - completed - failed;

    const completedDocs = documents.filter(d => d.chunkCount !== 'Pending' && d.chunkCount > 0);
    const totalChunks = completedDocs.reduce((acc, curr) => acc + (curr.chunkCount as number), 0);
    const totalVectors = completedDocs.reduce((acc, curr) => acc + (curr.vectorCount as number), 0);
    const averageChunks = completed > 0 ? Math.round(totalChunks / completed) : 0;

    // 1536 float32 dimensions per vector = 6144 bytes (~6KB)
    const totalStorage = totalVectors * 1536 * 4;
    const avgDocSize = completed > 0 ? Math.round(totalStorage / completed) : 0;
    const avgChunkSize = 1536 * 4;

    const valSuccessCount = documents.filter(d => d.validationStatus === 'Passed').length;
    const valTotalCount = documents.filter(d => d.validationStatus !== 'Pending').length;
    const validationSuccessRate = valTotalCount > 0 ? Math.round((valSuccessCount / valTotalCount) * 100) : 100;

    const vecSuccessCount = documents.filter(d => d.vectorizationStatus === 'Passed').length;
    const vecTotalCount = documents.filter(d => d.vectorizationStatus !== 'Pending').length;
    const vectorizationSuccessRate = vecTotalCount > 0 ? Math.round((vecSuccessCount / vecTotalCount) * 100) : 100;

    const completedTimes = documents.filter(d => d.processingTimeMs !== null) as { processingTimeMs: number }[];
    const avgProcTime = completedTimes.length > 0
      ? Math.round(completedTimes.reduce((acc, curr) => acc + curr.processingTimeMs, 0) / completedTimes.length)
      : 0;

    return {
      totalDocuments: total,
      completedDocuments: completed,
      failedDocuments: failed,
      processingDocuments: processing,
      totalChunks: backendSummary ? backendSummary.totalChunks : totalChunks,
      totalVectors: backendSummary ? backendSummary.totalVectors : totalVectors,
      averageChunksPerDoc: backendSummary ? backendSummary.averageChunksPerDoc : averageChunks,
      totalStorageBytes: backendSummary ? backendSummary.totalStorageBytes : totalStorage,
      averageDocSizeBytes: backendSummary ? backendSummary.averageDocSizeBytes : avgDocSize,
      averageChunkSizeBytes: backendSummary ? backendSummary.averageChunkSizeBytes : avgChunkSize,
      activeDocuments: backendSummary ? backendSummary.activeDocuments : completed,
      validationSuccessRate: backendSummary ? backendSummary.validationSuccessRate : validationSuccessRate,
      vectorizationSuccessRate: backendSummary ? backendSummary.vectorizationSuccessRate : vectorizationSuccessRate,
      averageProcessingTimeMs: backendSummary ? backendSummary.averageProcessingTimeMs : avgProcTime,
      averageEmbeddingTimeMs: backendSummary ? backendSummary.averageEmbeddingTimeMs : Math.round(avgProcTime * 0.4),
      queueLength: backendSummary ? backendSummary.queueLength : processing
    };
  }, [documents, backendSummary]);

  // Derived Activity Feed based on documents list state
  const activityFeed = useMemo(() => {
    if (backendActivity && backendActivity.length > 0) {
      return backendActivity;
    }
    const feed: { id: string; type: 'ready' | 'failed' | 'active'; text: string; time: string; docName: string; product: string }[] = [];
    
    // Sort documents by date to build feed chronologically
    const sorted = [...documents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
    
    sorted.forEach((doc) => {
      const pName = doc.productId ? doc.productId.charAt(0).toUpperCase() + doc.productId.slice(1) : 'Tensor';
      if (doc.status === 'ready') {
        feed.push({
          id: `ready-${doc.id}`,
          type: 'ready',
          text: `Document vectorization completed successfully`,
          time: 'Completed recently',
          docName: doc.fileName,
          product: pName
        });
      } else if (doc.status === 'failed') {
        feed.push({
          id: `failed-${doc.id}`,
          type: 'failed',
          text: `Document ingestion failed during processing`,
          time: 'Failed recently',
          docName: doc.fileName,
          product: pName
        });
      } else {
        feed.push({
          id: `active-${doc.id}`,
          type: 'active',
          text: `Document is currently processing in step: ${doc.status}`,
          time: 'Processing',
          docName: doc.fileName,
          product: pName
        });
      }
    });

    return feed.slice(0, 10); // Return top 10 activities
  }, [documents, backendActivity]);

  // Filter & Sort Logic
  const processedDocuments = useMemo(() => {
    let result = [...documents];

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        d => d.fileName.toLowerCase().includes(q) || d.productId.toLowerCase().includes(q)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      result = result.filter(d => d.status === statusFilter);
    }

    // Product filter
    if (productFilter !== 'all') {
      result = result.filter(d => d.productId === productFilter);
    }

    // Sorting
    result.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (aVal === null || aVal === undefined) return 1;
      if (bVal === null || bVal === undefined) return -1;

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = (bVal as string).toLowerCase();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return result;
  }, [documents, searchQuery, statusFilter, productFilter, sortField, sortDirection]);

  // Paginated Documents
  const paginatedDocuments = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return processedDocuments.slice(startIndex, startIndex + itemsPerPage);
  }, [processedDocuments, currentPage]);

  const totalPages = Math.ceil(processedDocuments.length / itemsPerPage) || 1;

  const handleSort = (field: keyof LiveDocumentInfo) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  return {
    documents: paginatedDocuments,
    allDocumentsRaw: documents,
    totalCount: processedDocuments.length,
    products,
    loading,
    refreshing,
    error,
    lastSync,
    summary,
    activityFeed,
    
    // Filtering/Searching
    searchQuery,
    setSearchQuery,
    statusFilter,
    setStatusFilter,
    productFilter,
    setProductFilter,

    // Sorting
    sortField,
    sortDirection,
    handleSort,

    // Pagination
    currentPage,
    setCurrentPage,
    totalPages,

    // Refresh action
    refresh: () => loadData(true)
  };
}
