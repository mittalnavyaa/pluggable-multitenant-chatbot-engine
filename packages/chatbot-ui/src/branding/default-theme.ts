// packages/chatbot-ui/src/branding/default-theme.ts

import { type BrandingConfig } from './branding-types';

export const DEFAULT_ENVOY_THEME: BrandingConfig = {
  colors: {
    primaryColor: '#2563eb',     // Tailwind blue-600
    secondaryColor: '#475569',   // Tailwind slate-600
    accentColor: '#10b981',      // Tailwind emerald-500
    backgroundColor: '#f8fafc',  // Tailwind slate-50 (light mode bg)
    surfaceColor: '#ffffff',     // white
    borderColor: '#e2e8f0',      // Tailwind slate-200
    textColor: '#0f172a',        // Tailwind slate-900
    mutedTextColor: '#64748b',   // Tailwind slate-500
    successColor: '#16a34a',     // green-600
    warningColor: '#d97706',     // amber-600
    errorColor: '#dc2626',       // red-600
  },
  typography: {
    fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    fontSize: '14px',
    headingWeight: 600,
    bodyWeight: 400,
    messageTextSize: '13px',
    buttonTextSize: '13px',
  },
  layout: {
    chatWidth: '380px',
    chatHeight: '520px',
    borderRadius: '12px',
    padding: '16px',
    spacing: '12px',
    bubbleRadius: '8px',
  },
  assets: {
    companyLogo: '',
    chatAvatar: '',
    botAvatar: '',
    launcherIcon: '',
    headerIcon: '',
  },
  content: {
    widgetTitle: 'Envoy Support Assistant',
    welcomeMessage: 'Hello! I am your Envoy AI helper. How can I assist you today?',
    placeholderText: 'Type a message...',
    offlineMessage: 'We are currently offline. Please check back later.',
    errorMessage: 'Something went wrong. Please try sending your message again.',
    typingIndicatorText: 'Agent is typing...',
  },
  featureFlags: {
    fileUpload: true,
    voiceInput: false,
    suggestedQuestions: true,
    typingAnimation: true,
    streamingResponses: true,
    conversationHistory: true,
  }
};
