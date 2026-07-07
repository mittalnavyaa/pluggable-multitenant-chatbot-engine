import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
import { isAuthenticated } from './auth/authService';
import { ProtectedRoute } from './components/ProtectedRoute';
import { useEnterpriseDashboardData } from '../hooks/useEnterpriseDashboardData.js';
import { DashboardLayout } from '../layouts/DashboardLayout.jsx';
import { ApiKeys } from '../pages/ApiKeys.jsx';
import { Branding } from '../pages/Branding.jsx';
import { Dashboard } from '../pages/Dashboard.jsx';
import { Documents } from '../pages/Documents.jsx';
import { ProductDetails } from '../pages/ProductDetails.jsx';
import { Products } from '../pages/Products.jsx';
import { Settings } from '../pages/Settings.jsx';
import { Uploads } from '../pages/Uploads';
import { Login } from './pages/Login';
import '../styles/dashboard.css';

const routeTitles: Record<string, string> = {
  '/': 'Dashboard',
  '/products': 'Products',
  '/branding': 'Branding',
  '/api-keys': 'API Keys',
  '/documents': 'Documents',
  '/uploads': 'Upload Manager',
  '/settings': 'Settings'
};

function ProductsRoute() {
  const data = useEnterpriseDashboardData();
  const navigate = useNavigate();

  return (
    <Products
      products={data.products}
      onViewDetails={(productId: string) => navigate(`/products/${productId}`)}
    />
  );
}

function ProductDetailsRoute() {
  const data = useEnterpriseDashboardData();
  const { id } = useParams();
  const product = data.products.find((item) => item.id === id) || data.selectedProduct;

  return <ProductDetails product={product} />;
}

function BrandingRoute() {
  const data = useEnterpriseDashboardData();
  return <Branding product={data.selectedProduct} />;
}

function DashboardApp() {
  const data = useEnterpriseDashboardData();
  const location = useLocation();
  const activePage = routeTitles[location.pathname] || (location.pathname.startsWith('/products/') ? 'Product Details' : 'Dashboard');

  return (
    <DashboardLayout activePage={activePage} onNavigate={undefined}>
      <Routes>
        <Route path="/" element={<Dashboard data={data} />} />
        <Route path="/products" element={<ProductsRoute />} />
        <Route path="/products/:id" element={<ProductDetailsRoute />} />
        <Route path="/branding" element={<BrandingRoute />} />
        <Route path="/api-keys" element={<ApiKeys keyRecords={data.keyRecords} />} />
        <Route path="/documents" element={<Documents documents={data.documents} />} />
        <Route path="/uploads" element={<Uploads />} />
        <Route path="/settings" element={<Settings settings={data.settings} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DashboardLayout>
  );
}

export function App() {
  return (
    <Routes>
      {/* Public route — login page */}
      <Route path="/login" element={
        isAuthenticated()
          ? <Navigate to="/" replace />
          : <Login />
      } />

      {/* All dashboard routes are protected */}
      <Route path="/*" element={
        <ProtectedRoute>
          <DashboardApp />
        </ProtectedRoute>
      } />
    </Routes>
  );
}
