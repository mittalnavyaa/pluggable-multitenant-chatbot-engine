// packages/chatbot-ui/src/components/MessageBubble.ts

import { type Message } from '../types';
import { MarkdownRenderer } from '../streaming/markdown-renderer';

export class MessageBubble {
  private wrapperEl: HTMLDivElement;
  private bubbleEl!: HTMLDivElement;
  private thumbsUpBtn?: HTMLButtonElement;
  private thumbsDownBtn?: HTMLButtonElement;
  private ratingState: 'none' | 'up' | 'down' = 'none';

  constructor(
    private parentContainer: HTMLElement,
    private msg: Message,
    private primaryColor: string,
    private onAction: (action: 'copy' | 'regenerate' | 'thumbs-up' | 'thumbs-down', messageId: string) => void
  ) {
    this.wrapperEl = document.createElement('div');
    const isBot = msg.sender === 'bot';
    
    // Bubble wrapper row alignment and animation
    this.wrapperEl.className = `flex w-full select-text animate-fade-in-up ${
      isBot ? 'justify-start relative group' : 'justify-end'
    }`;
    
    this.render();
    this.parentContainer.appendChild(this.wrapperEl);
  }

  private render() {
    const isBot = this.msg.sender === 'bot';

    if (isBot) {
      // Assistant Bubble with hover toolbar
      this.wrapperEl.innerHTML = `
        <div id="msg-${this.msg.id}" class="max-w-[85%] px-4 py-3 rounded-2xl rounded-tl-none text-xs leading-relaxed text-lt-text dark:text-dk-text bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border shadow-sm transition-all duration-200">
          ${MarkdownRenderer.render(this.msg.text)}
        </div>
        
        <!-- Hover actions toolbar -->
        <div class="absolute -top-3 right-4 bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border rounded-lg shadow-md px-1.5 py-1 flex items-center gap-1 opacity-0 pointer-events-none transition-all duration-200 group-hover:opacity-100 group-hover:pointer-events-auto z-10">
          <button type="button" id="btn-copy-${this.msg.id}" class="p-1 rounded text-lt-muted dark:text-dk-muted hover:text-lt-text dark:hover:text-dk-text hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors focus:outline-none" title="Copy to clipboard">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
          <button type="button" id="btn-regen-${this.msg.id}" class="p-1 rounded text-lt-muted dark:text-dk-muted hover:text-lt-text dark:hover:text-dk-text hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors focus:outline-none" title="Regenerate response">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M23 4v6h-6M1 20v-6h6"></path>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
          <button type="button" id="btn-up-${this.msg.id}" class="p-1 rounded text-lt-muted dark:text-dk-muted hover:text-lt-text dark:hover:text-dk-text hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors focus:outline-none" title="Thumbs up">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
            </svg>
          </button>
          <button type="button" id="btn-down-${this.msg.id}" class="p-1 rounded text-lt-muted dark:text-dk-muted hover:text-lt-text dark:hover:text-dk-text hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors focus:outline-none" title="Thumbs down">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm12-5h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>
            </svg>
          </button>
        </div>
      `;

      this.bubbleEl = this.wrapperEl.querySelector(`#msg-${this.msg.id}`) as HTMLDivElement;
      
      if (this.msg.isStreaming) {
        this.bubbleEl.classList.add('envoy-streaming');
      }

      // Bind buttons
      const copyBtn = this.wrapperEl.querySelector(`#btn-copy-${this.msg.id}`) as HTMLButtonElement;
      const regenBtn = this.wrapperEl.querySelector(`#btn-regen-${this.msg.id}`) as HTMLButtonElement;
      this.thumbsUpBtn = this.wrapperEl.querySelector(`#btn-up-${this.msg.id}`) as HTMLButtonElement;
      this.thumbsDownBtn = this.wrapperEl.querySelector(`#btn-down-${this.msg.id}`) as HTMLButtonElement;

      copyBtn.addEventListener('click', () => {
        this.onAction('copy', this.msg.id);
        // Visual indicator of copy success
        const origHtml = copyBtn.innerHTML;
        copyBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="green" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
        setTimeout(() => { copyBtn.innerHTML = origHtml; }, 1500);
      });

      regenBtn.addEventListener('click', () => this.onAction('regenerate', this.msg.id));
      
      this.thumbsUpBtn.addEventListener('click', () => {
        this.toggleRating('up');
        this.onAction('thumbs-up', this.msg.id);
      });

      this.thumbsDownBtn.addEventListener('click', () => {
        this.toggleRating('down');
        this.onAction('thumbs-down', this.msg.id);
      });

    } else {
      // User Bubble
      this.wrapperEl.innerHTML = `
        <div id="msg-${this.msg.id}" class="max-w-[85%] px-4 py-3 rounded-2xl rounded-tr-none text-xs leading-relaxed text-white shadow-sm font-medium">
          ${MarkdownRenderer.escapeHtml(this.msg.text)}
        </div>
      `;
      this.bubbleEl = this.wrapperEl.querySelector(`#msg-${this.msg.id}`) as HTMLDivElement;
      this.bubbleEl.style.backgroundColor = this.primaryColor;
    }
  }

  private toggleRating(rating: 'up' | 'down') {
    if (!this.thumbsUpBtn || !this.thumbsDownBtn) return;

    if (rating === 'up') {
      if (this.ratingState === 'up') {
        this.ratingState = 'none';
        this.thumbsUpBtn.classList.remove('text-green-500', 'dark:text-green-400');
      } else {
        this.ratingState = 'up';
        this.thumbsUpBtn.classList.add('text-green-500', 'dark:text-green-400');
        this.thumbsDownBtn.classList.remove('text-red-500', 'dark:text-red-400');
      }
    } else {
      if (this.ratingState === 'down') {
        this.ratingState = 'none';
        this.thumbsDownBtn.classList.remove('text-red-500', 'dark:text-red-400');
      } else {
        this.ratingState = 'down';
        this.thumbsDownBtn.classList.add('text-red-500', 'dark:text-red-400');
        this.thumbsUpBtn.classList.remove('text-green-500', 'dark:text-green-400');
      }
    }
  }

  public updateText(text: string) {
    this.msg.text = text;
    if (this.msg.sender === 'bot') {
      this.bubbleEl.innerHTML = MarkdownRenderer.render(text);
    } else {
      this.bubbleEl.textContent = text;
    }
  }

  public setStreaming(isStreaming: boolean) {
    this.msg.isStreaming = isStreaming;
    if (isStreaming) {
      this.bubbleEl.classList.add('envoy-streaming');
    } else {
      this.bubbleEl.classList.remove('envoy-streaming');
    }
  }

  public getElement() { return this.wrapperEl; }
  public getMessage() { return this.msg; }
}
