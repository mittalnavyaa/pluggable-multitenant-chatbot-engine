'use strict';

/**
 * ai-mock-integration/express-server/server.js
 *
 * Mock Express server demonstrating how to integrate the
 * @envoy/chatbot-backend-sdk into a Node.js host application.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * WHAT THIS SERVER DOES
 * ─────────────────────────────────────────────────────────────────────────────
 * 1. Loads environment variables from .env
 * 2. Instantiates the Backend SDK with your credentials
 * 3. Registers SDK middleware on the chat proxy route
 * 4. Provides mock endpoints that return realistic responses
 * 5. Serves the html-demo/ folder as static files
 *
 * In production, you would replace the mock response bodies with real
 * calls to your core backend. The SDK middleware layer stays exactly the same.
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * ENDPOINTS PROVIDED
 * ─────────────────────────────────────────────────────────────────────────────
 *   GET  /                                  → Serves html-demo/index.html
 *   GET  /health                            → Health check
 *   GET  /api/v1/products/:productId        → Mock branding response
 *   POST /api/v1/chat                       → Mock JSON chat response (SDK middleware applied)
 *   GET  /api/v1/chat/stream                → Mock SSE streaming response
 * ─────────────────────────────────────────────────────────────────────────────
 */

// ─── Step 1: Load environment variables ──────────────────────────────────────
//
// dotenv reads the .env file in this directory and populates process.env.
// Copy .env.example to .env and fill in your values before starting.
//
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

// ─── Step 2: Import dependencies ─────────────────────────────────────────────

const express = require('express');

// Import the Backend SDK.
// The package.json references it via a local file: path so it works
// directly from the monorepo without publishing to npm.
const { createChatbotSDK, SDKConfigurationError } = require('@envoy/chatbot-backend-sdk');

// ─── Step 3: Read configuration from environment variables ───────────────────
//
// All sensitive values come from environment variables — never hardcode them.
// See .env.example for the full list of required variables.
//
const PORT             = process.env.PORT             || 3000;
const CHATBOT_API_BASE = process.env.CHATBOT_API_BASE || 'http://localhost:8000';
const CHATBOT_API_KEY  = process.env.CHATBOT_API_KEY;
const CHATBOT_PRODUCT_ID    = process.env.CHATBOT_PRODUCT_ID;
const CHATBOT_SIGNING_SECRET = process.env.CHATBOT_SIGNING_SECRET;

// Validate that required environment variables are present before starting
if (!CHATBOT_API_KEY || !CHATBOT_PRODUCT_ID || !CHATBOT_SIGNING_SECRET) {
  console.error('[envoy-server] ERROR: Missing required environment variables.');
  console.error('[envoy-server] Copy .env.example to .env and fill in all values.');
  console.error('[envoy-server] Required: CHATBOT_API_KEY, CHATBOT_PRODUCT_ID, CHATBOT_SIGNING_SECRET');
  process.exit(1);
}

// ─── Step 4: Instantiate the Backend SDK ─────────────────────────────────────
//
// createChatbotSDK() validates all options and throws SDKConfigurationError
// if any required field is missing or invalid.
//
// SDKOptions:
//   apiBase        — URL of the core FastAPI backend
//   apiKey         — Your platform API key (injected into X-Envoy-API-Key header)
//   productId      — Your tenant product ID (injected into X-Envoy-Product-ID header)
//   signingSecret  — Secret used to compute HMAC-SHA256 request signatures
//   timeout        — Request timeout in milliseconds (default: 5000)
//   retries        — Number of retry attempts on transient failures (default: 3)
//
let sdk;
try {
  sdk = createChatbotSDK({
    apiBase:       CHATBOT_API_BASE,
    apiKey:        CHATBOT_API_KEY,
    productId:     CHATBOT_PRODUCT_ID,
    signingSecret: CHATBOT_SIGNING_SECRET,
    timeout:       5000,
    retries:       3,
    environment:   process.env.NODE_ENV || 'development',
  });
  console.log('[envoy-server] Backend SDK initialized successfully.');
} catch (err) {
  if (err instanceof SDKConfigurationError) {
    console.error('[envoy-server] SDK configuration error:', err.message);
  } else {
    console.error('[envoy-server] Unexpected error initializing SDK:', err.message);
  }
  process.exit(1);
}

