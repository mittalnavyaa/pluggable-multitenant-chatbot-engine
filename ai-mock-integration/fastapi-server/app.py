"""
ai-mock-integration/fastapi-server/app.py

Mock FastAPI server demonstrating the same integration pattern as the
Express server, for teams whose host application is built in Python.

─────────────────────────────────────────────────────────────────────────────
WHAT THIS SERVER DOES
─────────────────────────────────────────────────────────────────────────────
1. Loads environment variables from .env
2. Provides mock endpoints with the same response shapes as the Express server
3. Demonstrates how a Python host application would sit between the widget
   and the core backend

NOTE: The @envoy/chatbot-backend-sdk is a Node.js package. Python host
applications implement the same proxy pattern directly using the documented
API contracts from @envoy/shared-contracts. The HMAC signing logic is
reproduced here in Python using the same algorithm.

ENDPOINTS PROVIDED
─────────────────────────────────────────────────────────────────────────────
  GET  /health                            → Health check
  GET  /api/v1/products/{product_id}      → Mock branding response
  POST /api/v1/chat                       → Mock JSON chat response
  GET  /api/v1/chat/stream                → Mock SSE streaming response
─────────────────────────────────────────────────────────────────────────────
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# ─── Step 1: Load environment variables ──────────────────────────────────────
#
# python-dotenv reads the .env file in this directory.
# Copy .env.example to .env and fill in your values before starting.
#
load_dotenv()

PORT                   = int(os.getenv("PORT", "8001"))
CHATBOT_API_KEY        = os.getenv("CHATBOT_API_KEY", "")
CHATBOT_PRODUCT_ID     = os.getenv("CHATBOT_PRODUCT_ID", "tensor")
CHATBOT_SIGNING_SECRET = os.getenv("CHATBOT_SIGNING_SECRET", "")
ENVIRONMENT            = os.getenv("ENVIRONMENT", "development")

# ─── Step 2: Create the FastAPI application ───────────────────────────────────

app = FastAPI(
    title="Envoy Mock FastAPI Server",
    description="Mock backend demonstrating Envoy chatbot widget integration for Python host applications.",
    version="1.0.0",
)

# ─── Step 3: CORS middleware ──────────────────────────────────────────────────
#
# Allow the widget (running in the browser) to make requests to this server.
# In production, replace allow_origins=["*"] with your actual frontend domain.
#
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "X-Envoy-Signature",
        "X-Envoy-Timestamp",
        "X-Envoy-Nonce",
        "X-Envoy-API-Key",
        "X-Envoy-Product-ID",
    ],
)

# ─── Step 4: Request/Response models ─────────────────────────────────────────
#
# These Pydantic models mirror the TypeScript interfaces in
# @envoy/shared-contracts/src/types/index.ts
#

class ChatRequest(BaseModel):
    """Matches the ChatRequest interface from @envoy/shared-contracts."""
    bot_id: str
    conversation_id: str
    prompt: str
    stream: bool = False
    metadata: Optional[dict] = None


class ChatMessage(BaseModel):
    """Matches the ChatMessage interface from @envoy/shared-contracts."""
    id: str
    conversation_id: str
    sender: str  # 'user' | 'bot'
    text: str
    timestamp: str


class ChatResponse(BaseModel):
    """Matches the ChatResponse interface from @envoy/shared-contracts."""
    success: bool
    message: ChatMessage


class HealthResponse(BaseModel):
    """Matches the HealthResponse interface from @envoy/shared-contracts."""
    status: str
    timestamp: str
    version: str
    server: str


# ─── Step 5: HMAC signing helper ─────────────────────────────────────────────
#
# This reproduces the same signing algorithm used by HMACSignatureProvider
# in packages/chatbot-backend-sdk/src/utils/crypto.ts.
#
# In a Python host application, you implement this directly rather than
# using the Node.js SDK package.
#
def sign_request(payload: str) -> dict:
    """
    Generates HMAC-SHA256 signature headers for a request payload.
    Matches the output of HMACSignatureProvider.sign() in the Node.js SDK.

    Returns a dict of headers to inject into the outgoing request.
    """
    timestamp = str(int(time.time() * 1000))  # Unix epoch milliseconds
    nonce = secrets.token_hex(16)              # 16-byte random hex string

    # Canonical message: timestamp.nonce.payload
    # This matches the computeSignature() method in crypto.ts
    message = f"{timestamp}.{nonce}.{payload}"

    signature = hmac.new(
        CHATBOT_SIGNING_SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return {
        "X-Envoy-Signature":  signature,
        "X-Envoy-Timestamp":  timestamp,
        "X-Envoy-Nonce":      nonce,
        "X-Envoy-API-Key":    CHATBOT_API_KEY,
        "X-Envoy-Product-ID": CHATBOT_PRODUCT_ID,
    }


# ─── Step 6: Mock branding data ──────────────────────────────────────────────
#
# In production, this would be fetched from your database.
# The structure matches the ui_theme_config field that BrandingStore.loadBranding()
# expects in the widget.
#
MOCK_BRANDING = {
    "tensor": {
        "colors": {
            "primaryColor":    "#2563EB",
            "secondaryColor":  "#475569",
            "accentColor":     "#14B8A6",
            "backgroundColor": "#f8fafc",
            "surfaceColor":    "#ffffff",
            "borderColor":     "#e2e8f0",
            "textColor":       "#111827",
            "mutedTextColor":  "#64748b",
            "successColor":    "#16a34a",
            "warningColor":    "#d97706",
            "errorColor":      "#dc2626",
        },
        "typography": {
            "fontFamily":      "Inter, system-ui, sans-serif",
            "fontSize":        "14px",
            "headingWeight":   600,
            "bodyWeight":      400,
            "messageTextSize": "13px",
            "buttonTextSize":  "13px",
        },
        "layout": {
            "chatWidth":    "380px",
            "chatHeight":   "520px",
            "borderRadius": "12px",
            "padding":      "16px",
            "spacing":      "12px",
            "bubbleRadius": "8px",
        },
        "assets": {
            "companyLogo": "",
            "chatAvatar":  "",
            "botAvatar":   "",
            "launcherIcon": "",
            "headerIcon":  "",
        },
        "content": {
            "widgetTitle":         "Tensor Assistant",
            "welcomeMessage":      "Ask Tensor Assistant about analytics, models, and reports.",
            "placeholderText":     "Type your question...",
            "offlineMessage":      "Tensor Assistant is currently offline.",
            "errorMessage":        "Something went wrong. Please try again.",
            "typingIndicatorText": "Tensor is thinking...",
        },
        "featureFlags": {
            "fileUpload":          True,
            "voiceInput":          False,
            "suggestedQuestions":  True,
            "typingAnimation":     True,
            "streamingResponses":  True,
            "conversationHistory": True,
        },
    },
    "admissions": {
        "colors": {
            "primaryColor":    "#0F766E",
            "secondaryColor":  "#475569",
            "accentColor":     "#F97316",
            "backgroundColor": "#f8fafc",
            "surfaceColor":    "#ffffff",
            "borderColor":     "#e2e8f0",
            "textColor":       "#111827",
            "mutedTextColor":  "#64748b",
            "successColor":    "#16a34a",
            "warningColor":    "#d97706",
            "errorColor":      "#dc2626",
        },
        "typography": {
            "fontFamily":      "Inter, system-ui, sans-serif",
            "fontSize":        "14px",
            "headingWeight":   600,
            "bodyWeight":      400,
            "messageTextSize": "13px",
            "buttonTextSize":  "13px",
        },
        "layout": {
            "chatWidth":    "380px",
            "chatHeight":   "520px",
            "borderRadius": "12px",
            "padding":      "16px",
            "spacing":      "12px",
            "bubbleRadius": "8px",
        },
        "assets": {
            "companyLogo": "", "chatAvatar": "", "botAvatar": "",
            "launcherIcon": "", "headerIcon": "",
        },
        "content": {
            "widgetTitle":         "Admissions Assistant",
            "welcomeMessage":      "Ask about applications, eligibility, deadlines, and fee policies.",
            "placeholderText":     "Ask about admissions...",
            "offlineMessage":      "Admissions Assistant is currently offline.",
            "errorMessage":        "Something went wrong. Please try again.",
            "typingIndicatorText": "Admissions is thinking...",
        },
        "featureFlags": {
            "fileUpload": False, "voiceInput": False, "suggestedQuestions": True,
            "typingAnimation": True, "streamingResponses": True, "conversationHistory": True,
        },
    },
}


# ─── Endpoint 1: Health Check ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Returns server health status.
    Matches the HealthResponse interface from @envoy/shared-contracts.
    """
    return {
        "status":    "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version":   "1.0.0",
        "server":    "envoy-mock-fastapi",
    }


