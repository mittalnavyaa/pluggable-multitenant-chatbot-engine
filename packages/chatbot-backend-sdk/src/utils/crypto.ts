// packages/chatbot-backend-sdk/src/utils/crypto.ts

import * as crypto from 'crypto';
import { type SignatureHeaders, type SignatureProvider } from '../types';

export class HMACSignatureProvider implements SignatureProvider {
  constructor(
    private readonly apiKey: string,
    private readonly productId: string,
    private readonly signingSecret: string
  ) {}

  /**
   * Generates signature headers containing signature, nonce, timestamp, product tenant ID, and API key.
   */
  public sign(payload: string): SignatureHeaders {
    const timestamp = Date.now().toString();
    const nonce = crypto.randomBytes(16).toString('hex');
    
    const signature = this.computeSignature(timestamp, nonce, payload);

    return {
      'X-Envoy-Signature': signature,
      'X-Envoy-Timestamp': timestamp,
      'X-Envoy-Nonce': nonce,
      'X-Envoy-API-Key': this.apiKey,
      'X-Envoy-Product-ID': this.productId
    };
  }

  /**
   * Verifies the authenticity of incoming payload by comparing computed and received signatures.
   */
  public verify(payload: string, headers: Record<string, string>): boolean {
    const signature = headers['x-envoy-signature'] || headers['X-Envoy-Signature'];
    const timestamp = headers['x-envoy-timestamp'] || headers['X-Envoy-Timestamp'];
    const nonce = headers['x-envoy-nonce'] || headers['X-Envoy-Nonce'];

    if (!signature || !timestamp || !nonce) {
      return false;
    }

    // Prevent replay attacks: reject requests older than 5 minutes
    const reqTime = parseInt(timestamp, 10);
    if (isNaN(reqTime) || Math.abs(Date.now() - reqTime) > 5 * 60 * 1000) {
      return false;
    }

    const expectedSignature = this.computeSignature(timestamp, nonce, payload);

    // Constant-time comparison to prevent timing attacks
    return crypto.timingSafeEqual(
      Buffer.from(signature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );
  }

  private computeSignature(timestamp: string, nonce: string, payload: string): string {
    const message = `${timestamp}.${nonce}.${payload}`;
    return crypto
      .createHmac('sha256', this.signingSecret)
      .update(message)
      .digest('hex');
  }
}
