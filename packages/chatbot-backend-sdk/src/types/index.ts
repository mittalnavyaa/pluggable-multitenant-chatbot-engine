// packages/chatbot-backend-sdk/src/types/index.ts

export interface SDKOptions {
  apiBase: string;
  apiKey: string;
  productId: string;
  signingSecret: string;
  timeout?: number;
  retries?: number;
  environment?: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
}

export interface SDKResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface SignatureHeaders {
  'X-Envoy-Signature': string;
  'X-Envoy-Timestamp': string;
  'X-Envoy-Nonce': string;
  'X-Envoy-API-Key': string;
  'X-Envoy-Product-ID': string;
}

export interface SignatureProvider {
  sign(payload: string): SignatureHeaders;
  verify(payload: string, headers: Record<string, string>): boolean;
}

export interface ClientContract {
  queryChatbot(botId: string, prompt: string, stream?: boolean): Promise<any>;
  getBranding(productId: string): Promise<SDKResponse<any>>;
  syncDocuments(botId: string): Promise<SDKResponse<{ job_id: string }>>;
}

export type ExpressMiddleware = (req: any, res: any, next: (err?: any) => void) => void;

export interface MiddlewareContract {
  requestMiddleware: ExpressMiddleware;
  responseMiddleware: ExpressMiddleware;
  authenticationMiddleware: ExpressMiddleware;
  proxyMiddleware: ExpressMiddleware;
}