# ─── Endpoint 2: Product Branding ─────────────────────────────────────────────

@app.get("/api/v1/products/{product_id}")
def get_product(product_id: str):
    """
    Returns branding configuration for a product.
    The widget's BrandingStore calls this endpoint on startup.

    The response shape matches what BrandingStore.loadBranding() expects:
    the ui_theme_config field contains the full branding object.
    """
    branding = MOCK_BRANDING.get(product_id)

    if not branding:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code":           "NOT_FOUND",
                    "message":        f'Product "{product_id}" was not found.',
                    "details":        {"productId": product_id},
                    "correlation_id": f"req-{int(time.time() * 1000)}",
                    "timestamp":      datetime.now(timezone.utc).isoformat(),
                    "retryable":      False,
                },
            },
        )

    return {
        "id":              product_id,
        "product_id":      product_id,
        "name":            branding["content"]["widgetTitle"],
        "ui_theme_config": branding,
        "created_at":      "2025-01-01T00:00:00Z",
        "updated_at":      datetime.now(timezone.utc).isoformat(),
    }


# ─── Endpoint 3: Chat (JSON response) ─────────────────────────────────────────

@app.post("/api/v1/chat")
def chat(payload: ChatRequest):
    """
    Accepts a chat message and returns a bot response.

    Request body matches ChatRequest from @envoy/shared-contracts.
    Response body matches ChatResponse from @envoy/shared-contracts.

    In production, this method would:
    1. Validate the payload (done automatically by Pydantic)
    2. Sign the request using sign_request()
    3. Forward to the core backend
    4. Return the response
    """
    print(f"[envoy-fastapi] Chat request — bot: {payload.bot_id}, prompt: \"{payload.prompt}\"")

    # Generate a mock response
    response_text = get_mock_response(payload.prompt)

    # Return a ChatResponse matching the shared-contracts interface
    return {
        "success": True,
        "message": {
            "id":              f"msg_{int(time.time() * 1000)}",
            "conversation_id": payload.conversation_id,
            "sender":          "bot",
            "text":            response_text,
            "timestamp":       datetime.now(timezone.utc).isoformat(),
        },
    }