// ─── Step 5: Get middleware handlers from the SDK ────────────────────────────
//
// The SDK exposes four Express-compatible middleware functions:
//   requestMiddleware      — Validates bot_id and prompt fields
//   responseMiddleware     — Sanitizes response objects
//   authenticationMiddleware — Verifies X-Envoy-Signature header
//   proxyMiddleware        — Signs and forwards requests to the core backend
//
const middleware = sdk.getMiddleware();

// ─── Step 6: Create the Express application ───────────────────────────────────

const app = express();

// Parse JSON request bodies
app.use(express.json());

// ─── Step 7: CORS headers ────────────────────────────────────────────────────
//
// Allow the widget (running in the browser) to make requests to this server.
// In production, replace '*' with your actual frontend domain.
//
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-Envoy-Signature, X-Envoy-Timestamp, X-Envoy-Nonce, X-Envoy-API-Key, X-Envoy-Product-ID');
  if (req.method === 'OPTIONS') {
    return res.sendStatus(204);
  }
  next();
});

// ─── Step 8: Request logging ─────────────────────────────────────────────────

app.use((req, res, next) => {
  console.log(`[envoy-server] ${req.method} ${req.path}`);
  next();
});

// ─── Step 9: Serve the HTML demo as static files ─────────────────────────────
//
// This makes http://localhost:3000 serve the html-demo/index.html page.
// The widget bundle is served from the packages/chatbot-ui/dist/ folder.
//
app.use(express.static(path.join(__dirname, '..', 'html-demo')));

// Also serve the built widget bundle so the HTML demo can load it
app.use(
  '/packages/chatbot-ui/dist',
  express.static(path.join(__dirname, '..', '..', 'packages', 'chatbot-ui', 'dist'))
);

// ─── Endpoint 1: Health Check ─────────────────────────────────────────────────
//
// GET /health
//
// Returns the server status. The widget does not call this endpoint —
// it is provided for developer verification and monitoring.
//
// Response matches the HealthResponse interface from @envoy/shared-contracts.
//
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    server: 'envoy-mock-express',
    sdk_initialized: true,
  });
});

