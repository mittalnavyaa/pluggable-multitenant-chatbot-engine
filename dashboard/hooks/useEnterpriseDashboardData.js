import { useState, useEffect, useCallback } from 'react';

const sharedBranding = {
  backgroundColor: '#F8FAFC',
  surfaceColor: '#FFFFFF',
  textColor: '#111827',
  mutedTextColor: '#64748B',
  successColor: '#15803D',
  warningColor: '#B45309',
  errorColor: '#B91C1C',
  fontFamily: 'Inter, Arial, sans-serif',
  headingWeight: 600,
  bodyWeight: 400,
  borderRadius: '8px',
  spacing: '16px',
  shadow: '0 16px 40px rgba(15, 23, 42, 0.16)',
  maxWidth: '420px',
  buttonStyle: 'filled',
  buttonRadius: '8px',
  contrastMode: 'standard',
  darkModeSupported: false,
  version: '1.0.0'
};

const mockProducts = [
  {
    id: 'tensor',
    name: 'Tensor',
    status: 'active',
    createdDate: '2026-06-18',
    serviceTokenStatus: 'active',
    serviceTokenMasked: 'svc_tensor_************7A3F',
    logoInitials: 'TE',
    branding: {
      ...sharedBranding,
      primaryColor: '#2563EB',
      secondaryColor: '#0F766E',
      accentColor: '#14B8A6',
      widgetTitle: 'Tensor Assistant',
      launcherLabel: 'Open Tensor Assistant',
      welcomeMessage: 'Ask Tensor Assistant about analytics, models, report definitions, and approved operating metrics.',
      placeholderText: 'Ask about reports, metrics, or models',
      logoUrl: '/assets/branding/tensor.svg',
      faviconUrl: '/assets/branding/tensor.ico',
      updatedAt: '2026-07-06T09:30:00Z'
    }
  },
  {
    id: 'admissions',
    name: 'Admissions Portal',
    status: 'active',
    createdDate: '2026-06-20',
    serviceTokenStatus: 'active',
    serviceTokenMasked: 'svc_admissions_************1C8E',
    logoInitials: 'AD',
    branding: {
      ...sharedBranding,
      primaryColor: '#0F766E',
      secondaryColor: '#0369A1',
      accentColor: '#F59E0B',
      widgetTitle: 'Admissions Help Desk',
      launcherLabel: 'Open Admissions Help Desk',
      welcomeMessage: 'Welcome. I can help with admissions eligibility, application status, required documents, scholarships, and important deadlines.',
      placeholderText: 'Ask about admissions, documents, or deadlines',
      logoUrl: '/assets/branding/admissions.svg',
      faviconUrl: '/assets/branding/admissions.ico',
      updatedAt: '2026-07-06T09:30:00Z'
    }
  },
  {
    id: 'internal-support',
    name: 'Internal Support',
    status: 'active',
    createdDate: '2026-06-21',
    serviceTokenStatus: 'rotating',
    serviceTokenMasked: 'svc_support_************94B2',
    logoInitials: 'IS',
    branding: {
      ...sharedBranding,
      primaryColor: '#334155',
      secondaryColor: '#2563EB',
      accentColor: '#22C55E',
      widgetTitle: 'Support Assistant',
      launcherLabel: 'Open Support Assistant',
      welcomeMessage: 'Ask about IT help, access requests, devices, workplace support, and approved service procedures.',
      placeholderText: 'Ask about support or access requests',
      logoUrl: '/assets/branding/internal-support.svg',
      faviconUrl: '/assets/branding/internal-support.ico',
      updatedAt: '2026-07-05T12:10:00Z'
    }
  },
  {
    id: 'hr-portal',
    name: 'HR Portal',
    status: 'active',
    createdDate: '2026-06-23',
    serviceTokenStatus: 'active',
    serviceTokenMasked: 'svc_hr_portal_************5F01',
    logoInitials: 'HR',
    branding: {
      ...sharedBranding,
      primaryColor: '#7C3AED',
      secondaryColor: '#1D4ED8',
      accentColor: '#F59E0B',
      widgetTitle: 'HR Assistant',
      launcherLabel: 'Open HR Assistant',
      welcomeMessage: 'Ask about policies, leave, benefits, onboarding, employee services, and approved HR procedures.',
      placeholderText: 'Ask about policies, leave, or benefits',
      logoUrl: '/assets/branding/hr-portal.svg',
      faviconUrl: '/assets/branding/hr-portal.ico',
      updatedAt: '2026-07-04T14:20:00Z'
    }
  },
  {
    id: 'placement-cell',
    name: 'Placement Cell',
    status: 'active',
    createdDate: '2026-06-24',
    serviceTokenStatus: 'active',
    serviceTokenMasked: 'svc_placement_************E410',
    logoInitials: 'PC',
    branding: {
      ...sharedBranding,
      primaryColor: '#0369A1',
      secondaryColor: '#0F766E',
      accentColor: '#DC2626',
      widgetTitle: 'Placement Assistant',
      launcherLabel: 'Open Placement Assistant',
      welcomeMessage: 'Ask about placement drives, eligibility, interview schedules, offer process, and placement policies.',
      placeholderText: 'Ask about drives, schedules, or offers',
      logoUrl: '/assets/branding/placement-cell.svg',
      faviconUrl: '/assets/branding/placement-cell.ico',
      updatedAt: '2026-07-03T10:05:00Z'
    }
  },
  {
    id: 'website-analyzer',
    name: 'Website Analyzer',
    status: 'active',
    createdDate: '2026-06-25',
    serviceTokenStatus: 'active',
    serviceTokenMasked: 'svc_web_analyzer_************6B28',
    logoInitials: 'WA',
    branding: {
      ...sharedBranding,
      primaryColor: '#0E7490',
      secondaryColor: '#334155',
      accentColor: '#84CC16',
      widgetTitle: 'Website Analyzer Assistant',
      launcherLabel: 'Open Website Analyzer Assistant',
      welcomeMessage: 'Ask about SEO audits, crawl reports, page insights, indexing issues, and optimization recommendations.',
      placeholderText: 'Ask about crawl reports or SEO insights',
      logoUrl: '/assets/branding/website-analyzer.svg',
      faviconUrl: '/assets/branding/website-analyzer.ico',
      updatedAt: '2026-07-02T16:45:00Z'
    }
  },
  {
    id: 'knowledge-base',
    name: 'Knowledge Base',
    status: 'inactive',
    createdDate: '2026-06-28',
    serviceTokenStatus: 'disabled',
    serviceTokenMasked: 'svc_knowledge_************D902',
    logoInitials: 'KB',
    branding: {
      ...sharedBranding,
      primaryColor: '#1D4ED8',
      secondaryColor: '#0F766E',
      accentColor: '#059669',
      widgetTitle: 'Knowledge Assistant',
      launcherLabel: 'Open Knowledge Assistant',
      welcomeMessage: 'Search enterprise knowledge, operating procedures, internal guides, and approved reference material.',
      placeholderText: 'Search enterprise knowledge',
      logoUrl: '/assets/branding/knowledge-base.svg',
      faviconUrl: '/assets/branding/knowledge-base.ico',
      updatedAt: '2026-07-01T11:25:00Z'
    }
  }
];

