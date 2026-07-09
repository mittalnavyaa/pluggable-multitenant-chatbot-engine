# Configuration Guide

Complete reference for all configuration options in the Envoy chatbot platform.

---

## 1. Widget HTML Attributes

The `<envoy-chatbot>` Web Component is configured via HTML attributes.

```html
<envoy-chatbot
  data-bot-id="tensor"
  data-api-base="https://your-host-server.com"
></envoy-chatbot>
```

| Attribute | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `data-bot-id` | string | Yes | — | The product/tenant ID. The widget fetches branding for this ID from `GET /api/v1/products/:botId` on startup. |
| `data-api-base` | string | No | `window.location.origin` | Base URL of your host server. All widget API calls go to this origin. |

### Changing attributes dynamically

The widget observes both attributes. Changing them after mount triggers a branding reload:

```javascript
const widget = document.getElementById('envoy-widget');

// Switch to a different product at runtime
widget.setAttribute('data-bot-id', 'admissions');
widget.setAttribute('data-api-base', 'https://admissions.example.com');
```

---

## 2. Backend SDK Options (`SDKOptions`)

Passed to `createChatbotSDK()` when initializing the SDK in your host server.

```javascript
const sdk = createChatbotSDK({
  apiBase:       'http://localhost:8000',
  apiKey:        'envoy_prod_key_xyz',
  productId:     'tensor',
  signingSecret: 'your-signing-secret',
  timeout:       5000,
  retries:       3,
  environment:   'production',
});
```

| Option | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `apiBase` | string | Yes | — | Base URL of the core FastAPI backend. Must be a non-empty string URL. |
| `apiKey` | string | Yes | — | Your platform API key. Injected into `X-Envoy-API-Key` header on every proxied request. |
| `productId` | string | Yes | — | Your tenant product ID. Injected into `X-Envoy-Product-ID` header. Must match a `product_id` in the database. |
| `signingSecret` | string | Yes | — | Secret used to compute HMAC-SHA256 request signatures. Must match the secret configured in the core backend. |
| `timeout` | number | No | `5000` | Request timeout in milliseconds. Requests exceeding this limit throw `ProxyTimeoutError`. |
| `retries` | number | No | `3` | Number of retry attempts on transient failures (5xx errors, connection refused). Uses exponential backoff. |
| `environment` | string | No | `'development'` | Environment name. Used for logging. |

### Validation

The SDK validates all options on instantiation. Missing or invalid values throw `SDKConfigurationError`:

```javascript
import { createChatbotSDK, SDKConfigurationError } from '@envoy/chatbot-backend-sdk';

try {
  const sdk = createChatbotSDK({ /* options */ });
} catch (err) {
  if (err instanceof SDKConfigurationError) {
    console.error('Invalid SDK configuration:', err.message);
  }
}
```

---

## 3. Environment Variables

### Express Server (`express-server/.env`)

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | No | `3000` | Port the server listens on |
| `NODE_ENV` | No | `development` | Environment name |
| `CHATBOT_API_BASE` | Yes | — | Core backend URL (e.g. `http://localhost:8000`) |
| `CHATBOT_API_KEY` | Yes | — | Platform API key |
| `CHATBOT_PRODUCT_ID` | Yes | — | Tenant product ID |
| `CHATBOT_SIGNING_SECRET` | Yes | — | HMAC signing secret |

### FastAPI Server (`fastapi-server/.env`)

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `PORT` | No | `8001` | Port the server listens on |
| `ENVIRONMENT` | No | `development` | Environment name |
| `CHATBOT_API_KEY` | Yes | — | Platform API key |
| `CHATBOT_PRODUCT_ID` | Yes | — | Tenant product ID |
| `CHATBOT_SIGNING_SECRET` | Yes | — | HMAC signing secret |

---

## 4. Branding Configuration Schema

The branding configuration is stored in the database as a JSON object in the
`ui_theme_config` column of the `internal_products` table. The widget fetches
it on startup and applies it dynamically.

The full schema is defined in `packages/chatbot-ui/src/branding/branding-types.ts`.

### `colors`

Controls all color values in the widget. All values must be valid hex (`#rrggbb` or `#rgb`)
or `rgb()`/`rgba()` strings. Invalid values fall back to the default theme.

