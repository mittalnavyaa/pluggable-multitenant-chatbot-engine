import { useState, useEffect, useCallback } from 'react';

export function useEnterpriseDashboardData() {
  const [documentsState, setDocumentsState] = useState([]);
  const [productsState, setProductsState] = useState([]);
  const [summaryState, setSummaryState] = useState(null);

  const refreshSummary = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/dashboard/summary');
      if (response.ok) {
        const data = await response.json();
        setSummaryState(data);
      }
    } catch (err) {
      console.error('Failed to fetch dashboard summary:', err);
    }
  }, []);

  const refreshDocuments = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/documents');
      if (response.ok) {
        const data = await response.json();
        const mapped = data.map((d) => ({
          id: d.id,
          product: d.product_id ? d.product_id.charAt(0).toUpperCase() + d.product_id.slice(1) : '',
          fileName: d.filename,
          markdownFile: d.filename.split('.')[0] + '.md',
          chunkCount: 'Pending',
          embeddingStatus: d.status.toLowerCase() === 'completed' ? 'embedded' : d.status.toLowerCase(),
          uploadDate: d.created_at.split('T')[0],
          owner: 'System Ingestion',
          classification: 'Internal'
        }));
        setDocumentsState(mapped);
        refreshSummary();
      }
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    }
  }, [refreshSummary]);

  const refreshProducts = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/products');
      if (response.ok) {
        const data = await response.json();
        const mapped = data.map((p) => ({
          id: p.product_id,
          uuid: p.id,
          name: p.name,
          status: p.status || 'active',
          createdDate: p.created_at.split('T')[0],
          serviceTokenStatus: p.service_token_status || 'active',
          serviceTokenMasked: `svc_${p.product_id}_************${p.id.slice(-4).toUpperCase()}`,
          logoInitials: p.name.slice(0, 2).toUpperCase(),
          branding: p.ui_theme_config || {}
        }));
        setProductsState(mapped);
        refreshSummary();
      }
    } catch (err) {
      console.error('Failed to fetch products:', err);
    }
  }, [refreshSummary]);

  useEffect(() => {
    refreshDocuments();
    refreshProducts();
    refreshSummary();
  }, [refreshDocuments, refreshProducts, refreshSummary]);

  // TODO: Integrate actual service token database mapping when key management backend endpoints are implemented.
  const activeKeyRecords = productsState.map((product) => ({
    id: `key-${product.id}`,
    product: product.name,
    maskedKey: product.serviceTokenMasked,
    status: product.serviceTokenStatus,
    created: product.createdDate,
    lastRotated: product.createdDate
  }));

  const activeProductsCount = productsState.filter((p) => p.status === 'active').length;
  const inactiveProductsCount = productsState.filter((p) => p.status !== 'active').length;
  const markdownFiles = documentsState.filter((d) => d.markdownFile).length;

  return {
    products: productsState,
    selectedProduct: productsState[0] || null,
    documents: documentsState,
    keyRecords: activeKeyRecords,
    recentActivity: [],
    settings: [],
    refreshDocuments,
    refreshProducts,
    refreshSummary,
    metrics: {
      totalProducts: summaryState ? summaryState.total_products : productsState.length,
      activeProducts: summaryState ? summaryState.active_products : activeProductsCount,
      inactiveProducts: inactiveProductsCount,
      uploadedDocuments: summaryState ? summaryState.total_documents : documentsState.length,
      markdownFiles: summaryState ? summaryState.completed_documents : markdownFiles,
      qdrantStatus: 'Healthy',
      postgresqlStatus: 'Healthy',
      llmStatus: 'Healthy'
    }
  };
}
