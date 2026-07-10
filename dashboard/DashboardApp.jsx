import { useState } from 'react';
import { useEnterpriseDashboardData } from './hooks/useEnterpriseDashboardData';
import { DashboardLayout } from './layouts/DashboardLayout.jsx';
import { AdminDashboard } from './pages/AdminDashboard.jsx';
import { ApiKeys } from './pages/ApiKeys.jsx';
import { Branding } from './pages/Branding.jsx';
import { Dashboard } from './pages/Dashboard.jsx';
import { Documents } from './pages/Documents.jsx';
import { ProductDetails } from './pages/ProductDetails.jsx';
import { Products } from './pages/Products.jsx';
import { Settings } from './pages/Settings.jsx';
import { Uploads } from './pages/Uploads';
import './styles/dashboard.css';

export function DashboardApp() {
  const data = useEnterpriseDashboardData();
  const [activePage, setActivePage] = useState('Dashboard');
  const [selectedProductId, setSelectedProductId] = useState(data.selectedProduct?.id || null);
  const selectedProduct = data.products.find((product) => product.id === selectedProductId) || data.selectedProduct;

  function viewDetails(productId) {
    setSelectedProductId(productId);
    setActivePage('Product Details');
  }

  const pages = {
    Dashboard: <Dashboard data={data} />,
    'Overview Dashboard': <AdminDashboard />,
    'Bot Control Factory': <AdminDashboard />,
    'Ingestion Status Queues': <Documents documents={data.documents} />,
    'Sales Conversions': <AdminDashboard />,
    Products: <Products products={data.products} onViewDetails={viewDetails} />,
    'Product Details': selectedProduct ? <ProductDetails product={selectedProduct} /> : <div style={{ padding: '24px', color: 'var(--color-text)' }}>No product selected.</div>,
    Branding: selectedProduct ? <Branding product={selectedProduct} /> : <div style={{ padding: '24px', color: 'var(--color-text)' }}>Please select a product.</div>,
    Uploads: <Uploads />,
    'API Keys': <ApiKeys keyRecords={data.keyRecords} />,
    Documents: <Documents documents={data.documents} />,
    Settings: <Settings settings={data.settings} />
  };

  return (
    <DashboardLayout activePage={activePage} onNavigate={setActivePage}>
      {pages[activePage]}
    </DashboardLayout>
  );
}
