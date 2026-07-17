// packages/chatbot-ui/src/components/ChatWindow.ts

import { type BrandingConfig } from '../types';

export class ChatWindow {
  private element: HTMLDivElement;

  constructor(private parentContainer: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'envoy-chat-window';
    // Starts collapsed/hidden
    this.element.className = 'envoy-chat-window-collapsed absolute flex flex-col overflow-hidden bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border shadow-2xl transition-all duration-300 transform scale-95 opacity-0 pointer-events-none z-[99999]';
    this.parentContainer.appendChild(this.element);
  }

  public updateLayout(branding: BrandingConfig) {
    this.element.style.width = branding.layout.chatWidth || '380px';
    this.element.style.height = branding.layout.chatHeight || '520px';
    this.element.style.borderRadius = branding.layout.borderRadius || '12px';

    const anchor = branding.layout.position?.anchor || 'bottom-right';
    
    // Clear alignment styles
    this.element.style.top = '';
    this.element.style.bottom = '';
    this.element.style.left = '';
    this.element.style.right = '';

    // Position window relative to launcher depending on the anchor
    if (anchor === 'bottom-right') {
      this.element.style.bottom = '76px';
      this.element.style.right = '0';
    } else if (anchor === 'bottom-left') {
      this.element.style.bottom = '76px';
      this.element.style.left = '0';
    } else if (anchor === 'top-right') {
      this.element.style.top = '76px';
      this.element.style.right = '0';
    } else if (anchor === 'top-left') {
      this.element.style.top = '76px';
      this.element.style.left = '0';
    }
  }

  public setOpen(isOpen: boolean) {
    if (isOpen) {
      this.element.classList.remove('envoy-chat-window-collapsed', 'scale-95', 'opacity-0', 'pointer-events-none');
      this.element.classList.add('envoy-chat-window-expanded', 'scale-100', 'opacity-100');
    } else {
      this.element.classList.remove('envoy-chat-window-expanded', 'scale-100', 'opacity-100');
      this.element.classList.add('envoy-chat-window-collapsed', 'scale-95', 'opacity-0', 'pointer-events-none');
    }
  }

  public getElement() { return this.element; }
}
