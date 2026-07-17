// packages/chatbot-ui/src/components/OverflowMenu.ts

import { type OverflowMenuItemConfig } from '../branding/branding-types';

export class OverflowMenu {
  private element: HTMLDivElement;
  private isOpen: boolean = false;

  constructor(
    private parentContainer: HTMLElement,
    private onItemClick: (item: OverflowMenuItemConfig) => void
  ) {
    this.element = document.createElement('div');
    this.element.id = 'envoy-overflow-menu';
    this.element.className = 'hidden absolute top-[48px] right-2 bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border shadow-xl rounded-lg py-1.5 w-48 z-[99999] transition-all duration-200 transform scale-95 opacity-0 origin-top-right';
    this.parentContainer.appendChild(this.element);

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (this.isOpen) {
        const path = e.composedPath();
        const clickedInsideMenu = path.includes(this.element);
        const clickedOnButton = path.some(el => (el as HTMLElement).id === 'envoy-overflow-btn');
        if (!clickedInsideMenu && !clickedOnButton) {
          this.close();
        }
      }
    });
  }

  public setConfig(items: OverflowMenuItemConfig[]) {
    this.element.innerHTML = '';
    const enabledItems = items.filter(item => item.enabled !== false);
    
    if (enabledItems.length === 0) {
      this.element.innerHTML = '<div class="px-3 py-1.5 text-xs text-lt-muted dark:text-dk-muted">No options available</div>';
      return;
    }

    enabledItems.forEach(item => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'w-full text-left px-4 py-2.5 text-xs text-lt-text dark:text-dk-text hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors flex items-center gap-2 cursor-pointer focus:outline-none focus:bg-slate-50 dark:focus:bg-slate-800';

      // Add icons based on common types to look extremely premium!
      const icon = this.getIconForAction(item.actionType, item.id);
      btn.innerHTML = `${icon}<span>${item.label}</span>`;

      btn.addEventListener('click', () => {
        this.onItemClick(item);
        this.close();
      });

      this.element.appendChild(btn);
    });
  }

  private getIconForAction(actionType: string, id: string): string {
    const cleanId = id.toLowerCase();
    if (actionType === 'restart' || cleanId.includes('restart')) {
      return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="opacity-70"><path d="M23 4v6h-6M1 20v-6h6"></path><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>`;
    }
    if (actionType === 'clear' || cleanId.includes('clear')) {
      return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="opacity-70"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`;
    }
    if (actionType === 'download' || cleanId.includes('download')) {
      return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="opacity-70"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;
    }
    if (actionType === 'url' || cleanId.includes('policy') || cleanId.includes('privacy') || cleanId.includes('about')) {
      return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="opacity-70"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`;
    }
    // Default info icon
    return `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="opacity-70"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;
  }

  public toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  public open() {
    this.isOpen = true;
    this.element.classList.remove('hidden', 'scale-95', 'opacity-0');
    this.element.classList.add('scale-100', 'opacity-100');
  }

  public close() {
    this.isOpen = false;
    this.element.classList.remove('scale-100', 'opacity-100');
    this.element.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
      if (!this.isOpen) this.element.classList.add('hidden');
    }, 200);
  }

  public getElement() { return this.element; }
}
