// packages/security/src/signing/index.ts

import * as crypto from 'crypto';
import { CanonicalRequestBuilder, type CanonicalParams } from '../canonical-request';

export class HMACSigner {
  /**
   * Computes HMAC-SHA256 signature digest from canonicalized request contents.
   */
  public static sign(params: CanonicalParams, secret: string): string {
    const canonicalString = CanonicalRequestBuilder.build(params);
    return crypto
      .createHmac('sha256', secret)
      .update(canonicalString)
      .digest('hex');
  }
}
