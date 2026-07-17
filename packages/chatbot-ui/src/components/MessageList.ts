// packages/chatbot-ui/src/components/MessageList.ts

import { type Message } from '../types';
import { MessageBubble } from './MessageBubble';

export class MessageList {
  private element: HTMLDivElement;

  constructor(private parentContainer: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'envoy-messages';
    this.element.className = 'flex-1 p-4 overflow-y-auto bg-lt-bg dark:bg-dk-bg flex flex-col gap-4.5 envoy-messages-container scroll-smooth';
    this.parentContainer.appendChild(this.element);
  }

  public clear() {
    this.element.innerHTML = '';
  }

  public appendMessage(
    msg: Message,
    primaryColor: string,
    onAction: (action: 'copy' | 'regenerate' | 'thumbs-up' | 'thumbs-down', messageId: string) => void
  ): MessageBubble {
    const bubble = new MessageBubble(this.element, msg, primaryColor, onAction);
    return bubble;
  }

  public getElement() { return this.element; }
}
