// packages/chatbot-ui/src/streaming/stream-types.ts

export type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'completed' | 'failed';

export interface SSEClientOptions {
  apiBase: string;
  botId: string;
  prompt: string;
  headers?: Record<string, string>;
  maxRetries?: number;      // Default: 3
  retryInterval?: number;   // In ms, default: 1000
  onStatusChange?: (status: StreamStatus, error?: string) => void;
  onToken?: (token: string) => void;
  onComplete?: (messageId: string) => void;
  onError?: (error: string) => void;
}
