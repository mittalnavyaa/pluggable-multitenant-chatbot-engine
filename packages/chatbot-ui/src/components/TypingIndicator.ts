// packages/chatbot-ui/src/components/TypingIndicator.ts

import { type BrandingConfig } from '../types';

export class TypingIndicator {
  private element: HTMLDivElement;

  constructor(private parentContainer: HTMLElement) {
    this.element = document.createElement('div');
    this.element.id = 'envoy-typing';
    this.element.className = 'hidden px-4 py-2 text-xs text-lt-muted dark:text-dk-muted bg-lt-bg dark:bg-dk-bg flex items-center gap-1.5 border-t border-lt-border/30 dark:border-dk-border/30 select-none';
    this.parentContainer.appendChild(this.element);

    this.render();
  }

  private render() {
    this.element.setAttribute('role', 'status');
    this.element.setAttribute('aria-live', 'polite');
    this.element.setAttribute('aria-label', 'Agent is typing');

    this.element.innerHTML = `
      <span class="flex gap-1.5 items-center">
        <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 0ms"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 150ms"></span>
        <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 300ms"></span>
      </span>
      <span id="envoy-typing-text">Agent is typing...</span>
    `;
  }

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

  public hide() {
    this.element.classList.add('hidden');
    this.element.setAttribute('aria-hidden', 'true');
  }

  public updateTheme(branding: BrandingConfig) {
    const textEl = this.element.querySelector('#envoy-typing-text');
    if (textEl) {
      textEl.textContent = branding.content.typingIndicatorText || 'Agent is typing...';
    }
  }

  public getElement() { return this.element; }
}
