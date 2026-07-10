# @envoy/chatbot-ui

Framework-agnostic, plug-and-play chatbot widget built as a Web Component.
Embeds into any website with a single `<script>` tag and a single HTML element.
No React, Vue, Angular, or any other framework required.

---

## Features

- Web Component (`<envoy-chatbot>`) — works in any HTML page
- Shadow DOM isolation — widget styles never conflict with the host page
- Dynamic branding — fetches colors, fonts, and content from your backend at runtime
- SSE streaming — bot responses stream token by token in real time
- Conversation history — persists chat history in `localStorage`
- Feature flags — enable/disable file upload, voice input, suggestions, and more
- Public JavaScript API — `open()`, `close()`, `toggle()`, `sendMessage()`, `resetConversation()`, `destroy()`
- Custom events — `envoy-chat-opened`, `envoy-chat-closed`, `envoy-message-sent`, `envoy-message-received`

---

## Installation

### Option A — Build from source (monorepo)

```bash
cd packages/chatbot-ui
pnpm install
pnpm build
```

Output: `packages/chatbot-ui/dist/chatbot-ui.js`

### Option B — Install from npm (when published)

```bash
npm install @envoy/chatbot-ui
```

---

## Quick Start

### Step 1 — Load the bundle

```html
<script src="/path/to/chatbot-ui.js"></script>
```

### Step 2 — Place the element

```html
<envoy-chatbot
  data-bot-id="your-product-id"
  data-api-base="https://your-host-server.com"
></envoy-chatbot>
```

That is the entire embed. The widget registers itself, fetches branding, and renders.

---

## HTML Attributes

| Attribute | Required | Description |
| :--- | :--- | :--- |
| `data-bot-id` | Yes | Product/tenant ID. Used to fetch branding from `GET /api/v1/products/:botId`. |
| `data-api-base` | No | Base URL of your host server. Defaults to `window.location.origin`. |

---

## JavaScript API

```javascript
const widget = document.getElementById('my-widget');

widget.open();                          // Open the chat window
widget.close();                         // Close the chat window
widget.toggle();                        // Toggle open/closed
widget.sendMessage('Hello!');           // Send a message programmatically
widget.resetConversation();             // Clear messages and reset to welcome state
widget.destroy();                       // Remove the widget from the DOM
```

---

## Custom Events

All events bubble and are composed (cross Shadow DOM boundaries).

```javascript
widget.addEventListener('envoy-chat-opened',     () => { /* chat opened */ });
widget.addEventListener('envoy-chat-closed',     () => { /* chat closed */ });
widget.addEventListener('envoy-message-sent',    (e) => console.log(e.detail.text));
widget.addEventListener('envoy-message-received',(e) => console.log(e.detail.text));
```

---

## Branding

The widget fetches branding from `GET {data-api-base}/api/v1/products/{data-bot-id}` on startup.
The response must include a `ui_theme_config` object with the following structure:

```json
{
  "ui_theme_config": {
    "colors":       { "primaryColor": "#2563EB", ... },
    "typography":   { "fontFamily": "Inter, sans-serif", ... },
    "layout":       { "chatWidth": "380px", "chatHeight": "520px", ... },
    "assets":       { "companyLogo": "", ... },
    "content":      { "widgetTitle": "My Assistant", "welcomeMessage": "Hello!", ... },
    "featureFlags": { "streamingResponses": true, "conversationHistory": true, ... }
  }
}
```

If the fetch fails, the widget falls back to the default Envoy theme and still functions normally.

See `ai-mock-integration/configs/sample-branding.json` for a complete example.

---

## Streaming

When `featureFlags.streamingResponses` is `true`, the widget calls:

```
GET {data-api-base}/api/v1/chat/stream?bot_id={botId}&prompt={encodedPrompt}
```

The server must respond with `Content-Type: text/event-stream` and emit chunks:

```
data: {"event":"text","text":"Hello"}

data: {"event":"done","message_id":"msg_123"}
```

See `packages/shared-contracts/API_SPECIFICATION.md` for the full SSE specification.

---

## Development

```bash
# Start the Vite dev server with hot reload
cd packages/chatbot-ui
pnpm dev

# Open the test-bed page
http://localhost:5173
```

The `index.html` test-bed exercises the widget lifecycle, public API, and Shadow DOM isolation.

---

## Build

```bash
pnpm build
```

Produces a single UMD bundle at `dist/chatbot-ui.js`.
The bundle is self-contained — it includes all styles injected via Shadow DOM.

---

## Testing

```bash
# Unit tests (BrandingValidator, CSSVariableMapper, widget lifecycle)
# Tests are in src/tests/widget.test.ts
```

---

## Integration Demo

See `ai-mock-integration/` for a complete working demo including:
- A mock website embedding the widget
- An Express mock server
- A FastAPI mock server
- Full developer documentation
