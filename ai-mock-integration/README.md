# Envoy Chatbot — Mock Integration Environment

This folder is the **developer onboarding and mock integration environment** for the
Envoy pluggable multi-tenant chatbot engine. It is the single place a new developer
needs to look to understand how all three layers of the platform connect and to run
a working end-to-end demo on their local machine in under ten minutes.

---

## What Is This Folder?

The Envoy platform is built from three independently developed layers:

| Layer | Package | Owner |
| :--- | :--- | :--- |
| Frontend Widget | `@envoy/chatbot-ui` | Widget team |
| Backend Proxy SDK | `@envoy/chatbot-backend-sdk` | SDK team |
| Core RAG Engine | `apps/central-hub-backend` | Backend team |

This folder **does not modify any of those packages**. It provides:

- A **mock Express server** that demonstrates how to integrate the Backend SDK into a Node.js host application
- A **mock FastAPI server** that demonstrates the same integration pattern in Python
- A **standalone HTML demo page** that embeds the Frontend Widget and connects it to either mock server
- **Sample configuration files** matching the exact schemas used by the real packages
- **Developer documentation** covering installation, configuration, deployment, and troubleshooting
- An **integration flow guide** explaining every network hop from browser to core engine

---

## Prerequisites

| Tool | Minimum Version | Check |
| :--- | :--- | :--- |
| Node.js | 18.x | `node --version` |
| npm | 9.x | `npm --version` |
| pnpm | 8.x | `pnpm --version` |
| Python | 3.11 | `python --version` |
| pip | 23.x | `pip --version` |

---

## Quick Start (3 Steps)

### Step 1 — Build the widget

From the project root:

```bash
cd packages/chatbot-ui
pnpm install
pnpm build
```

This produces `packages/chatbot-ui/dist/chatbot-ui.js` — the compiled UMD bundle
that the HTML demo page loads.

---

### Step 2 — Start the Express mock server

```bash
cd ai-mock-integration/express-server
npm install
cp .env.example .env
npm start
```

Server starts on `http://localhost:3000`.

---

### Step 3 — Open the HTML demo

Open your browser and navigate to:

```
http://localhost:3000
```

You will see a mock website with the Envoy chatbot widget embedded in the bottom-right
corner. Click the launcher button to open it, type a message, and watch the streaming
response appear.

---

## Folder Structure

```
ai-mock-integration/
├── README.md                        ← You are here
│
├── html-demo/                       ← Standalone HTML demo website
│   ├── index.html                   ← Mock website embedding the widget
│   ├── app.js                       ← Host-page JS demonstrating the widget public API
│   ├── style.css                    ← Intentionally aggressive styles to prove Shadow DOM isolation
│   └── README.md                    ← How to run the HTML demo
│
├── express-server/                  ← Node.js mock backend using the SDK
│   ├── server.js                    ← Express server with all mock endpoints
│   ├── package.json                 ← Dependencies (express + SDK via file: path)
│   ├── .env.example                 ← All environment variables documented
│   └── README.md                    ← Setup and usage guide
│
├── fastapi-server/                  ← Python mock backend (same endpoints)
│   ├── app.py                       ← FastAPI server with all mock endpoints
│   ├── requirements.txt             ← Python dependencies
│   ├── .env.example                 ← All environment variables documented
│   └── README.md                    ← Setup and usage guide
│
├── configs/                         ← Sample JSON configuration files
│   ├── sample-widget-config.json    ← Widget HTML attributes and JS API reference
│   ├── sample-branding.json         ← Complete branding payload (matches WidgetBrandingConfig)
│   └── sample-chat-response.json    ← JSON and SSE response shapes
│
├── docs/                            ← Developer documentation
│   ├── installation.md              ← Prerequisites and installation steps
│   ├── configuration.md             ← All configuration options documented
│   ├── deployment.md                ← Production deployment guide
│   ├── troubleshooting.md           ← Common problems and solutions
│   └── testing.md                   ← Local testing harness and verification checklist
│
└── integration/                     ← End-to-end integration documentation
    ├── README.md                    ← Integration overview
    └── integration-flow.md          ← Step-by-step flow with diagrams
```

---

## Documentation Index

| Document | Purpose |
| :--- | :--- |
| [Installation Guide](docs/installation.md) | Prerequisites, install steps, build verification |
| [Configuration Guide](docs/configuration.md) | SDK options, widget attributes, env vars, branding schema |
| [Deployment Guide](docs/deployment.md) | Static embed, Express, FastAPI, Docker, security checklist |
| [Troubleshooting Guide](docs/troubleshooting.md) | Common errors and fixes |
| [Testing Guide](docs/testing.md) | Local verification checklist with curl commands |
| [Integration Overview](integration/README.md) | What connects to what |
| [Integration Flow](integration/integration-flow.md) | Step-by-step network flow with diagrams |
| [HTML Demo Guide](html-demo/README.md) | Running the demo website |
| [Express Server Guide](express-server/README.md) | Running the Node.js mock server |
| [FastAPI Server Guide](fastapi-server/README.md) | Running the Python mock server |

---

## Architecture at a Glance

```
Browser
  └── html-demo/index.html
        └── <envoy-chatbot> Web Component  (packages/chatbot-ui/dist/chatbot-ui.js)
              │
              │  GET  /api/v1/products/:botId     ← fetch branding
              │  POST /api/v1/chat                ← send message
              │  GET  /api/v1/chat/stream         ← SSE streaming
              ▼
        express-server/server.js  OR  fastapi-server/app.py
              │
              │  Uses @envoy/chatbot-backend-sdk
              │  Signs requests with HMAC-SHA256
              │  Forwards to core backend
              ▼
        apps/central-hub-backend  (Core FastAPI RAG Engine)
```

---

## Which Server Should I Use?

| Scenario | Use |
| :--- | :--- |
| Your production host app is Node.js / Express | `express-server/` |
| Your production host app is Python / FastAPI | `fastapi-server/` |
| You just want to see the widget work | Either — both expose identical endpoints |
| You want to test without any server | Open `html-demo/index.html` directly — the widget falls back to simulated responses |
