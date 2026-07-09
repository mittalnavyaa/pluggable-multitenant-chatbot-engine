// packages/chatbot-backend-sdk/src/sdk.ts

import { type SDKOptions } from './types';
import { SDKConfigurationError } from './errors';
import { SDKClient } from './client';
import { SDKMiddleware } from './middleware';

export class ChatbotSDK {
  private readonly client: SDKClient;
  private readonly middleware: SDKMiddleware;

  constructor(private readonly options: SDKOptions) {
    this.validateOptions(options);

    this.client = new SDKClient(
      options.apiBase,
      options.apiKey,
      options.productId,
      options.timeout
    );

    this.middleware = new SDKMiddleware();
  }

  private validateOptions(options: SDKOptions) {
    if (!options) {
      throw new SDKConfigurationError("options", "must be provided as an options object");
    }
    if (typeof options.apiBase !== "string" || !options.apiBase.trim()) {
      throw new SDKConfigurationError("apiBase", "must be a non-empty string URL");
    }
    if (typeof options.apiKey !== "string" || !options.apiKey.trim()) {
      throw new SDKConfigurationError("apiKey", "must be a non-empty API key string");
    }
    if (typeof options.productId !== "string" || !options.productId.trim()) {
      throw new SDKConfigurationError("productId", "must be a non-empty product tenant ID");
    }
    if (options.timeout !== undefined && (typeof options.timeout !== "number" || options.timeout <= 0)) {
      throw new SDKConfigurationError("timeout", "must be a positive number of milliseconds");
    }
  }

  /**
   * Return client class for future API calls
   */
  public getClient(): SDKClient {
    return this.client;
  }

  /**
   * Return middleware stubs for host frameworks integrations
   */
  public getMiddleware(): SDKMiddleware {
    return this.middleware;
  }
}
