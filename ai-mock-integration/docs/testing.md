# Testing Guide

A local testing harness for verifying every integration checkpoint in the
Envoy chatbot platform.

---

## Prerequisites

Before running any tests, ensure:

1. The widget bundle is built: `packages/chatbot-ui/dist/chatbot-ui.js` exists
2. The Express mock server is running on `http://localhost:3000`

```bash
# Build the widget
cd packages/chatbot-ui && pnpm build

# Start the Express server
cd ai-mock-integration/express-server && npm start
```

---

## Verification Checklist

Work through each checkpoint in order. Each one builds on the previous.

---

### Checkpoint 1 — Widget Bundle Loads

**What to verify:** The compiled widget JavaScript file is served correctly.

**Test:**

```bash
curl -I http://localhost:3000/packages/chatbot-ui/dist/chatbot-ui.js
```

**Expected:**

```
HTTP/1.1 200 OK
Content-Type: application/javascript
```

**Browser test:**

Open `http://localhost:3000` and check DevTools → Network tab.
Filter by `chatbot-ui.js`. The request should show status 200.

---

### Checkpoint 2 — Widget Renders

**What to verify:** The `<envoy-chatbot>` custom element is registered and renders
a launcher button.

**Browser test:**

1. Open `http://localhost:3000`
2. Open DevTools → Elements tab
3. Find `<envoy-chatbot id="envoy-widget">`
4. Expand it — you should see `#shadow-root (open)` containing the launcher button

**Console test:**

```javascript
// Run in browser console
const widget = document.getElementById('envoy-widget');
console.log(widget.shadowRoot); // Should not be null
console.log(widget.shadowRoot.getElementById('envoy-launcher')); // Should be a button element
```

---

### Checkpoint 3 — Server Health

**What to verify:** The mock server is running and the SDK initialized correctly.

**Test:**

```bash
curl http://localhost:3000/health
```

**Expected:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T00:00:00.000Z",
  "version": "1.0.0",
  "server": "envoy-mock-express",
  "sdk_initialized": true
}
```

---

### Checkpoint 4 — Branding Loads

**What to verify:** The widget fetches branding from the server and applies it.

**API test:**

```bash
curl http://localhost:3000/api/v1/products/tensor
```

**Expected:** A JSON object containing `ui_theme_config` with colors, typography,
layout, content, and featureFlags.

**Browser test:**

1. Open `http://localhost:3000`
2. Open DevTools → Network tab
3. Look for a request to `/api/v1/products/tensor`
4. It should return 200 with the branding JSON
5. The widget header should show "Tensor Assistant" (not the default "Envoy Support Assistant")

**Console test:**

```javascript
// Run in browser console after page loads
// The widget title should reflect the loaded branding
const widget = document.getElementById('envoy-widget');
const titleEl = widget.shadowRoot.getElementById('envoy-title');
console.log('Widget title:', titleEl.textContent); // Should be "Tensor Assistant"
```

---

### Checkpoint 5 — Widget Opens and Closes

**What to verify:** The public JavaScript API works correctly.

**Browser test:**

```javascript
// Run in browser console
const widget = document.getElementById('envoy-widget');

// Open the chat window
widget.open();
// Expected: chat window appears

// Close it
widget.close();
// Expected: chat window disappears

// Toggle
widget.toggle();
// Expected: chat window appears again
widget.toggle();
// Expected: chat window disappears
```

---

### Checkpoint 6 — Chat Request (JSON)

**What to verify:** The `POST /api/v1/chat` endpoint accepts a valid request
and returns a `ChatResponse`.

**Test:**

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "bot_id": "tensor",
    "conversation_id": "conv_test_001",
    "prompt": "Hello! What can you help me with?",
    "stream": false
  }'
```

**Expected:**

```json
{
  "success": true,
  "message": {
    "id": "msg_...",
    "conversation_id": "conv_test_001",
    "sender": "bot",
    "text": "Hello! I am the Envoy AI assistant...",
    "timestamp": "..."
  }
}
```

---

### Checkpoint 7 — SDK Request Validation

**What to verify:** The SDK's `requestMiddleware` rejects invalid payloads with 400.

**Test — missing bot_id:**

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello"}'
```

**Expected:**

```json
{
  "success": false,
  "error": "Bad Request: \"bot_id\" parameter is required."
}
```

