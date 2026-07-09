# Deployment Guide

This guide covers deploying the Envoy chatbot widget and host server to production.

---

## Overview

A production Envoy deployment has three components:

```
Browser
  └── Your Website (serves the widget bundle)
        └── <envoy-chatbot> Web Component
              │
              ▼
        Your Host Server (Express or FastAPI + Backend SDK)
              │
              ▼
        Core Backend (apps/central-hub-backend)
```

You are responsible for deploying the first two. The core backend is deployed
separately by the backend team.

---

## Scenario 1 — Static HTML Embed

Use this when your website is a static site (no server-side rendering).

### Step 1: Build the widget bundle

```bash
cd packages/chatbot-ui
pnpm build
```

### Step 2: Host the bundle

Upload `packages/chatbot-ui/dist/chatbot-ui.js` to your CDN or static file server.

```
https://cdn.yourcompany.com/chatbot/chatbot-ui.js
```

### Step 3: Embed in your HTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>Your Website</title>
</head>
<body>

  <!-- Your website content -->

  <!-- Load the widget bundle from your CDN -->
  <script src="https://cdn.yourcompany.com/chatbot/chatbot-ui.js"></script>

  <!-- Place the widget element -->
  <envoy-chatbot
    data-bot-id="your-product-id"
    data-api-base="https://your-host-server.com"
  ></envoy-chatbot>

</body>
</html>
```

### Step 4: Deploy your host server

The widget needs a host server to fetch branding and process chat requests.
See Scenario 2 (Express) or Scenario 3 (FastAPI) below.

---

## Scenario 2 — Express Server Deployment

### Option A: Node.js with PM2

```bash
# Install PM2 globally
npm install -g pm2

# Navigate to the express server
cd ai-mock-integration/express-server

# Install dependencies
npm install --production

# Create production .env
cp .env.example .env
# Edit .env with production values

# Start with PM2
pm2 start server.js --name envoy-host-server

# Save PM2 process list (auto-restart on reboot)
pm2 save
pm2 startup
```

### Option B: Docker

Create a `Dockerfile` in `express-server/`:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

Build and run:

```bash
docker build -t envoy-host-server .
docker run -d \
  --name envoy-host-server \
  -p 3000:3000 \
  --env-file .env \
  envoy-host-server
```

### Environment variables for production

```bash
PORT=3000
NODE_ENV=production
CHATBOT_API_BASE=https://your-core-backend.com
CHATBOT_API_KEY=<your-production-api-key>
CHATBOT_PRODUCT_ID=<your-product-id>
CHATBOT_SIGNING_SECRET=<your-production-signing-secret>
```

---

## Scenario 3 — FastAPI Server Deployment

### Option A: uvicorn with gunicorn

```bash
cd ai-mock-integration/fastapi-server

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create production .env
cp .env.example .env
# Edit .env with production values

# Start with gunicorn (4 workers)
gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### Option B: Docker

Create a `Dockerfile` in `fastapi-server/`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
EXPOSE 8000
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Build and run:

```bash
docker build -t envoy-fastapi-server .
docker run -d \
  --name envoy-fastapi-server \
  -p 8000:8000 \
  --env-file .env \
  envoy-fastapi-server
```

---

## CORS Configuration

In production, restrict CORS to your actual frontend domain.

### Express

```javascript
// Replace the wildcard CORS header with your domain
res.setHeader('Access-Control-Allow-Origin', 'https://yourwebsite.com');
```

### FastAPI

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourwebsite.com"],
    ...
)
```

---

## HTTPS

Always use HTTPS in production. The widget makes API calls from the browser,
and browsers block mixed-content requests (HTTPS page calling HTTP API).

- Use a reverse proxy (nginx, Caddy, AWS ALB) to terminate TLS
- Ensure `CHATBOT_API_BASE` uses `https://` in production
- Ensure `data-api-base` on the widget element uses `https://`

---

## Security Checklist

Before deploying to production, verify:

```
✓ CHATBOT_SIGNING_SECRET is a long, random string (minimum 32 characters)
✓ CHATBOT_SIGNING_SECRET is NOT committed to version control
✓ CHATBOT_API_KEY is NOT committed to version control
✓ .env files are listed in .gitignore
✓ CORS is restricted to your actual frontend domain (not *)
✓ All API calls use HTTPS
✓ The widget bundle is served from HTTPS
✓ NODE_ENV=production (Express) or ENVIRONMENT=production (FastAPI)
✓ The signing secret matches between your host server and the core backend
```

---

## Rotating API Keys and Signing Secrets

When rotating credentials:

1. Generate a new key/secret
2. Update the core backend configuration first
3. Update your host server `.env` and restart
4. Verify the widget still works end-to-end
5. Revoke the old key/secret

The core backend supports a transition period where both the current and previous
signing secrets are valid simultaneously. See `packages/security/SECURITY_SPECIFICATION.md`
for the key rotation policy.
