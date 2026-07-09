// packages/chatbot-ui/src/types.ts

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
}

export interface BrandingConfig {
  primaryColor?: string;
  accentColor?: string;
  widgetTitle?: string;
  launcherLabel?: string;
  welcomeMessage?: string;
  logoUrl?: string;
  borderRadius?: string;
  fontFamily?: string;
}

export type WidgetState = 'idle' | 'loading' | 'connected' | 'error';
