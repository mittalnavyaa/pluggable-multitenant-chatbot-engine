// packages/security/src/tests/security.test.ts

import { CanonicalRequestBuilder } from '../canonical-request';
import { HMACSigner } from '../signing';
import { SignatureVerifier } from '../verification';

describe('Cryptographic Verification Strategy Suite', () => {
  const secret = 'signing_secret_key_90210';
  const validParams = {
    method: 'POST',
    path: '/api/v1/chat/stream',
    queryParams: { b: '2', a: '1' },
    productId: 'tenant-omega',
    timestamp: Date.now().toString(),
    nonce: 'unique-nonce-1',
    body: { prompt: 'Who is Alan Turing?' }
  };

  describe('CanonicalRequestBuilder Serialization', () => {
    test('should build deterministic string sorting query parameters alphabetically', () => {
      const canonical = CanonicalRequestBuilder.build(validParams);
      const lines = canonical.split('\n');
      expect(lines[0]).toBe('POST');
      expect(lines[1]).toBe('/api/v1/chat/stream');
      expect(lines[2]).toBe('a=1&b=2'); // alphabetized sort query params
      expect(lines[3]).toBe('tenant-omega');
      expect(lines[6]).toBe(JSON.stringify({ prompt: 'Who is Alan Turing?' }));
    });

    test('should remove trailing slash in path names', () => {
      const params = { ...validParams, path: '/api/v1/chat/' };
      const canonical = CanonicalRequestBuilder.build(params);
      expect(canonical.split('\n')[1]).toBe('/api/v1/chat');
    });
  });

  describe('SignatureVerifier handshakes', () => {
    test('should approve valid signatures', () => {
      const signature = HMACSigner.sign(validParams, secret);
      const verification = SignatureVerifier.verify(validParams, signature, { secret });
      expect(verification.isValid).toBe(true);
    });

    test('should reject incorrect signatures', () => {
      const verification = SignatureVerifier.verify(validParams, 'wrong_signature_hash', { secret });
      expect(verification.isValid).toBe(false);
      expect(verification.reason).toContain('INVALID_SIGNATURE');
    });

    test('should reject expired request timestamps outside clock skew boundaries', () => {
      const oldTime = (Date.now() - 10 * 60 * 1000).toString(); // 10 mins ago
      const expiredParams = { ...validParams, timestamp: oldTime, nonce: 'nonce-old' };
      const signature = HMACSigner.sign(expiredParams, secret);
      
      const verification = SignatureVerifier.verify(expiredParams, signature, { secret });
      expect(verification.isValid).toBe(false);
      expect(verification.reason).toContain('EXPIRED_TIMESTAMP');
    });

    test('should reject duplicate nonces to prevent replay attacks', () => {
      const nonce = 'replay-check-nonce';
      const params1 = { ...validParams, nonce, timestamp: Date.now().toString() };
      const signature1 = HMACSigner.sign(params1, secret);
      
      const res1 = SignatureVerifier.verify(params1, signature1, { secret });
      expect(res1.isValid).toBe(true);

      // Re-sign request with same nonce (even if timestamp changes)
      const params2 = { ...validParams, nonce, timestamp: Date.now().toString() };
      const signature2 = HMACSigner.sign(params2, secret);

      const res2 = SignatureVerifier.verify(params2, signature2, { secret });
      expect(res2.isValid).toBe(false);
      expect(res2.reason).toContain('REPLAY_ATTACK');
    });
  });
});
