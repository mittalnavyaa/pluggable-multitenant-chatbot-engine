// packages/chatbot-backend-sdk/src/middleware/index.ts

import { type MiddlewareContract, type ExpressMiddleware } from '../types';
import { NotImplementedError } from '../errors';

export class SDKMiddleware implements MiddlewareContract {
  /**
   * Request middleware stub for future request body validation/parsing.
   */
  public requestMiddleware: ExpressMiddleware = (req, res, next) => {
    // Current stub simply passes request downstream
    next();
  };

  /**
   * Response middleware stub for sanitizing output payloads.
   */
  public responseMiddleware: ExpressMiddleware = (req, res, next) => {
    // Current stub simply passes request downstream
    next();
  };

  /**
   * Authentication middleware stub for validating/injecting future request JWTs or API headers.
   */
  public authenticationMiddleware: ExpressMiddleware = (req, res, next) => {
    // Current stub triggers NotImplementedError placeholder
    next(new NotImplementedError("authenticationMiddleware"));
  };

  /**
   * Proxy middleware stub for forwarding chat request prompts to the centralized RAG backend.
   */
  public proxyMiddleware: ExpressMiddleware = (req, res, next) => {
    // Current stub triggers NotImplementedError placeholder
    next(new NotImplementedError("proxyMiddleware"));
  };
}
