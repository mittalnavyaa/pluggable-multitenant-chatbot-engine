// packages/security/src/canonical-request/index.ts

export interface CanonicalParams {
  method: string;
  path: string;
  queryParams?: Record<string, string>;
  productId: string;
  timestamp: string;
  nonce: string;
  body?: string | Record<string, any>;
}

export class CanonicalRequestBuilder {
  /**
   * Serializes request parameters into a deterministic canonical string pattern:
   * METHOD\nPATH\nSORTED_QUERY_PARAMS\nPRODUCT_ID\nTIMESTAMP\nNONCE\nBODY_PAYLOAD
   */
  public static build(params: CanonicalParams): string {
    const method = params.method.toUpperCase().trim();
    
    // Normalize path: lowercase, remove trailing slashes unless it's just '/'
    let path = params.path.toLowerCase().trim();
    if (path.length > 1 && path.endsWith('/')) {
      path = path.slice(0, -1);
    }

    // Normalize and sort query params alphabetically
    let sortedQueryStr = '';
    if (params.queryParams && Object.keys(params.queryParams).length > 0) {
      const sortedKeys = Object.keys(params.queryParams).sort();
      sortedQueryStr = sortedKeys
        .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(params.queryParams![key])}`)
        .join('&');
    }

    // Normalize body payload: stringify JSON if it's an object, or use raw string
    let normalizedBody = '';
    if (params.body !== undefined && params.body !== null) {
      if (typeof params.body === 'object') {
        normalizedBody = JSON.stringify(params.body);
      } else {
        normalizedBody = String(params.body);
      }
    }

    return [
      method,
      path,
      sortedQueryStr,
      params.productId.trim(),
      params.timestamp.trim(),
      params.nonce.trim(),
      normalizedBody
    ].join('\n');
  }
}
