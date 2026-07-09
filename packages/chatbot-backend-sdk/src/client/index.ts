// packages/chatbot-backend-sdk/src/client/index.ts

import * as http from 'http';
import * as https from 'https';
import { URL } from 'url';
import { type ClientContract, type SDKResponse } from '../types';
import { BackendUnavailableError, ProxyTimeoutError, SDKNetworkError } from '../errors';

export class SDKClient implements ClientContract {
  constructor(
    private readonly apiBase: string,
    private readonly apiKey: string,
    private readonly productId: string,
    private readonly timeout = 5000,
    private readonly retries = 3
  ) {}

  /**
   * Forwards a chat query to the core FastAPI backend, supporting both JSON and streaming response options.
   */
  public async queryChatbot(botId: string, prompt: string, stream = false, extraHeaders?: Record<string, string>): Promise<any> {
    const payload = JSON.stringify({ bot_id: botId, prompt, stream });
    const targetUrl = `${this.apiBase}/api/v1/chat/stream`;
    
    return this.requestWithRetry('POST', targetUrl, payload, stream, extraHeaders);
  }

  /**
   * Retrieves product branding metadata from core backend.
   */
  public async getBranding(productId: string): Promise<SDKResponse<any>> {
    const targetUrl = `${this.apiBase}/api/v1/products/${productId}`;
    return this.requestWithRetry('GET', targetUrl);
  }

  /**
   * Manually triggers vectorization document synchronization pipelines.
   */
  public async syncDocuments(botId: string): Promise<SDKResponse<{ job_id: string }>> {
    const targetUrl = `${this.apiBase}/api/v1/documents/sync`;
    const payload = JSON.stringify({ bot_id: botId });
    return this.requestWithRetry('POST', targetUrl, payload);
  }

  /**
   * Execution wrapper handling request timeouts and transient failures retries.
   */
  private async requestWithRetry(
    method: 'GET' | 'POST',
    targetUrl: string,
    body?: string,
    streamResponse = false,
    extraHeaders?: Record<string, string>,
    attempt = 1
  ): Promise<any> {
    try {
      return await this.dispatchRequest(method, targetUrl, body, streamResponse, extraHeaders);
    } catch (err) {
      const isTransient = err instanceof BackendUnavailableError || 
                          (err instanceof SDKNetworkError && err.message.includes('Status 5')); // 5xx server errors
      
      if (isTransient && attempt < this.retries) {
        const delay = Math.pow(2, attempt) * 100; // Exponential backoff: 200ms, 400ms, 800ms
        console.warn(`[envoy-client] Transient error on attempt ${attempt}. Retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.requestWithRetry(method, targetUrl, body, streamResponse, extraHeaders, attempt + 1);
      }
      throw err;
    }
  }

  private dispatchRequest(
    method: 'GET' | 'POST',
    targetUrl: string,
    body?: string,
    streamResponse = false,
    extraHeaders?: Record<string, string>
  ): Promise<any> {
    return new Promise((resolve, reject) => {
      const url = new URL(targetUrl);
      const isHttps = url.protocol === 'https:';
      const requestLib = isHttps ? https : http;

      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Envoy-API-Key': this.apiKey,
        'X-Envoy-Product-ID': this.productId,
        ...extraHeaders
      };

      if (body) {
        headers['Content-Length'] = Buffer.byteLength(body).toString();
      }

      const options: http.RequestOptions = {
        method,
        hostname: url.hostname,
        port: url.port || (isHttps ? 443 : 80),
        path: url.pathname + url.search,
        headers,
        timeout: this.timeout
      };

      const req = requestLib.request(options, (res: http.IncomingMessage) => {
        const status = res.statusCode || 500;

        // In streaming mode, resolve the promise directly with response stream if status is success
        if (streamResponse && status >= 200 && status < 300) {
          resolve(res);
          return;
        }

        let responseBody = '';
        res.on('data', (chunk: any) => {
          responseBody += chunk;
        });

        res.on('end', () => {
          if (status < 200 || status >= 300) {
            reject(new SDKNetworkError(targetUrl, status, responseBody));
            return;
          }

          try {
            const json = JSON.parse(responseBody);
            resolve({ success: true, data: json });
          } catch {
            resolve({ success: true, data: responseBody as any });
          }
        });
      });

      req.on('error', (err: any) => {
        if (err.code === 'ECONNREFUSED' || err.code === 'ENOTFOUND') {
          reject(new BackendUnavailableError(targetUrl, err.message));
        } else {
          reject(new SDKNetworkError(targetUrl, 500, err.message));
        }
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new ProxyTimeoutError(targetUrl, this.timeout));
      });

      if (body) {
        req.write(body);
      }
      req.end();
    });
  }
}
