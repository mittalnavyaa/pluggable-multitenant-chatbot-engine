import { ProductInfo } from '../services/productService';

export type Product = ProductInfo;
export type SelectedProduct = ProductInfo | null;

export interface DashboardDocument {
  id: string;
  product: string;
  fileName: string;
  markdownFile: string;
  chunkCount: string;
  embeddingStatus: string;
  uploadDate: string;
  owner: string;
  classification: string;
}

export interface KeyRecord {
  id: string;
  product: string;
  maskedKey: string;
  status: string;
  created: string;
  lastRotated: string;
}

export interface DashboardMetrics {
  totalProducts: number;
  activeProducts: number;
  inactiveProducts: number;
  uploadedDocuments: number;
  markdownFiles: number;
  qdrantStatus: string;
  postgresqlStatus: string;
  llmStatus: string;
}

export interface DashboardData {
  products: Product[];
  selectedProduct: SelectedProduct;
  documents: DashboardDocument[];
  keyRecords: KeyRecord[];
  recentActivity: any[];
  settings: any[];
  refreshDocuments: () => Promise<void>;
  refreshProducts: () => Promise<void>;
  refreshSummary: () => Promise<void>;
  metrics: DashboardMetrics;
}
