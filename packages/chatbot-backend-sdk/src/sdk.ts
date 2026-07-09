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
      options.timeout || 5000,
      options.retries || 3
    );

    this.middleware = new SDKMiddleware(this);
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
    if (typeof options.signingSecret !== "string" || !options.signingSecret.trim()) {
      throw new SDKConfigurationError("signingSecret", "must be a non-empty cryptographic signing secret string");
    }
    if (options.timeout !== undefined && (typeof options.timeout !== "number" || options.timeout <= 0)) {
      throw new SDKConfigurationError("timeout", "must be a positive number of milliseconds");
    }
    if (options.retries !== undefined && (typeof options.retries !== "number" || options.retries < 0)) {
      throw new SDKConfigurationError("retries", "must be a non-negative number of retry counts");
    }
  }

  /**
   * Return client class for future API calls
   */
  public getClient(): SDKClient {
    return this.client;
  }

  /**
   * Return middleware handlers for host frameworks integrations
   */
  public getMiddleware(): SDKMiddleware {
    return this.middleware;
  }

  /**
   * Get active SDK configuration options
   */
  public getOptions(): SDKOptions {
    return this.options;
  }
}