// ─── Endpoint 2: Product Branding ─────────────────────────────────────────────
//
// GET /api/v1/products/:productId
//
// The widget calls this endpoint on startup to fetch branding configuration.
// The BrandingStore in the widget reads the response and applies colors,
// fonts, layout, and feature flags dynamically.
//
// This mock returns realistic branding data for known product IDs.
// In production, this would query your database.
//
app.get('/api/v1/products/:productId', async (req, res) => {
  const { productId } = req.params;

  res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
  res.setHeader('Pragma', 'no-cache');
  res.setHeader('Expires', '0');

  // Try to fetch live branding metadata from the core backend via the SDK
  try {
    const client = sdk.getClient();
    const result = await client.getBranding(productId);
    if (result && result.success && result.data) {
      console.log(`[envoy-server] Successfully fetched live branding config for product "${productId}" from core backend.`);
      return res.json(result.data);
    }
  } catch (err) {
    console.warn(`[envoy-server] Could not fetch live branding for product "${productId}" from core backend: ${err.message}. Falling back to mock configuration.`);
  }

  // Mock branding configurations for each known product.
  // These match the ui_theme_config shape that BrandingStore.loadBranding() expects.
  const brandingMap = {
    tensor: {
      colors: {
        primaryColor:   '#2563EB',
        secondaryColor: '#475569',
        accentColor:    '#14B8A6',
        backgroundColor:'#f8fafc',
        surfaceColor:   '#ffffff',
        borderColor:    '#e2e8f0',
        textColor:      '#111827',
        mutedTextColor: '#64748b',
        successColor:   '#16a34a',
        warningColor:   '#d97706',
        errorColor:     '#dc2626',
        darkPrimaryColor: '#3b82f6',
        darkSecondaryColor: '#64748b',
        darkAccentColor: '#14b8a6',
        darkBackgroundColor: '#020617',
        darkSurfaceColor: '#0f172a',
        darkBorderColor: '#334155',
        darkTextColor: '#f8fafc',
        darkMutedTextColor: '#94a3b8',
      },
      typography: {
        fontFamily:      'Inter, system-ui, sans-serif',
        fontSize:        '14px',
        headingWeight:   600,
        bodyWeight:      400,
        messageTextSize: '13px',
        buttonTextSize:  '13px',
      },
      layout: {
        chatWidth:    '380px',
        chatHeight:   '520px',
        borderRadius: '12px',
        padding:      '16px',
        spacing:      '12px',
        bubbleRadius: '8px',
        position: {
          anchor: 'bottom-right',
          offsetX: 20,
          offsetY: 20
        }
      },
      assets: {
        companyLogo: '',
        chatAvatar:  '',
        botAvatar:   '',
        launcherIcon:'',
        headerIcon:  '',
      },
      content: {
        widgetTitle:         'Tensor Assistant',
        welcomeMessage:      'Ask Tensor Assistant about analytics, models, and reports.',
        placeholderText:     'Type your question...',
        offlineMessage:      'Tensor Assistant is currently offline.',
        errorMessage:        'Something went wrong. Please try again.',
        typingIndicatorText: 'Tensor is thinking...',
        subtitle:            'Online',
        onlineStatus:        'online',
        suggestedQuestions: [
          'Pricing',
          'Documentation',
          'Contact Support'
        ]
      },
      featureFlags: {
        fileUpload:          true,
        voiceInput:          false,
        suggestedQuestions:  true,
        typingAnimation:     true,
        streamingResponses:  true,
        conversationHistory: true,
      },
      overflowMenu: [
        { id: 'restart', label: 'Restart Conversation', enabled: true, actionType: 'restart' },
        { id: 'clear', label: 'Clear Chat', enabled: true, actionType: 'clear' },
        { id: 'download', label: 'Download Conversation', enabled: true, actionType: 'download' },
        { id: 'privacy', label: 'Privacy Policy', enabled: true, actionType: 'url', url: 'https://envoy.com/privacy' },
        { id: 'about', label: 'About Bot', enabled: true, actionType: 'callback', eventName: 'envoy-about-clicked' }
      ],
      theme: 'auto'
    },
    admissions: {
      colors: {
        primaryColor:   '#0F766E',
        secondaryColor: '#475569',
        accentColor:    '#F97316',
        backgroundColor:'#f8fafc',
        surfaceColor:   '#ffffff',
        borderColor:    '#e2e8f0',
        textColor:      '#111827',
        mutedTextColor: '#64748b',
        successColor:   '#16a34a',
        warningColor:   '#d97706',
        errorColor:     '#dc2626',
        darkPrimaryColor: '#0d9488',
        darkSecondaryColor: '#64748b',
        darkAccentColor: '#f97316',
        darkBackgroundColor: '#042f2e',
        darkSurfaceColor: '#115e59',
        darkBorderColor: '#14b8a6',
        darkTextColor: '#f0fdfa',
        darkMutedTextColor: '#99f6e4',
      },
      typography: {
        fontFamily:      'Inter, system-ui, sans-serif',
        fontSize:        '14px',
        headingWeight:   600,
        bodyWeight:      400,
        messageTextSize: '13px',
        buttonTextSize:  '13px',
      },
      layout: {
        chatWidth:    '380px',
        chatHeight:   '520px',
        borderRadius: '12px',
        padding:      '16px',
        spacing:      '12px',
        bubbleRadius: '8px',
        position: {
          anchor: 'bottom-left',
          offsetX: 30,
          offsetY: 30
        }
      },
      assets: { companyLogo: '', chatAvatar: '', botAvatar: '', launcherIcon: '', headerIcon: '' },
      content: {
        widgetTitle:         'Admissions Assistant',
        welcomeMessage:      'Ask about applications, eligibility, deadlines, and fee policies.',
        placeholderText:     'Ask about admissions...',
        offlineMessage:      'Admissions Assistant is currently offline.',
        errorMessage:        'Something went wrong. Please try again.',
        typingIndicatorText: 'Admissions is thinking...',
        subtitle:            'Admissions Desk',
        onlineStatus:        'online',
        suggestedQuestions: [
          'Admissions Requirements',
          'Tuition & Fees',
          'Application Deadline'
        ]
      },
      featureFlags: {
        fileUpload: false, voiceInput: false, suggestedQuestions: true,
        typingAnimation: true, streamingResponses: true, conversationHistory: true,
      },
      overflowMenu: [
        { id: 'restart', label: 'Start Over', enabled: true, actionType: 'restart' },
        { id: 'clear', label: 'Clear History', enabled: true, actionType: 'clear' },
        { id: 'download', label: 'Export Chat', enabled: true, actionType: 'download' },
        { id: 'privacy', label: 'Terms & Privacy', enabled: true, actionType: 'url', url: 'https://envoy.com/privacy' }
      ],
      theme: 'light'
    },
  };

  const branding = brandingMap[productId];

  if (!branding) {
    // Unknown product ID — return 404 matching the APIErrorResponse contract
    return res.status(404).json({
      success: false,
      error: {
        code: 'NOT_FOUND',
        message: `Product "${productId}" was not found.`,
        details: { productId },
        correlation_id: `req-${Date.now()}`,
        timestamp: new Date().toISOString(),
        retryable: false,
      },
    });
  }

  // Return the product record.
  // The widget's BrandingStore reads the ui_theme_config field.
  res.json({
    id:              productId,
    product_id:      productId,
    name:            branding.content.widgetTitle,
    ui_theme_config: branding,
    created_at:      '2025-01-01T00:00:00Z',
    updated_at:      new Date().toISOString(),
  });
});