| Field | Default | Description |
| :--- | :--- | :--- |
| `primaryColor` | `#2563eb` | Launcher button, header, send button, user message bubbles |
| `secondaryColor` | `#475569` | Secondary UI elements |
| `accentColor` | `#10b981` | Accent highlights |
| `backgroundColor` | `#f8fafc` | Message area background |
| `surfaceColor` | `#ffffff` | Chat window surface, bot message bubbles |
| `borderColor` | `#e2e8f0` | Borders and dividers |
| `textColor` | `#0f172a` | Primary text |
| `mutedTextColor` | `#64748b` | Placeholder text, timestamps |
| `successColor` | `#16a34a` | Success states |
| `warningColor` | `#d97706` | Warning states |
| `errorColor` | `#dc2626` | Error states |

### `typography`

| Field | Default | Description |
| :--- | :--- | :--- |
| `fontFamily` | `Inter, system-ui, sans-serif` | Font stack applied inside Shadow DOM |
| `fontSize` | `14px` | Base font size |
| `headingWeight` | `600` | Font weight for headings |
| `bodyWeight` | `400` | Font weight for body text |
| `messageTextSize` | `13px` | Font size for message bubbles |
| `buttonTextSize` | `13px` | Font size for buttons |

### `layout`

| Field | Default | Description |
| :--- | :--- | :--- |
| `chatWidth` | `380px` | Width of the expanded chat window |
| `chatHeight` | `520px` | Height of the expanded chat window |
| `borderRadius` | `12px` | Border radius of the chat window |
| `padding` | `16px` | Internal padding |
| `spacing` | `12px` | Gap between elements |
| `bubbleRadius` | `8px` | Border radius of message bubbles |

### `assets`

| Field | Default | Description |
| :--- | :--- | :--- |
| `companyLogo` | `''` | URL of the company logo. Empty string disables it. |
| `chatAvatar` | `''` | URL of the chat avatar icon |
| `botAvatar` | `''` | URL of the bot avatar shown next to bot messages |
| `launcherIcon` | `''` | URL of a custom launcher button icon |
| `headerIcon` | `''` | URL of an icon shown in the chat header |

Asset URLs must be absolute (`https://`) or root-relative (`/path`).

### `content`

| Field | Default | Description |
| :--- | :--- | :--- |
| `widgetTitle` | `Envoy Support Assistant` | Title shown in the chat header |
| `welcomeMessage` | `Hello! I am your Envoy AI helper...` | First message shown when chat opens |
| `placeholderText` | `Type a message...` | Input field placeholder |
| `offlineMessage` | `We are currently offline...` | Shown when the bot is unavailable |
| `errorMessage` | `Something went wrong...` | Shown on request failure |
| `typingIndicatorText` | `Agent is typing...` | Text shown during the typing animation |

### `featureFlags`

Boolean flags that enable or disable widget features at runtime.

| Flag | Default | Description |
| :--- | :--- | :--- |
| `fileUpload` | `true` | Shows the file attachment button in the input area |
| `voiceInput` | `false` | Shows the microphone button in the input area |
| `suggestedQuestions` | `true` | Shows suggested question chips before the first message |
| `typingAnimation` | `true` | Shows the animated typing indicator while waiting for a response |
| `streamingResponses` | `true` | Enables SSE streaming. When false, waits for the full response before displaying. |
| `conversationHistory` | `true` | Persists conversation history in `localStorage` across page reloads |

---

## 5. Security Headers

The SDK injects these headers on every proxied request to the core backend.
The core backend verifies them before processing the request.

| Header | Source | Description |
| :--- | :--- | :--- |
| `X-Envoy-API-Key` | `SDKOptions.apiKey` | Platform API key |
| `X-Envoy-Product-ID` | `SDKOptions.productId` | Tenant product ID |
| `X-Envoy-Signature` | Computed by `HMACSignatureProvider` | HMAC-SHA256 signature of the request payload |
| `X-Envoy-Timestamp` | Current Unix epoch (ms) | Used in signature computation. Requests older than 5 minutes are rejected. |
| `X-Envoy-Nonce` | 16-byte random hex | Prevents replay attacks. Each nonce can only be used once. |

See `packages/security/SECURITY_SPECIFICATION.md` for the full cryptographic specification.
