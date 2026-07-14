import re

class ChatFallbackService:
    """Service class containing offline/development fallback rules."""

    @classmethod
    def generate_response_text(cls, prompt: str, context: str) -> str:
        """Keyword-based fallback response for development and testing."""
        q = prompt.lower()
        words = set(re.findall(r'\b\w+\b', q))
        
        if context and context.strip():
            return f"Based on the retrieved knowledge documents: {context[:500]}... If you need more details, please let me know."
        
        if words & {"hello", "hi", "hey"}:
            return "Hello! I am the Envoy AI assistant. I can help you with analytics, reports, and platform configuration. What would you like to know?"
        if words & {"branding", "color", "theme"}:
            return "You can customize the widget's colors, fonts, and layout through the Branding configuration panel in the admin dashboard. Changes are applied dynamically at runtime."
        if words & {"sync", "knowledge", "document"}:
            return "To synchronize the knowledge base, navigate to the Knowledge Metrics section and click 'Synchronize Brain'. The system will re-index all pending documents."
        if words & {"sdk", "install", "integrate"}:
            return "To integrate the Backend SDK, install @envoy/chatbot-backend-sdk, call createChatbotSDK() with your credentials, and register the middleware on your chat route."
        if words & {"stream", "sse"}:
            return "Streaming responses use Server-Sent Events (SSE). The widget connects to GET /api/v1/chat/stream and reads token chunks as they arrive."
            
        return f'Thank you for your question about "{prompt}". The Envoy AI platform provides intelligent, context-aware responses from your indexed knowledge base. How can I assist you further?'
