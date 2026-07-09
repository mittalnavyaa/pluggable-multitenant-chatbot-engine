# @envoy/chatbot-backend-sdk

Node.js SDK for integrating multi-tenant chatbot engine services into host application backends.

---

> [!NOTE]
> **Networking & Authentication Status**: In this version, all client requests and middleware routing layers are scaffolded as architectural placeholders (stubs) to finalize the API surfaces before secure transport, signing, and encryption proxies are implemented. Calling the client APIs will throw a `NotImplementedError`.

---

## Installation

Install the package within your project workspace:

```bash
npm install @envoy/chatbot-backend-sdk
```

---

## Quick Start & Usage

```javascript
import { createChatbotSDK, SDKConfigurationError } from "@envoy/chatbot-backend-sdk";

try {
  const sdk = createChatbotSDK({
    apiBase: "http://localhost:8000",
    apiKey: "envoy_prod_key_xyz",
    productId: "tenant-tensor-alpha",
    timeout: 5000,
    environment: "production"
  });

  // Access client APIs (Stubs - throws NotImplementedError in this version)
  const client = sdk.getClient();
  
  // Access middleware layers for Express
  const middleware = sdk.getMiddleware();
  app.use("/api/v1/chat/proxy", middleware.proxyMiddleware);

} catch (err) {
  if (err instanceof SDKConfigurationError) {
    console.error("Invalid SDK configuration parameters:", err.message);
  }
}
```

---

## Exposed Class Surfaces

### 1. Configuration Options (`SDKOptions`)
- `apiBase` (Required string)
- `apiKey` (Required string)
- `productId` (Required string)
- `timeout` (Optional number)
- `environment` (Optional string)

### 2. Client Abstraction Methods
- `queryChatbot(botId, prompt)` — Sends prompt contextual payloads downstream.
- `getBranding(productId)` — Retrieves product branding variables.
- `syncDocuments(botId)` — Triggers vectorization jobs manually.

### 3. Middleware Handlers
- `requestMiddleware` — Parses inputs.
- `responseMiddleware` — Sanitizes response objects.
- `authenticationMiddleware` — Signature signer stub.
- `proxyMiddleware` — Request-forwarding proxy stub.
