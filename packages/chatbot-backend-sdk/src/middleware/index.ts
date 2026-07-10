// packages/chatbot-backend-sdk/src/middleware/index.ts

import { type MiddlewareContract, type ExpressMiddleware } from '../types';
import { InvalidSignatureError, UnauthorizedProxyRequest, ProxyTimeoutError, BackendUnavailableError } from '../errors';
import { HMACSignatureProvider } from '../utils/crypto';
import { type ChatbotSDK } from '../sdk';

function sanitizeLog(value: unknown): string {
  return String(value).replace(/[\r\n\x00-\x1f\x7f]/g, '');
}

export class SDKMiddleware implements MiddlewareContract {
  constructor(private readonly sdk: ChatbotSDK) {}

  /**
   * Request interceptor middleware validating user payload parameters.
   */
  public requestMiddleware: ExpressMiddleware = (req, res, next) => {
    const body = req.body || {};
    if (!body.bot_id || typeof body.bot_id !== 'string') {
      res.status(400).json({ success: false, error: 'Bad Request: "bot_id" parameter is required.' });
      return;
    }
    if (!body.prompt || typeof body.prompt !== 'string') {
      res.status(400).json({ success: false, error: 'Bad Request: "prompt" parameter is required.' });
      return;
    }
    next();
  };

  /**
   * Response sanitizer middleware (stubs).
   */
  public responseMiddleware: ExpressMiddleware = (req, res, next) => {
    next();
  };

  /**
   * Inbound signature authentication verification middleware.
   */
  public authenticationMiddleware: ExpressMiddleware = (req, res, next) => {
    const signature = req.headers['x-envoy-signature'] || req.headers['X-Envoy-Signature'];
    if (!signature) {
      next(new UnauthorizedProxyRequest("Missing required header X-Envoy-Signature"));
      return;
    }
    next();
  };

  /**
   * Core secure network proxy routing middleware forwarding request prompts to core FastAPI backend,
   * injecting server credentials, cryptographic signatures, and handling Server-Sent Events streams piping.
   */
  public proxyMiddleware: ExpressMiddleware = async (req, res) => {
    const startTime = Date.now();
    const body = req.body || {};
    const botId = body.bot_id;
    const prompt = body.prompt;
    const isStream = body.stream === true;

    const options = this.sdk.getOptions();
    const client = this.sdk.getClient();

    try {
      // 1. Instantiates the cryptographic signature provider
      const signer = new HMACSignatureProvider(
        options.apiKey,
        options.productId,
        options.signingSecret
      );

      // 2. Sign JSON body payload
      const signPayload = JSON.stringify({ bot_id: botId, prompt, stream: isStream });
      const signatureHeaders = signer.sign(signPayload);

      // 3. Dispatch call to client proxy
      console.log('[envoy-proxy] Forwarding request', { bot_id: sanitizeLog(botId), stream: isStream });
      
      const response = await client.queryChatbot(botId, prompt, isStream, signatureHeaders as any);

      // 4. Handle response transfer formats
      if (isStream) {
        // SSE pipe response logic
        res.setHeader('Content-Type', 'text/event-stream');
        res.setHeader('Cache-Control', 'no-cache');
        res.setHeader('Connection', 'keep-alive');
        
        response.on('data', (chunk: any) => {
          res.write(chunk);
        });

        response.on('end', () => {
          const duration = Date.now() - startTime;
          console.log(`[envoy-proxy] SSE Stream ended successfully. Duration: ${duration}ms`);
          res.end();
        });

        response.on('error', (err: any) => {
          console.error(`[envoy-proxy] SSE Stream connection error:`, err);
          res.write(`data: ${JSON.stringify({ error: 'Connection interrupted' })}\n\n`);
          res.end();
        });
      } else {
        // Standard JSON response
        const duration = Date.now() - startTime;
        console.log(`[envoy-proxy] JSON request completed. Duration: ${duration}ms`);
        res.status(200).json(response);
      }

    } catch (err: any) {
      const duration = Date.now() - startTime;
      console.error(`[envoy-proxy] Ingestion proxy routing failed after ${duration}ms: ${sanitizeLog(err.message)}`);

      // Map proxy exceptions to clean, safe browser responses
      let status = 500;
      let errorMsg = 'An internal gateway proxy error occurred.';

      if (err instanceof InvalidSignatureError) {
        status = 403;
        errorMsg = 'Security validation failure.';
      } else if (err instanceof ProxyTimeoutError) {
        status = 504;
        errorMsg = 'Gateway timeout connecting to central agent services.';
      } else if (err instanceof BackendUnavailableError) {
        status = 503;
        errorMsg = 'Centralized AI agent engine is currently unreachable.';
      } else if (err instanceof UnauthorizedProxyRequest) {
        status = 401;
        errorMsg = 'Access denied.';
      }

      res.status(status).json({ success: false, error: errorMsg });
    }
  };
}
