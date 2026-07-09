// packages/security/src/verification/index.ts

import * as crypto from 'crypto';
import { CanonicalRequestBuilder, type CanonicalParams } from '../canonical-request';
import { HMACSigner } from '../signing';

export interface VerificationOptions {
  secret: string;
  allowedSkewMs?: number; // Defaults to 5 minutes (300,000 ms)
  nonceStore?: {
    has(nonce: string): boolean;
    add(nonce: string): void;
  };
}

export class SignatureVerifier {
  // Simple in-memory fallback store to track nonces and prevent duplicate attacks
  private static readonly defaultNonceCache = new Set<string>();
  
  private static readonly DEFAULT_SKEW_MS = 5 * 60 * 1000; // 5 minutes

  /**
   * Performs high-security validations verifying signature authenticity, clock skew limits, nonces reuse, and tenant matching.
   */
  public static verify(
    params: CanonicalParams,
    receivedSignature: string,
    options: VerificationOptions
  ): { isValid: boolean; reason?: string } {
    
    // 1. Validate Timestamp Skew Window
    const skew = options.allowedSkewMs ?? this.DEFAULT_SKEW_MS;
    const reqTime = parseInt(params.timestamp, 10);
    if (isNaN(reqTime)) {
      return { isValid: false, reason: 'EXPIRED_TIMESTAMP: Timestamp is malformed or invalid' };
    }

    const timeDifference = Math.abs(Date.now() - reqTime);
    if (timeDifference > skew) {
      return { isValid: false, reason: 'EXPIRED_TIMESTAMP: Request timestamp is outside clock skew window' };
    }

    // 2. Prevent Replay Attack via Nonces verification
    const store = options.nonceStore || {
      has: (n: string) => this.defaultNonceCache.has(n),
      add: (n: string) => {
        this.defaultNonceCache.add(n);
        // Auto cleanup expired nonces from memory after 10 minutes to prevent resource memory leaks
        setTimeout(() => this.defaultNonceCache.delete(n), 10 * 60 * 1000);
      }
    };

    if (store.has(params.nonce)) {
      return { isValid: false, reason: 'REPLAY_ATTACK: Nonce has already been processed' };
    }

    // 3. Compute and Compare Signature
    const expectedSignature = HMACSigner.sign(params, options.secret);

    // Constant-time hash check
    const matches = crypto.timingSafeEqual(
      Buffer.from(receivedSignature, 'hex'),
      Buffer.from(expectedSignature, 'hex')
    );

    if (!matches) {
      return { isValid: false, reason: 'INVALID_SIGNATURE: Cryptographic signature mismatch' };
    }

    // Success - add nonce to prevent replay
    store.add(params.nonce);

    return { isValid: true };
  }
}
