# Installation Guide

This guide walks you through installing and running the Envoy chatbot platform
locally from scratch.

---

## Prerequisites

Install the following tools before proceeding.

### Node.js and pnpm

The widget and Backend SDK are Node.js packages managed with pnpm.

```bash
# Check Node.js version (18 or higher required)
node --version

# Check pnpm version (8 or higher required)
pnpm --version

# Install pnpm if not present
npm install -g pnpm
```

### Python

The FastAPI mock server and the core backend require Python.

```bash
# Check Python version (3.11 or higher required)
python --version

# Check pip
pip --version
```

### Docker (Optional)

Required only if you want to run the full core backend stack (PostgreSQL, Qdrant, Redis, MinIO).

```bash
docker --version
docker compose version
```

---

## Step 1 — Clone the Repository

```bash
git clone <repository-url>
cd pluggable-multitenant-chatbot-engine
```

---

## Step 2 — Install Workspace Packages

From the project root, install all Node.js packages across the monorepo:

```bash
pnpm install
```

This installs dependencies for:
- `packages/chatbot-ui`
- `packages/chatbot-backend-sdk`
- `packages/shared-contracts`
- `packages/security`

---

## Step 3 — Build the Widget

The HTML demo page loads the compiled widget bundle. Build it now:

```bash
cd packages/chatbot-ui
pnpm build
```

Expected output:

```
✓ built in Xms
dist/chatbot-ui.js   XXX kB
```

Verify the build output exists:

```bash
# On macOS/Linux:
ls packages/chatbot-ui/dist/chatbot-ui.js

# On Windows:
dir packages\chatbot-ui\dist\chatbot-ui.js
```

If the file exists, the widget is ready to embed.

---

## Step 4 — Build the Backend SDK

The Express mock server imports the SDK via a local `file:` path. Build it so
the compiled JavaScript is available:

```bash
cd packages/chatbot-backend-sdk
npm run build
```

Expected output:

```
dist/index.js
dist/index.d.ts
```

---

## Step 5 — Set Up the Express Mock Server

```bash
cd ai-mock-integration/express-server

# Install dependencies (express, dotenv, and the local SDK)
npm install

# Create your environment file
cp .env.example .env
```

The default `.env` values work for local mock testing without any changes.
See the [Configuration Guide](configuration.md) if you want to point at a real backend.

---

## Step 6 — Start the Express Server

```bash
npm start
```

You should see:

```
╔══════════════════════════════════════════════════════════╗
║         Envoy Mock Express Server — Running              ║
╠══════════════════════════════════════════════════════════╣
║  Demo website:   http://localhost:3000                   ║
║  Health check:   http://localhost:3000/health            ║
...
```

---

## Step 7 — Open the Demo

Navigate to `http://localhost:3000` in your browser.

You should see the Acme Corp mock website with the Envoy chatbot widget in the
bottom-right corner. Click the launcher button to open it.

---

## Step 8 — Verify Everything Works

Run through this checklist:

```
✓ http://localhost:3000 loads the demo page
✓ The chatbot launcher button appears in the bottom-right corner
✓ Clicking the launcher opens the chat window
✓ The widget title shows "Tensor Assistant" (branding loaded from server)
✓ Typing a message and pressing Enter sends it
✓ The bot response streams back character by character
✓ http://localhost:3000/health returns {"status":"healthy"}
```

---

## Optional: Set Up the FastAPI Mock Server

If you prefer Python, set up the FastAPI server instead of (or alongside) the Express server.

```bash
cd ai-mock-integration/fastapi-server

# Create a virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env

# Start the server (runs on port 8001 by default)
python app.py
```

Then update the widget's `data-api-base` attribute in `html-demo/index.html`:

```html
<envoy-chatbot
  data-bot-id="tensor"
  data-api-base="http://localhost:8001"
></envoy-chatbot>
```

---

## Optional: Run the Full Core Backend Stack

To connect to the real AI engine instead of mock responses:

```bash
# From the project root
docker compose up -d
```

This starts PostgreSQL, Qdrant, Redis, MinIO, the FastAPI backend, and the Celery worker.

Then update `CHATBOT_API_BASE` in your `.env` file:

```
CHATBOT_API_BASE=http://localhost:8000
```

See `docker/setup-guide.md` for database seeding instructions.

---

## Troubleshooting Installation

| Problem | Solution |
| :--- | :--- |
| `pnpm: command not found` | Run `npm install -g pnpm` |
| `pnpm build` fails in chatbot-ui | Check that TypeScript is installed: `pnpm install` |
| `dist/chatbot-ui.js` not found | Run `pnpm build` inside `packages/chatbot-ui/` |
| `npm install` fails in express-server | Ensure `packages/chatbot-backend-sdk` exists and has been built |
| Port 3000 already in use | Change `PORT=3001` in `express-server/.env` |
| Widget shows but no branding | Express server is not running or `.env` is not configured |

For more detailed troubleshooting, see [troubleshooting.md](troubleshooting.md).
