// packages/chatbot-ui/src/ui/typing-indicator.ts

import { type BrandingConfig } from '../types';

export class TypingIndicator {
  constructor(private readonly element: HTMLDivElement) {
    this.setupAccessibility();
  }

  private setupAccessibility() {
    this.element.setAttribute('role', 'status');
    this.element.setAttribute('aria-live', 'polite');
    this.element.setAttribute('aria-label', 'Agent is typing');
  }

  /**
   * Display the typing animation.
   */
  public show(text?: string) {
    if (text) {
      const textEl = this.element.querySelector('#envoy-typing-text');
      if (textEl) {
        textEl.textContent = text;
      }
    }
    this.element.classList.remove('hidden');
    this.element.setAttribute('aria-hidden', 'false');
  }

  /**
   * Hide the typing animation.
   */
  public hide() {
    this.element.classList.add('hidden');
    this.element.setAttribute('aria-hidden', 'true');
  }

  /**
   * Update theme-aware branding content dynamically.
   */
  public updateTheme(branding: BrandingConfig) {
    const textEl = this.element.querySelector('#envoy-typing-text');
    if (textEl) {
      textEl.textContent = branding.content.typingIndicatorText || 'Agent is typing...';
    }
  }
}