const documents = [
  { id: 'doc-001', product: 'Tensor', fileName: 'analytics-metric-catalog.pdf', markdownFile: 'analytics-metric-catalog.md', chunkCount: 184, embeddingStatus: 'embedded', uploadDate: '2026-07-05', owner: 'Data Platform', classification: 'Internal' },
  { id: 'doc-002', product: 'Admissions Portal', fileName: 'admissions-policy-2026.pdf', markdownFile: 'admissions-policy-2026.md', chunkCount: 96, embeddingStatus: 'embedded', uploadDate: '2026-07-04', owner: 'Admissions Office', classification: 'Internal' },
  { id: 'doc-003', product: 'HR Portal', fileName: 'employee-handbook.pdf', markdownFile: 'employee-handbook.md', chunkCount: 142, embeddingStatus: 'embedded', uploadDate: '2026-07-04', owner: 'Human Resources', classification: 'Confidential' },
  { id: 'doc-004', product: 'Website Analyzer', fileName: 'seo-audit-playbook.pdf', markdownFile: 'seo-audit-playbook.md', chunkCount: 78, embeddingStatus: 'queued', uploadDate: '2026-07-06', owner: 'Digital Experience', classification: 'Internal' },
  { id: 'doc-005', product: 'Placement Cell', fileName: 'campus-drive-process.docx', markdownFile: 'campus-drive-process.md', chunkCount: 64, embeddingStatus: 'embedded', uploadDate: '2026-07-03', owner: 'Career Services', classification: 'Internal' }
];

