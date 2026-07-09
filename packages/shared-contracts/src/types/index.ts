// packages/shared-contracts/src/types/index.ts

/**
 * 1. Widget Initialization Contract
 */
export interface WidgetInitRequest {
  bot_id: string;
}

export interface WidgetBrandingConfig {
  colors: {
    primaryColor: string;
    secondaryColor: string;
    accentColor: string;
    backgroundColor: string;
    surfaceColor: string;
    borderColor: string;
    textColor: string;
    successColor: string;
    warningColor: string;
    dangerColor: string;
  };
  layout: {
    chatWidth: string;
    chatHeight: string;
    borderRadius: string;
  };
  assets: {
    avatarUrl: string;
    logoUrl: string;
  };
  content: {
    welcomeMessage: string;
    placeholderText: string;
  };
  featureFlags: {
    fileUpload: boolean;
    voiceInput: boolean;
    suggestedQuestions: boolean;
    conversationHistory: boolean;
    typingAnimation: boolean;
    streamingResponses: boolean;
  };
}

export interface WidgetInitResponse {
  success: boolean;
  branding: WidgetBrandingConfig;
}

/**
 * 2. Send Chat Message Contract
 */
export interface ChatRequest {
  bot_id: string;
  conversation_id: string;
  prompt: string;
  stream: boolean;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
}

export interface ChatResponse {
  success: boolean;
  message: ChatMessage;
}

/**
 * 3. Streaming Response Chunks
 */
export interface StreamingTextChunk {
  event: 'text';
  text: string;
}

export interface StreamingDoneChunk {
  event: 'done';
  message_id: string;
}

export interface StreamingErrorChunk {
  event: 'error';
  error: string;
}

export type StreamingChunk = StreamingTextChunk | StreamingDoneChunk | StreamingErrorChunk;

/**
 * 4. System Health Check Contract
 */
export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
}

/**
 * 5. Standard System Error Contract
 */
export interface APIErrorBlock {
  code: string;
  message: string;
  details?: any;
  correlation_id: string;
  timestamp: string;
  retryable: boolean;
}

export interface APIErrorResponse {
  success: false;
  error: APIErrorBlock;
}
