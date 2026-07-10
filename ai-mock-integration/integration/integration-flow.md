# End-to-End Integration Flow

This document traces every network request and code execution step from the moment
a user opens a web page to the moment a bot response appears in the chat window.

---

## Complete Flow Diagram

```
Browser                    Host Server                  Core Backend
(html-demo/index.html)     (express-server/server.js)   (apps/central-hub-backend)
        │                          │                            │
        │  Page loads              │                            │
        │  <script> loads          │                            │
        │  chatbot-ui.js           │                            │
        │                          │                            │
        │  customElements.define() │                            │
        │  registers <envoy-chatbot>                            │
        │                          │                            │
        │  connectedCallback()     │                            │
        │  runs on mount           │                            │
        │                          │                            │
        │──── GET /api/v1/products/tensor ──────────────────────▶
        │                          │                            │
        │◀─── 200 { ui_theme_config: { colors, layout... } } ───
        │                          │                            │
        │  BrandingStore applies   │                            │
        │  theme to Shadow DOM     │                            │
        │                          │                            │
        │  Widget renders with     │                            │
        │  product branding        │                            │
        │                          │                            │
        │  [User clicks launcher]  │                            │
        │  Chat window opens       │                            │
        │  envoy-chat-opened fires │                            │
        │                          │                            │
        │  [User types message]    │                            │
        │  [User presses Enter]    │                            │
        │                          │                            │
        │  sendMessage() called    │                            │
        │  User bubble rendered    │                            │
        │  envoy-message-sent fires│                            │
        │                          │                            │
        │  streamingResponses=true │                            │
        │  fetch() to stream URL   │                            │
        │                          │                            │
        │──── GET /api/v1/chat/stream?bot_id=tensor&prompt=... ─▶
        │                          │                            │
        │                          │  [SDK middleware runs]     │
        │                          │  requestMiddleware:        │
        │                          │  validates bot_id, prompt  │
        │                          │                            │
        │                          │  proxyMiddleware:          │
        │                          │  1. HMACSignatureProvider  │
        │                          │     .sign(payload)         │
        │                          │  2. Injects headers:       │
        │                          │     X-Envoy-Signature      │
        │                          │     X-Envoy-Timestamp      │
        │                          │     X-Envoy-Nonce          │
        │                          │     X-Envoy-API-Key        │
        │                          │     X-Envoy-Product-ID     │
        │                          │                            │
        │                          │──── POST /api/v1/chat/stream ──────────────▶
        │                          │     (with signature headers)               │
        │                          │                                             │
        │                          │                            │  Verify HMAC  │
        │                          │                            │  Check nonce  │
        │                          │                            │  Check skew   │
        │                          │                            │  Query Qdrant │
        │                          │                            │  Call LLM     │
        │                          │                            │               │
        │◀─── SSE: data: {"event":"text","text":"H"} ──────────────────────────◀
        │◀─── SSE: data: {"event":"text","text":"e"} ──────────────────────────◀
        │◀─── SSE: data: {"event":"text","text":"l"} ──────────────────────────◀
        │  (each chunk renders     │                            │               │
        │   immediately in the     │                            │               │
        │   message bubble)        │                            │               │
        │◀─── SSE: data: {"event":"done","message_id":"..."} ──────────────────◀
        │                          │                            │
        │  Stream complete         │                            │
        │  envoy-message-received  │                            │
        │  fires with full text    │                            │
        │                          │                            │
```

---

## Step-by-Step Breakdown

### Step 1 — Page Load and Widget Registration

**File:** `html-demo/index.html`

The browser loads the page and encounters:

```html
<script src="../../packages/chatbot-ui/dist/chatbot-ui.js"></script>
```

The UMD bundle executes and runs:

```javascript
if (!customElements.get('envoy-chatbot')) {
  customElements.define('envoy-chatbot', EnvoyChatbot);
}
```

The `<envoy-chatbot>` custom element is now registered in the browser.

---

### Step 2 — Widget Mount (`connectedCallback`)

**File:** `packages/chatbot-ui/src/index.ts`

When the browser parses `<envoy-chatbot data-bot-id="tensor" data-api-base="http://localhost:3000">`,
it calls `connectedCallback()` on the element:

```typescript
async connectedCallback() {
  this.botId = this.getAttribute('data-bot-id') || '';
  this.apiBase = this.getAttribute('data-api-base') || window.location.origin;
  this.renderStructure();          // Build Shadow DOM
  brandingStore.addListener(...);  // Subscribe to branding updates
  this.refreshBranding();          // Trigger branding fetch
  this.setupListeners();           // Attach event handlers
}
```