const keyRecords = []; // deprecated static array, calculated dynamically inside hook

const recentActivity = [
  { id: 1, type: 'warning', text: 'Website Analyzer document embedding queued for seo-audit-playbook.pdf', time: '2 min ago' },
  { id: 2, type: 'warning', text: 'Internal Support service token entered rotation window', time: '18 min ago' },
  { id: 3, type: 'info',    text: 'Admissions Portal branding updated to schema version 1.0.0', time: '1 hr ago' },
  { id: 4, type: 'success', text: 'HR Portal employee handbook embeddings completed', time: '3 hr ago' }
];

const settings = [
  { name: 'Database', value: 'PostgreSQL 16', status: 'healthy', detail: 'Primary connection pool available' },
  { name: 'Qdrant', value: 'Qdrant Vector Store', status: 'healthy', detail: 'Collection chatbot_knowledge responding' },
  { name: 'LLM', value: 'Enterprise LLM Gateway', status: 'healthy', detail: 'Completion and embedding routes available' },
  { name: 'Storage', value: 'Internal Object Storage', status: 'healthy', detail: 'Document uploads available' },
  { name: 'Environment', value: 'Production', status: 'healthy', detail: 'Internal network only' },
  { name: 'System Version', value: '2026.07.06', status: 'healthy', detail: 'Dashboard layout package' }
];

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
          product: d.product_id ? d.product_id.charAt(0).toUpperCase() + d.product_id.slice(1) : 'Tensor',
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
        const mapped = data.map((p) => {
          const mockProd = mockProducts.find(m => m.id === p.product_id);
          const defaultBranding = mockProd ? mockProd.branding : sharedBranding;
          
          return {
            id: p.product_id,
            uuid: p.id,
            name: p.name,
            status: mockProd ? mockProd.status : 'active',
            createdDate: p.created_at.split('T')[0],
            serviceTokenStatus: mockProd ? mockProd.serviceTokenStatus : 'active',
            serviceTokenMasked: mockProd ? mockProd.serviceTokenMasked : `svc_${p.product_id}_************${p.id.slice(-4).toUpperCase()}`,
            logoInitials: mockProd ? mockProd.logoInitials : p.name.slice(0, 2).toUpperCase(),
            branding: {
              ...defaultBranding,
              ...(p.ui_theme_config || {})
            }
          };
        });
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

  const activeProducts = productsState.length > 0 ? productsState : mockProducts;
  const activeDocuments = documentsState.length > 0 ? documentsState : [];

  // TODO: Integrate actual service token database mapping when key management backend endpoints are implemented.
  const activeKeyRecords = activeProducts.map((product, index) => ({
    id: `key-${product.id}`,
    product: product.name,
    maskedKey: product.serviceTokenMasked,
    status: product.serviceTokenStatus,
    created: product.createdDate,
    lastRotated: index === 2 ? '2026-07-06' : '2026-06-30'
  }));

  const activeProductsCount = activeProducts.filter((product) => product.status === 'active').length;
  const inactiveProductsCount = activeProducts.filter((product) => product.status !== 'active').length;
  const markdownFiles = activeDocuments.filter((document) => document.markdownFile).length;

  return {
    products: activeProducts,
    selectedProduct: activeProducts[1] || activeProducts[0],
    documents: activeDocuments,
    keyRecords: activeKeyRecords,
    recentActivity,
    settings,
    refreshDocuments,
    refreshProducts,
    refreshSummary,
    metrics: {
      totalProducts: summaryState ? summaryState.total_products : activeProducts.length,
      activeProducts: activeProductsCount,
      inactiveProducts: inactiveProductsCount,
      uploadedDocuments: summaryState ? summaryState.total_documents : activeDocuments.length,
      markdownFiles: summaryState ? summaryState.completed_documents : markdownFiles,
      qdrantStatus: 'Healthy',
      postgresqlStatus: 'Healthy',
      llmStatus: 'Healthy'
    }
  };
}