# ─── Endpoint 4: Chat Stream (SSE) ────────────────────────────────────────────

@app.get("/api/v1/chat/stream")
def chat_stream(
    bot_id: str = Query(..., description="The product/bot ID"),
    prompt: str = Query(..., description="The user's message"),
):
    """
    Streams a bot response as Server-Sent Events.
    The widget calls this when streamingResponses feature flag is true.

    Each chunk matches the StreamingChunk union type from @envoy/shared-contracts:
      StreamingTextChunk: { "event": "text", "text": "..." }
      StreamingDoneChunk: { "event": "done", "message_id": "..." }
      StreamingErrorChunk: { "event": "error", "error": "..." }
    """
    print(f"[envoy-fastapi] SSE stream — bot: {bot_id}, prompt: \"{prompt}\"")

    full_text = get_mock_response(prompt)
    message_id = f"msg_{int(time.time() * 1000)}"

    def event_generator():
        """
        Generator function that yields SSE-formatted chunks.
        Each yield sends one character of the response to simulate
        token-by-token LLM streaming.
        """
        # Stream each character as a text chunk
        for char in full_text:
            chunk = json.dumps({"event": "text", "text": char})
            yield f"data: {chunk}\n\n"

        # Send the completion event
        done_chunk = json.dumps({"event": "done", "message_id": message_id})
        yield f"data: {done_chunk}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "Connection":       "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Helper: Mock response generator ─────────────────────────────────────────

def get_mock_response(prompt: str) -> str:
    """
    Returns a realistic mock response based on keywords in the user's prompt.
    In production, this is replaced by a real call to the core backend.
    """
    q = prompt.lower()

    if any(word in q for word in ["hello", "hi", "hey"]):
        return "Hello! I am the Envoy AI assistant. I can help you with analytics, reports, and platform configuration. What would you like to know?"

    if any(word in q for word in ["branding", "color", "theme"]):
        return "You can customize the widget's colors, fonts, and layout through the Branding configuration panel in the admin dashboard. Changes are applied dynamically at runtime."

    if any(word in q for word in ["sync", "knowledge", "document"]):
        return "To synchronize the knowledge base, navigate to the Knowledge Metrics section and click 'Synchronize Brain'. The system will re-index all pending documents."

    if any(word in q for word in ["sdk", "install", "integrate"]):
        return "To integrate the Backend SDK, install @envoy/chatbot-backend-sdk, call createChatbotSDK() with your credentials, and register the middleware on your chat route."

    if any(word in q for word in ["stream", "sse", "real-time"]):
        return "Streaming responses use Server-Sent Events (SSE). The widget connects to GET /api/v1/chat/stream and reads token chunks as they arrive."

    return f'Thank you for your question about "{prompt}". The Envoy AI platform provides intelligent, context-aware responses from your indexed knowledge base. Connect to the core backend to receive real AI-generated answers.'


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         Envoy Mock FastAPI Server — Running              ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  API docs:       http://localhost:{PORT}/docs                 ║")
    print(f"║  Health check:   http://localhost:{PORT}/health               ║")
    print(f"║  Branding API:   GET  /api/v1/products/{{product_id}}     ║")
    print(f"║  Chat API:       POST /api/v1/chat                       ║")
    print(f"║  Stream API:     GET  /api/v1/chat/stream                ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Product ID:     {CHATBOT_PRODUCT_ID:<38}║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("")

    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=True)
