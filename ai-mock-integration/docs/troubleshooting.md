# Troubleshooting Guide

Solutions to the most common problems encountered when integrating the Envoy chatbot widget.

---

## Widget Does Not Appear on the Page

**Symptom:** The page loads but no launcher button appears in the bottom-right corner.

**Causes and fixes:**

1. The widget bundle was not loaded.

   Check the browser console for a 404 error on `chatbot-ui.js`.

   Fix: Build the widget first.
   ```bash
   cd packages/chatbot-ui
   pnpm build
   ```
   Then verify the file exists at `packages/chatbot-ui/dist/chatbot-ui.js`.

2. The `<script>` tag path is wrong.

   Open browser DevTools → Network tab → filter by `chatbot-ui.js`.
   If the request shows 404, the path in your `<script src="...">` is incorrect.

   Fix: Use the correct relative or absolute path to the bundle.

3. The `<envoy-chatbot>` element is missing.

   Check that the HTML element is present in the page source:
   ```html
   <envoy-chatbot data-bot-id="tensor" data-api-base="http://localhost:3000"></envoy-chatbot>
   ```

4. A JavaScript error is preventing the custom element from registering.

   Open browser DevTools → Console tab. Look for any red errors.

---

## Branding Does Not Load (Widget Shows Default Blue Theme)

**Symptom:** The widget appears but uses the default blue theme instead of your product's colors.

**Causes and fixes:**

1. The host server is not running.

   Fix: Start the Express or FastAPI mock server.
   ```bash
   cd ai-mock-integration/express-server
   npm start
   ```

2. `data-api-base` points to the wrong URL.

   The widget fetches branding from `{data-api-base}/api/v1/products/{data-bot-id}`.
   Open DevTools → Network tab and look for a request to `/api/v1/products/...`.
   If it shows a network error or 404, the URL is wrong.

   Fix: Ensure `data-api-base` matches the URL where your server is running.

3. The product ID does not exist in the mock server.

   The Express mock server only has branding for `tensor` and `admissions`.

   Fix: Either use one of those IDs, or add your product to the `brandingMap` in `server.js`.

4. CORS is blocking the request.

   Open DevTools → Console. Look for a CORS error like:
   ```
   Access to fetch at 'http://localhost:3000/api/v1/products/tensor' from origin
   'null' has been blocked by CORS policy
   ```

   Fix: If opening `index.html` directly as a file (`file://`), the origin is `null`.
   Serve the page through the Express server instead: `http://localhost:3000`.

---

## Chat Messages Are Not Sent

**Symptom:** Typing a message and pressing Enter does nothing, or the message appears but no response comes.

**Causes and fixes:**

1. The host server is not running.

   Fix: Start the server. The widget falls back to simulated responses only when
   the streaming fetch fails. If the server is down, the fallback simulation runs.

2. The `POST /api/v1/chat` request is failing.

   Open DevTools → Network tab. Look for a POST request to `/api/v1/chat`.
   Check the response status and body.

3. The request body is missing `bot_id` or `prompt`.

   The SDK's `requestMiddleware` returns 400 if either field is missing.
   This should not happen with the widget, but check the request payload in DevTools.

---

## Streaming Does Not Work

**Symptom:** The bot response appears all at once instead of streaming character by character.

**Causes and fixes:**

1. The `streamingResponses` feature flag is `false` in the branding config.

   Fix: Set `featureFlags.streamingResponses: true` in your branding configuration.

2. The SSE endpoint is not reachable.

   The widget calls `GET /api/v1/chat/stream?bot_id=...&prompt=...`.
   Open DevTools → Network tab and look for this request.
   If it fails, the widget falls back to the simulated streaming mode (still streams, but locally).

3. A proxy or server is buffering the SSE response.

   Fix: Add the `X-Accel-Buffering: no` header to the SSE response (already included in both mock servers).
   If behind nginx, add `proxy_buffering off;` to your nginx config.

---

## SDK Configuration Error on Server Start

**Symptom:** The Express server exits immediately with an error like:
```
SDK Configuration Error: Parameter "signingSecret" must be a non-empty cryptographic signing secret string.
```

**Cause:** A required environment variable is missing or empty.

**Fix:**

1. Verify your `.env` file exists:
   ```bash
   ls ai-mock-integration/express-server/.env
   ```

2. Verify all required variables are set:
   ```bash
   cat ai-mock-integration/express-server/.env
   ```

3. Ensure none of the values are still the placeholder text `replace_me`.

---

## CORS Errors in the Browser

**Symptom:** Browser console shows:
```
Access to fetch at 'http://localhost:3000/...' has been blocked by CORS policy
```

**Causes and fixes:**

1. You are opening `index.html` directly as a `file://` URL.

   Fix: Serve the page through the Express server at `http://localhost:3000`.

2. The server is not sending CORS headers.

   Fix: Verify the CORS middleware is registered in `server.js` before any routes.

3. The `data-api-base` uses a different origin than the server.

   Fix: Ensure `data-api-base` exactly matches the server's origin (protocol + host + port).

---

## `widget.destroy()` Was Called Accidentally

**Symptom:** The widget disappears from the page and cannot be reopened.

**Cause:** `destroy()` removes the element from the DOM.

**Fix:** Re-add the element to the DOM:

```javascript
const newWidget = document.createElement('envoy-chatbot');
newWidget.setAttribute('id', 'envoy-widget');
newWidget.setAttribute('data-bot-id', 'tensor');
newWidget.setAttribute('data-api-base', 'http://localhost:3000');
document.body.appendChild(newWidget);
```

---

## Widget Styles Are Leaking Into the Host Page

**Symptom:** The host page's layout or fonts change after the widget loads.

**This should not happen.** The widget uses Shadow DOM, which fully isolates its styles.

If you are seeing style leakage, check:

1. The widget bundle was built correctly (not a development build).
2. No global CSS reset in the widget's `styles.css` is escaping the Shadow DOM.

Open DevTools → Elements tab → find the `<envoy-chatbot>` element → expand its
`#shadow-root`. All widget elements should be inside the shadow root.

---

## Python `ModuleNotFoundError` in FastAPI Server

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix:** Activate your virtual environment before running the server:

```bash
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Then install:
pip install -r requirements.txt
```

---

## Port Already in Use

**Symptom:**
```
Error: listen EADDRINUSE: address already in use :::3000
```

**Fix:** Either stop the process using the port, or change the port:

```bash
# Find what is using port 3000 (macOS/Linux):
lsof -i :3000

# Change the port in .env:
PORT=3001
```
