// packages/chatbot-ui/src/components/Header.ts

import { type BrandingConfig } from '../types';

export class Header {
  private element: HTMLElement;
  private titleEl!: HTMLSpanElement;
  private subtitleEl!: HTMLSpanElement;
  private statusDotEl!: HTMLSpanElement;
  private restartBtnEl!: HTMLButtonElement;
  private overflowBtnEl!: HTMLButtonElement;
  private closeBtnEl!: HTMLButtonElement;

  constructor(
    private parentContainer: HTMLElement,
    private callbacks: {
      onCloseClick: () => void;
      onRestartClick: () => void;
      onOverflowToggle: (e: MouseEvent) => void;
    }
  ) {
    this.element = document.createElement('header');
    this.element.id = 'envoy-header';
    this.element.className = 'px-4 py-3 flex items-center justify-between text-white shadow-md select-none relative z-10';
    this.parentContainer.appendChild(this.element);

    this.render();
  }

  private render() {
    this.element.innerHTML = `
      <div class="flex items-center gap-2.5 min-w-0">
        <!-- Avatar Wrapper -->
        <div class="relative flex-shrink-0" id="envoy-avatar-container">
          <div id="envoy-header-avatar" class="w-9 h-9 rounded-full flex items-center justify-center text-xs font-semibold bg-white/20 text-white border border-white/10 overflow-hidden shadow-sm">
            AI
          </div>
          <!-- Status dot overlay -->
          <span id="envoy-status-dot" class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-primary transition-all duration-300"></span>
        </div>
        
        <!-- Info Text -->
        <div class="flex flex-col min-w-0 leading-tight">
          <span id="envoy-title" class="font-semibold truncate text-sm">Assistant</span>
          <span id="envoy-subtitle" class="text-[10px] text-white/80 opacity-90 truncate">Online</span>
        </div>
      </div>

      <!-- Header Controls -->
      <div class="flex items-center gap-1">
        <button type="button" id="envoy-reset-btn" class="p-1.5 rounded-lg hover:bg-white/10 text-white cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-white/20" title="Restart conversation">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M23 4v6h-6M1 20v-6h6"></path>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
          </svg>
        </button>
        <button type="button" id="envoy-overflow-btn" class="p-1.5 rounded-lg hover:bg-white/10 text-white cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-white/20" title="More options" aria-haspopup="true">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <circle cx="12" cy="12" r="1.5"></circle>
            <circle cx="12" cy="5" r="1.5"></circle>
            <circle cx="12" cy="19" r="1.5"></circle>
          </svg>
        </button>
        <button type="button" id="envoy-close-btn" class="p-1.5 rounded-lg hover:bg-white/10 text-white cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-white/20" aria-label="Close Chat Window">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>
    `;

    // Bind refs
    this.titleEl = this.element.querySelector('#envoy-title') as HTMLSpanElement;
    this.subtitleEl = this.element.querySelector('#envoy-subtitle') as HTMLSpanElement;
    this.statusDotEl = this.element.querySelector('#envoy-status-dot') as HTMLSpanElement;
    this.restartBtnEl = this.element.querySelector('#envoy-reset-btn') as HTMLButtonElement;
    this.overflowBtnEl = this.element.querySelector('#envoy-overflow-btn') as HTMLButtonElement;
    this.closeBtnEl = this.element.querySelector('#envoy-close-btn') as HTMLButtonElement;

    // Bind listeners
    this.closeBtnEl.addEventListener('click', () => this.callbacks.onCloseClick());
    this.restartBtnEl.addEventListener('click', () => this.callbacks.onRestartClick());
    this.overflowBtnEl.addEventListener('click', (e) => this.callbacks.onOverflowToggle(e));
  }

  public updateBranding(branding: BrandingConfig) {
    this.element.style.backgroundColor = branding.colors.primaryColor || '#2563eb';
    this.titleEl.textContent = branding.content.widgetTitle || 'Envoy AI Agent';
    
    // Status dot color adjustments
    if (branding.content.onlineStatus === 'offline' || branding.content.onlineStatus === false) {
      this.statusDotEl.className = 'absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-slate-400 border-2 border-white/20 transition-all duration-300';
      this.statusDotEl.setAttribute('title', 'Offline');
      this.subtitleEl.textContent = branding.content.offlineMessage || 'Offline';
    } else {
      this.statusDotEl.className = 'absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-green-400 border-2 border-white/20 transition-all duration-300 animate-pulse';
      this.statusDotEl.setAttribute('title', 'Online');
      this.subtitleEl.textContent = branding.content.subtitle || 'Online';
    }

    // Apply custom avatar
    const avatarEl = this.element.querySelector('#envoy-header-avatar') as HTMLDivElement;
    if (avatarEl) {
      const avatarUrl = branding.assets.botAvatar || branding.assets.chatAvatar || branding.assets.companyLogo;
      if (avatarUrl && avatarUrl.trim()) {
        avatarEl.innerHTML = `<img src="${avatarUrl}" alt="${branding.content.widgetTitle}" class="w-full h-full object-cover" />`;
      } else {
        const initials = (branding.content.widgetTitle || 'AI')
          .split(' ')
          .map(w => w[0])
          .join('')
          .substring(0, 2)
          .toUpperCase();
        avatarEl.textContent = initials;
      }
    }
  }

  public getStatusDot() { return this.statusDotEl; }
}
