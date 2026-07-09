// packages/chatbot-backend-sdk/src/types/index.ts

export interface SDKOptions {
  apiBase: string;
  apiKey: string;
  productId: string;
  timeout?: number;
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

export interface ClientContract {
  queryChatbot(botId: string, prompt: string): Promise<SDKResponse<ChatMessage>>;
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
