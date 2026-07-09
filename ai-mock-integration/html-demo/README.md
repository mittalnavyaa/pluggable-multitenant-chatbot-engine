# HTML Demo

A standalone mock website that embeds the `<envoy-chatbot>` Web Component widget
and demonstrates the complete frontend integration pattern.

---

## What This Demo Shows

| Feature | How It Is Demonstrated |
| :--- | :--- |
| Widget embed | Single `<script>` tag + single `<envoy-chatbot>` element |
| Shadow DOM isolation | Host page uses Comic Sans and red buttons — widget is unaffected |
| Branding load | Widget fetches from `GET /api/v1/products/tensor` on startup |
| Public JS API | Control panel buttons call `open()`, `close()`, `toggle()`, etc. |
| Custom events | Live event log captures all four widget events |
| SSE streaming | Bot responses stream token-by-token when connected to a server |

---

## Prerequisites

The widget bundle must be built before opening this page:

```bash
cd packages/chatbot-ui
pnpm install
pnpm build
```

This produces `packages/chatbot-ui/dist/chatbot-ui.js`.
The `index.html` loads it via a relative path:

```html
<script src="../../packages/chatbot-ui/dist/chatbot-ui.js"></script>
```

---

## Option A — With the Express Mock Server (Recommended)

This gives you full branding load, chat responses, and SSE streaming.

```bash
# Terminal 1 — start the Express server
cd ai-mock-integration/express-server
npm install
cp .env.example .env
npm start

# Then open in browser
http://localhost:3000
```

The Express server serves the `html-demo/` folder as static files and also
provides all the mock API endpoints the widget calls.

---

## Option B — Open Directly in Browser (No Server)

You can open `index.html` directly in your browser without any server.

```bash
# From the project root, just open the file
# On macOS:
open ai-mock-integration/html-demo/index.html

# On Windows:
start ai-mock-integration/html-demo/index.html
```

In this mode:
- The widget loads and renders correctly
- Branding fetch will fail (no server) — the widget falls back to its default theme
- Chat messages will use the widget's built-in simulated responses
- SSE streaming simulation still works (no server needed)

---

## Files

| File | Purpose |
| :--- | :--- |
| `index.html` | The mock website. Every line is commented for developer education. |
| `app.js` | Host-page JS. Demonstrates the widget public API and event listeners. |
| `style.css` | Intentionally aggressive styles to prove Shadow DOM isolation. |

---

## Widget Configuration in This Demo

The widget is configured via HTML attributes on the `<envoy-chatbot>` element:

```html
<envoy-chatbot
  id="envoy-widget"
  data-bot-id="tensor"
  data-api-base="http://localhost:3000"
></envoy-chatbot>
```

| Attribute | Value | Meaning |
| :--- | :--- | :--- |
| `data-bot-id` | `tensor` | Fetches branding for the "tensor" product |
| `data-api-base` | `http://localhost:3000` | All widget API calls go to this origin |

To test with a different product, change `data-bot-id` to any product ID that
exists in your backend (e.g. `admissions`, `hr-portal`).
