// packages/chatbot-backend-sdk/src/errors/index.ts

export class SDKError extends Error {
  constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
    if (typeof Error.captureStackTrace === 'function') {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

export class SDKConfigurationError extends SDKError {
  constructor(paramName: string, reason = "is missing or invalid") {
    super(`SDK Configuration Error: Parameter "${paramName}" ${reason}.`);
  }
}

export class SDKValidationError extends SDKError {
  constructor(message: string) {
    super(`SDK Validation Error: ${message}`);
  }
}

export class SDKNetworkError extends SDKError {
  constructor(endpoint: string, status: number, details?: string) {
    super(`SDK Network Error: Fetch request to ${endpoint} failed with HTTP Status ${status}.${details ? ` ${details}` : ""}`);
  }
}

export class SDKAuthenticationError extends SDKError {
  constructor(reason = "Invalid credentials or token signing validation failed") {
    super(`SDK Authentication Error: ${reason}.`);
  }
}

export class NotImplementedError extends SDKError {
  constructor(methodName: string) {
    super(`SDK Feature Error: The method "${methodName}" is not implemented in this version.`);
  }
}

export class InvalidSignatureError extends SDKError {
  constructor(reason = "HMAC signature mismatch") {
    super(`SDK Security Error: Invalid request signature - ${reason}.`);
  }
}

export class BackendUnavailableError extends SDKError {
  constructor(endpoint: string, details?: string) {
    super(`SDK Network Error: Central backend at ${endpoint} is unavailable.${details ? ` ${details}` : ""}`);
  }
}

export class ProxyTimeoutError extends SDKError {
  constructor(endpoint: string, timeoutMs: number) {
    super(`SDK Timeout Error: Request to ${endpoint} timed out after ${timeoutMs}ms.`);
  }
}

export class UnauthorizedProxyRequest extends SDKError {
  constructor(reason = "Missing or invalid authorization context") {
    super(`SDK Access Error: Unauthorized proxy routing request - ${reason}.`);
  }
}
