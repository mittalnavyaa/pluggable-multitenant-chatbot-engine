// packages/chatbot-backend-sdk/src/client/index.ts

import { type ClientContract, type SDKResponse, type ChatMessage } from '../types';
import { NotImplementedError } from '../errors';

export class SDKClient implements ClientContract {
  constructor(
    private readonly apiBase: string,
    private readonly apiKey: string,
    private readonly productId: string,
    private readonly timeout?: number
  ) {}

  /**
   * Stub endpoint for future chatbot context queries.
   */
  public async queryChatbot(botId: string, prompt: string): Promise<SDKResponse<ChatMessage>> {
    throw new NotImplementedError("queryChatbot");
  }

  /**
   * Stub endpoint for future product branding retrieval.
   */
  public async getBranding(productId: string): Promise<SDKResponse<any>> {
    throw new NotImplementedError("getBranding");
  }

  /**
   * Stub endpoint for manually triggering document synchronization tasks.
   */
  public async syncDocuments(botId: string): Promise<SDKResponse<{ job_id: string }>> {
    throw new NotImplementedError("syncDocuments");
  }
}
