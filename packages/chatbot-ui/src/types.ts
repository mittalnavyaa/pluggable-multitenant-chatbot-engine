// packages/chatbot-ui/src/types.ts


export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
}

export * from './branding/branding-types';

export type WidgetState = 'idle' | 'loading' | 'connected' | 'error';