// ─── Endpoint 3: Chat (JSON response) ─────────────────────────────────────────
//
// POST /api/v1/chat
//
// The widget sends user messages here. The SDK's requestMiddleware validates
// the payload before the route handler runs.
//
// Request body (ChatRequest from @envoy/shared-contracts):
//   { bot_id, conversation_id, prompt, stream, metadata? }
//
// Response body (ChatResponse from @envoy/shared-contracts):
//   { success, message: { id, conversation_id, sender, text, timestamp } }
//
// NOTE: The SDK's requestMiddleware is applied here. It validates that
// bot_id and prompt are present and non-empty strings. If validation fails,
// it responds with 400 before this handler runs.
//
app.post(
  '/api/v1/chat',
  middleware.requestMiddleware,   // ← SDK validates bot_id and prompt
  async (req, res, next) => {
    const { bot_id, conversation_id, prompt, stream } = req.body;

    console.log(`[envoy-server] Chat request forwarding to core backend — bot: ${bot_id}, prompt: "${prompt}"`);

    try {
      const client = sdk.getClient();
      const response = await client.queryChatbot(bot_id, prompt, false);
      res.status(200).json(response.data);
    } catch (err) {
      console.error('[envoy-server] Core backend query failed:', err.message);
      next(err);
    }
  }
);

// ─── Endpoint 4: Chat Stream (SSE) ────────────────────────────────────────────
//
// GET /api/v1/chat/stream?bot_id=...&prompt=...
//
// The widget calls this endpoint when streamingResponses feature flag is true.
// It uses the Fetch API with a ReadableStream reader to consume SSE chunks.
//
// Response format — Server-Sent Events (text/event-stream):
//   data: {"event":"text","text":"Hello"}
//   data: {"event":"text","text":" there"}
//   data: {"event":"done","message_id":"msg_123"}
//
// Each chunk matches the StreamingChunk union type from @envoy/shared-contracts.
//
app.get('/api/v1/chat/stream', async (req, res, next) => {
  const { bot_id, prompt } = req.query;

  if (!bot_id || !prompt) {
    return res.status(400).json({
      success: false,
      error: {
        code: 'BAD_REQUEST',
        message: 'Query parameters "bot_id" and "prompt" are required.',
        correlation_id: `req-${Date.now()}`,
        timestamp: new Date().toISOString(),
        retryable: false,
      },
    });
  }

  console.log(`[envoy-server] SSE stream forwarding to core backend — bot: ${bot_id}, prompt: "${prompt}"`);

  try {
    // Set SSE headers — these tell the browser to keep the connection open
    // and treat each line as a server-sent event
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('X-Accel-Buffering', 'no'); // Disable nginx buffering if behind a proxy
    res.flushHeaders();

    const client = sdk.getClient();
    const responseStream = await client.queryChatbot(String(bot_id), String(prompt), true);

    responseStream.on('data', (chunk) => {
      res.write(chunk);
    });

    responseStream.on('end', () => {
      res.end();
    });

    responseStream.on('error', (err) => {
      console.error('[envoy-server] Core backend stream error:', err);
      res.write(`data: ${JSON.stringify({ event: 'error', error: err.message })}\n\n`);
      res.end();
    });

    req.on('close', () => {
      if (responseStream.destroy) {
        responseStream.destroy();
      }
    });

  } catch (err) {
    console.error('[envoy-server] Core backend stream connection failed:', err.message);
    res.write(`data: ${JSON.stringify({ event: 'error', error: err.message })}\n\n`);
    res.end();
  }
});

