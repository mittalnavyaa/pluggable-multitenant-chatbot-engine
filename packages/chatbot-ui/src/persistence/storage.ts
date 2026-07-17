// packages/chatbot-ui/src/persistence/storage.ts

import { type Message } from '../types';

export interface ConversationStorage {
  saveConversation(botId: string, messages: Message[], conversationId: string): void;
  loadConversation(botId: string): { messages: Message[]; conversationId: string } | null;
  clearConversation(botId: string): void;
}

export class LocalStorageConversationStorage implements ConversationStorage {
  public saveConversation(botId: string, messages: Message[], conversationId: string): void {
    try {
      localStorage.setItem(`envoy-chat-history-${botId}`, JSON.stringify(messages));
      localStorage.setItem(`envoy-chat-conv-id-${botId}`, conversationId);
    } catch (err) {
      console.warn('[envoy-storage] Failed saving conversation to localStorage:', err);
    }
  }

  public loadConversation(botId: string): { messages: Message[]; conversationId: string } | null {
    try {
      const historyStr = localStorage.getItem(`envoy-chat-history-${botId}`);
      const convId = localStorage.getItem(`envoy-chat-conv-id-${botId}`);
      if (historyStr && convId) {
        const messages = JSON.parse(historyStr);
        if (Array.isArray(messages)) {
          return { messages, conversationId: convId };
        }
      }
    } catch (err) {
      console.warn('[envoy-storage] Failed loading conversation from localStorage:', err);
    }
    return null;
  }

  public clearConversation(botId: string): void {
    try {
      localStorage.removeItem(`envoy-chat-history-${botId}`);
      localStorage.removeItem(`envoy-chat-conv-id-${botId}`);
    } catch (err) {
      console.warn('[envoy-storage] Failed clearing conversation from localStorage:', err);
    }
  }
}
