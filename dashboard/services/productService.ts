// dashboard/services/productService.ts

export interface ProductBranding {
  backgroundColor: string;
  surfaceColor: string;
  textColor: string;
  mutedTextColor: string;
  successColor: string;
  warningColor: string;
  errorColor: string;
  fontFamily: string;
  headingWeight: number;
  bodyWeight: number;
  borderRadius: string;
  spacing: string;
  shadow: string;
  maxWidth: string;
  buttonStyle: string;
  buttonRadius: string;
  contrastMode: string;
  darkModeSupported: boolean;
  version: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  widgetTitle: string;
  launcherLabel: string;
  welcomeMessage: string;
  placeholderText: string;
  logoUrl?: string;
  faviconUrl?: string;
  updatedAt?: string;
}

export interface ProductInfo {
  id: string; // mapped from varchar product_id
  uuid: string; // DB primary key UUID
  name: string;
  status: string;
  createdDate: string;
  serviceTokenStatus: string;
  serviceTokenMasked: string;
  logoInitials: string;
  branding: ProductBranding;
}

export async function fetchProducts(): Promise<ProductInfo[]> {
  const response = await fetch('/api/v1/products');
  if (!response.ok) {
    throw new Error(`Failed to fetch products: HTTP ${response.status}`);
  }
  const data = await response.json();
  return data;
}

export async function fetchProductById(productId: string): Promise<ProductInfo> {
  const response = await fetch(`/api/v1/products/${productId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch product ${productId}: HTTP ${response.status}`);
  }
  const p = await response.json();
  return p;
}

export async function createProduct(productId: string, name: string): Promise<ProductInfo> {
  const response = await fetch('/api/v1/products', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      product_id: productId,
      name
    })
  });
  if (!response.ok) {
    const errorText = await response.text();
    let detail = `HTTP ${response.status}`;
    try {
      const errorJson = JSON.parse(errorText);
      detail = errorJson.detail || errorJson.error || errorText || detail;
    } catch {
      if (errorText) {
        detail = errorText;
      }
    }
    throw new Error(`Failed to create product: ${detail}`);
  }
  const p = await response.json();
  return p;
}
