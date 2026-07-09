// packages/chatbot-backend-sdk/src/tests/proxy.test.ts

import { createChatbotSDK } from '../index';
import { HMACSignatureProvider } from '../utils/crypto';
import { SDKConfigurationError } from '../errors';

describe('Chatbot SDK Security & Proxy Core', () => {
  const apiKey = 'test_api_key_123';
  const productId = 'test_tenant_id';
  const signingSecret = 'super_secret_signing_key';

  describe('HMACSignatureProvider Hashing', () => {
    let signer: HMACSignatureProvider;
    const testPayload = JSON.stringify({ bot_id: 'bot_abc', prompt: 'Hello AI' });

    beforeEach(() => {
      signer = new HMACSignatureProvider(apiKey, productId, signingSecret);
    });

    test('should sign payload and produce valid headers structure', () => {
      const headers = signer.sign(testPayload);
      expect(headers['X-Envoy-Signature']).toBeDefined();
      expect(headers['X-Envoy-Timestamp']).toBeDefined();
      expect(headers['X-Envoy-Nonce']).toBeDefined();
      expect(headers['X-Envoy-API-Key']).toBe(apiKey);
      expect(headers['X-Envoy-Product-ID']).toBe(productId);
    });

    test('should verify valid signatures matching the same payload and secret', () => {
      const headers = signer.sign(testPayload);
      
      // Standardize header keys mapping to lowercase as typical in express/http
      const reqHeaders = {
        'x-envoy-signature': headers['X-Envoy-Signature'],
        'x-envoy-timestamp': headers['X-Envoy-Timestamp'],
        'x-envoy-nonce': headers['X-Envoy-Nonce']
      };

      const isValid = signer.verify(testPayload, reqHeaders);
      expect(isValid).toBe(true);
    });

    test('should reject signatures verified with incorrect secret keys', () => {
      const headers = signer.sign(testPayload);
      const invalidSigner = new HMACSignatureProvider(apiKey, productId, 'wrong_secret');
      
      const reqHeaders = {
        'x-envoy-signature': headers['X-Envoy-Signature'],
        'x-envoy-timestamp': headers['X-Envoy-Timestamp'],
        'x-envoy-nonce': headers['X-Envoy-Nonce']
      };

      const isValid = invalidSigner.verify(testPayload, reqHeaders);
      expect(isValid).toBe(false);
    });

    test('should reject signatures if payload is altered', () => {
      const headers = signer.sign(testPayload);
      
      const reqHeaders = {
        'x-envoy-signature': headers['X-Envoy-Signature'],
        'x-envoy-timestamp': headers['X-Envoy-Timestamp'],
        'x-envoy-nonce': headers['X-Envoy-Nonce']
      };

      const isValid = signer.verify(testPayload + ' modified body', reqHeaders);
      expect(isValid).toBe(false);
    });

    test('should reject signatures with expired timestamp windows', () => {
      const oldTimestamp = (Date.now() - 10 * 60 * 1000).toString(); // 10 minutes ago
      const nonce = 'random_nonce';
      
      // Compute signature manually
      const message = `${oldTimestamp}.${nonce}.${testPayload}`;
      const crypto = require('crypto');
      const signature = crypto
        .createHmac('sha256', signingSecret)
        .update(message)
        .digest('hex');

      const reqHeaders = {
        'x-envoy-signature': signature,
        'x-envoy-timestamp': oldTimestamp,
        'x-envoy-nonce': nonce
      };

      const isValid = signer.verify(testPayload, reqHeaders);
      expect(isValid).toBe(false);
    });
  });

  describe('ChatbotSDK Setup Validations', () => {
    test('should throw config error if vital credentials are missing', () => {
      expect(() => {
        createChatbotSDK({
          apiBase: '',
          apiKey: 'key',
          productId: 'prod',
          signingSecret: 'secret'
        });
      }).toThrow(SDKConfigurationError);

      expect(() => {
        createChatbotSDK({
          apiBase: 'http://localhost:8000',
          apiKey: '',
          productId: 'prod',
          signingSecret: 'secret'
        });
      }).toThrow(SDKConfigurationError);

      expect(() => {
        createChatbotSDK({
          apiBase: 'http://localhost:8000',
          apiKey: 'key',
          productId: 'prod',
          signingSecret: ''
        });
      }).toThrow(SDKConfigurationError);
    });

    test('should initialize successfully with valid parameters', () => {
      const sdk = createChatbotSDK({
        apiBase: 'http://localhost:8000',
        apiKey: 'key',
        productId: 'prod',
        signingSecret: 'secret',
        timeout: 2000,
        retries: 2
      });
      expect(sdk).toBeDefined();
      expect(sdk.getClient()).toBeDefined();
      expect(sdk.getMiddleware()).toBeDefined();
    });
  });

  describe('SDKMiddleware Requests Interception', () => {
    let sdk: any;
    let middleware: any;

    beforeEach(() => {
      sdk = createChatbotSDK({
        apiBase: 'http://localhost:8000',
        apiKey: 'key',
        productId: 'prod',
        signingSecret: 'secret'
      });
      middleware = sdk.getMiddleware();
    });

    test('requestMiddleware should pass valid body payloads', () => {
      const req = {
        body: {
          bot_id: 'bot_123',
          prompt: 'Hello AI'
        }
      };
      
      let nextCalled = false;
      const next = () => {
        nextCalled = true;
      };

      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      };

      middleware.requestMiddleware(req, res, next);
      expect(nextCalled).toBe(true);
    });

    test('requestMiddleware should fail and respond with 400 on missing arguments', () => {
      const req = {
        body: {
          bot_id: '',
          prompt: 'Hello AI'
        }
      };
      
      let nextCalled = false;
      const next = () => {
        nextCalled = true;
      };

      const jsonMock = jest.fn();
      const res = {
        status: jest.fn().mockReturnValue({ json: jsonMock }),
        json: jsonMock
      };

      middleware.requestMiddleware(req, res, next);
      expect(nextCalled).toBe(false);
      expect(res.status).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({ error: expect.stringContaining('bot_id') })
      );
    });
  });
});
