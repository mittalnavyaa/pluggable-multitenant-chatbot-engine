// packages/chatbot-backend-sdk/src/index.ts

import { ChatbotSDK } from './sdk';
import { type SDKOptions } from './types';

/**
 * Factory creator function to instantiate the Chatbot SDK.
 */
export function createChatbotSDK(options: SDKOptions): ChatbotSDK {
  return new ChatbotSDK(options);
}

// Export public classes, error interfaces, and typing contracts
export { ChatbotSDK } from './sdk';
export { SDKClient } from './client';
export { SDKMiddleware } from './middleware';
export { HMACSignatureProvider } from './utils/crypto';

export * from './types';
export * from './errors';