// ─── Error handler ────────────────────────────────────────────────────────────
//
// Catches errors thrown by SDK middleware (e.g. UnauthorizedProxyRequest)
// and returns a clean JSON error response.
//
app.use((err, req, res, _next) => {
  console.error('[envoy-server] Unhandled error:', err.message);
  res.status(500).json({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: err.message || 'An unexpected error occurred.',
      correlation_id: `req-${Date.now()}`,
      timestamp: new Date().toISOString(),
      retryable: false,
    },
  });
});

// ─── Start the server ─────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log('');
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║         Envoy Mock Express Server — Running              ║');
  console.log('╠══════════════════════════════════════════════════════════╣');
  console.log(`║  Demo website:   http://localhost:${PORT}                    ║`);
  console.log(`║  Health check:   http://localhost:${PORT}/health              ║`);
  console.log(`║  Branding API:   GET  /api/v1/products/:productId        ║`);
  console.log(`║  Chat API:       POST /api/v1/chat                       ║`);
  console.log(`║  Stream API:     GET  /api/v1/chat/stream                ║`);
  console.log('╠══════════════════════════════════════════════════════════╣');
  console.log(`║  SDK target:     ${CHATBOT_API_BASE.padEnd(38)}║`);
  console.log(`║  Product ID:     ${CHATBOT_PRODUCT_ID.padEnd(38)}║`);
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');
});

// ─── Helper: Mock response generator ─────────────────────────────────────────
//
// Returns a realistic mock response based on keywords in the user's prompt.
// In production, this logic is replaced by the SDK's proxyMiddleware which
// forwards the request to the real core backend.
//
function getMockResponse(prompt) {
  const q = prompt.toLowerCase();

  if (q.includes('hello') || q.includes('hi') || q.includes('hey')) {
    return 'Hello! I am the Envoy AI assistant. I can help you with analytics, reports, and platform configuration. What would you like to know?';
  }
  if (q.includes('branding') || q.includes('color') || q.includes('theme')) {
    return 'You can customize the widget\'s colors, fonts, and layout through the Branding configuration panel in the admin dashboard. Changes are applied dynamically at runtime without redeploying the widget.';
  }
  if (q.includes('sync') || q.includes('knowledge') || q.includes('document')) {
    return 'To synchronize the knowledge base, navigate to the Knowledge Metrics section in your dashboard and click "Synchronize Brain". The system will re-index all pending documents and update the vector store.';
  }
  if (q.includes('sdk') || q.includes('install') || q.includes('integrate')) {
    return 'To integrate the Backend SDK, install @envoy/chatbot-backend-sdk, call createChatbotSDK() with your credentials, and register the middleware on your chat route. See the installation guide in ai-mock-integration/docs/installation.md for step-by-step instructions.';
  }
  if (q.includes('stream') || q.includes('sse') || q.includes('real-time')) {
    return 'Streaming responses use Server-Sent Events (SSE). The widget connects to GET /api/v1/chat/stream and reads token chunks as they arrive. Enable the streamingResponses feature flag in your branding configuration to activate this mode.';
  }
  if (q.includes('error') || q.includes('problem') || q.includes('issue')) {
    return 'For troubleshooting, check the browser console for widget events, the server console for SDK logs, and the Network tab for API responses. The troubleshooting guide at ai-mock-integration/docs/troubleshooting.md covers the most common issues.';
  }

  return `Thank you for your question about "${prompt}". The Envoy AI platform is designed to provide intelligent, context-aware responses from your indexed knowledge base. In this mock environment, responses are simulated. Connect to the core backend to receive real AI-generated answers.`;
}