**Test — missing prompt:**

```bash
curl -X POST http://localhost:3000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"bot_id": "tensor"}'
```

**Expected:**

```json
{
  "success": false,
  "error": "Bad Request: \"prompt\" parameter is required."
}
```

---

### Checkpoint 8 — SSE Streaming

**What to verify:** The `GET /api/v1/chat/stream` endpoint streams SSE chunks correctly.

**Test:**

```bash
curl -N "http://localhost:3000/api/v1/chat/stream?bot_id=tensor&prompt=Hello"
```

**Expected output (streaming):**

```
data: {"event":"text","text":"H"}
data: {"event":"text","text":"e"}
data: {"event":"text","text":"l"}
...
data: {"event":"done","message_id":"msg_..."}
```

The `-N` flag disables curl's output buffering so you see chunks as they arrive.

**Browser test:**

1. Open `http://localhost:3000`
2. Open the chat widget
3. Type a message and send it
4. Open DevTools → Network tab
5. Look for a request to `/api/v1/chat/stream`
6. Click on it → EventStream tab
7. You should see individual text chunks arriving

---

### Checkpoint 9 — Widget Sends and Receives Messages

**What to verify:** The full widget → server → response cycle works end-to-end.

**Browser test:**

1. Open `http://localhost:3000`
2. Click the launcher button to open the chat
3. Type "Hello" and press Enter
4. The user message should appear immediately
5. The typing indicator should appear briefly
6. The bot response should stream in character by character
7. The event log panel should show `envoy-message-sent` and `envoy-message-received`

---

### Checkpoint 10 — Error Handling

**What to verify:** The widget handles server errors gracefully.

**Test — unknown product ID:**

```bash
curl http://localhost:3000/api/v1/products/nonexistent-product
```

**Expected:**

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Product \"nonexistent-product\" was not found.",
    ...
  }
}
```

**Widget behavior:** When branding fetch fails, the widget falls back to the
default theme and still functions normally.

---

### Checkpoint 11 — Custom Events

**What to verify:** All four custom events fire correctly.

**Browser test:**

```javascript
// Run in browser console
const widget = document.getElementById('envoy-widget');

widget.addEventListener('envoy-chat-opened',    () => console.log('✓ envoy-chat-opened'));
widget.addEventListener('envoy-chat-closed',    () => console.log('✓ envoy-chat-closed'));
widget.addEventListener('envoy-message-sent',   (e) => console.log('✓ envoy-message-sent', e.detail));
widget.addEventListener('envoy-message-received',(e) => console.log('✓ envoy-message-received', e.detail));

// Now interact with the widget and verify each event fires
widget.open();    // Should log: ✓ envoy-chat-opened
widget.close();   // Should log: ✓ envoy-chat-closed
widget.sendMessage('Test message');  // Should log: ✓ envoy-message-sent, then ✓ envoy-message-received
```

---

## Running the Package Unit Tests

Each package has its own unit test suite.

```bash
# Backend SDK tests (HMAC signing, middleware validation)
cd packages/chatbot-backend-sdk
npm test

# Shared contracts tests (payload validation)
cd packages/shared-contracts
# (no test runner configured — tests are in src/tests/contracts.test.ts)

# Security package tests (canonical request, signature verification)
cd packages/security
# (no test runner configured — tests are in src/tests/security.test.ts)
```

---

## Full Verification Summary

```
Checkpoint 1  ✓ Widget bundle loads (HTTP 200 on chatbot-ui.js)
Checkpoint 2  ✓ Widget renders (shadow root + launcher button present)
Checkpoint 3  ✓ Server health (GET /health returns healthy)
Checkpoint 4  ✓ Branding loads (widget title shows product name)
Checkpoint 5  ✓ Widget API works (open/close/toggle)
Checkpoint 6  ✓ Chat request accepted (POST /api/v1/chat returns ChatResponse)
Checkpoint 7  ✓ SDK validation works (400 on missing fields)
Checkpoint 8  ✓ SSE streaming works (chunks arrive in order)
Checkpoint 9  ✓ End-to-end message flow works
Checkpoint 10 ✓ Error handling works (404 on unknown product)
Checkpoint 11 ✓ Custom events fire correctly
```

All 11 checkpoints passing means the integration is working correctly.