The Shadow DOM is created with `this.attachShadow({ mode: 'open' })`.
All widget HTML and CSS live inside this shadow root, isolated from the host page.

---

### Step 3 — Branding Fetch

**File:** `packages/chatbot-ui/src/branding/branding-store.ts`

`BrandingStore.loadBranding()` fetches:

```
GET http://localhost:3000/api/v1/products/tensor
```

**Server handler** (`express-server/server.js`):

```javascript
app.get('/api/v1/products/:productId', (req, res) => {
  const branding = brandingMap[req.params.productId];
  res.json({ id: productId, product_id: productId, ui_theme_config: branding, ... });
});
```

The widget reads `data.ui_theme_config`, validates it through `BrandingValidator`,
and applies it via `CSSVariableMapper` which sets CSS custom properties on the
shadow host element.

---

### Step 4 — User Sends a Message

**File:** `packages/chatbot-ui/src/index.ts`

The user types a message and presses Enter. The form submit handler calls:

```typescript
public async sendMessage(text: string) {
  // 1. Append user message bubble to Shadow DOM
  // 2. Save to localStorage if conversationHistory is enabled
  // 3. Dispatch envoy-message-sent custom event
  // 4. Call generateBotResponse(text)
}
```

---

### Step 5 — Widget Initiates SSE Stream

**File:** `packages/chatbot-ui/src/index.ts` — `generateBotResponse()`

Because `featureFlags.streamingResponses` is `true`:

```typescript
const streamUrl = `${this.apiBase}/api/v1/chat/stream?bot_id=${this.botId}&prompt=${encodeURIComponent(userPrompt)}`;
const response = await fetch(streamUrl);
const reader = response.body.getReader();
```

---

### Step 6 — SDK Middleware Validates the Request

**File:** `packages/chatbot-backend-sdk/src/middleware/index.ts`

`requestMiddleware` runs first:

```typescript
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
```

---

### Step 7 — SDK Signs the Request

**File:** `packages/chatbot-backend-sdk/src/utils/crypto.ts`

`HMACSignatureProvider.sign()` computes:

```
message = "{timestamp}.{nonce}.{JSON.stringify(payload)}"
signature = HMAC-SHA256(signingSecret, message)
```

And returns headers:

```
X-Envoy-Signature:  <64-char hex digest>
X-Envoy-Timestamp:  <unix epoch ms>
X-Envoy-Nonce:      <32-char random hex>
X-Envoy-API-Key:    <your api key>
X-Envoy-Product-ID: <your product id>
```

---

### Step 8 — Core Backend Verifies and Responds

**File:** `packages/security/src/verification/index.ts`

The core backend's verification middleware:

1. Checks `X-Envoy-Timestamp` is within 5 minutes of server time
2. Checks `X-Envoy-Nonce` has not been seen before (replay attack prevention)
3. Re-computes the canonical request string
4. Computes expected HMAC and compares with `X-Envoy-Signature` using constant-time comparison

If all checks pass, the request is processed by the RAG pipeline.

---

### Step 9 — SSE Chunks Stream Back

The core backend (or mock server) writes SSE chunks:

```
data: {"event":"text","text":"H"}\n\n
data: {"event":"text","text":"e"}\n\n
data: {"event":"text","text":"l"}\n\n
...
data: {"event":"done","message_id":"msg_..."}\n\n
```

The widget's `ReadableStream` reader processes each chunk:

```typescript
while (true) {
  const { value, done } = await reader.read();
  if (done) break;
  const chunk = decoder.decode(value, { stream: true });
  // Parse "data: {...}" lines
  // Append text to the message bubble
  // Scroll to bottom
}
```

---

### Step 10 — Stream Complete

When the `done` event chunk arrives, the widget:

1. Marks the message as no longer streaming
2. Saves the conversation to `localStorage` (if `conversationHistory` is enabled)
3. Dispatches `envoy-message-received` custom event with the full response text

The host page's event listener receives the event:

```javascript
widget.addEventListener('envoy-message-received', (e) => {
  console.log('Bot said:', e.detail.text);
  // Log to analytics, trigger follow-up actions, etc.
});
```

---

## Headers Injected at Each Hop

| Hop | Direction | Headers |
| :--- | :--- | :--- |
| Widget → Host Server | Browser → Server | `Content-Type: application/json` |
| Host Server → Core Backend | Server → Server | `Content-Type: application/json`, `X-Envoy-API-Key`, `X-Envoy-Product-ID`, `X-Envoy-Signature`, `X-Envoy-Timestamp`, `X-Envoy-Nonce` |

The browser **never** sends the security headers. They are added exclusively by the
SDK middleware on the server side.
