// packages/chatbot-ui/src/components/Launcher.ts

export class Launcher {
  private element: HTMLButtonElement;
  private primaryColor: string = '#2563eb';
  private launcherIcon?: string;
  private isOpen: boolean = false;

  constructor(
    private parentContainer: HTMLElement,
    private onClick: () => void
  ) {
    this.element = document.createElement('button');
    this.element.type = 'button';
    this.element.id = 'envoy-launcher';
    this.element.className = 'w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 hover:scale-105 active:scale-95 cursor-pointer text-white focus:outline-none focus:ring-4 focus:ring-blue-300';
    this.element.setAttribute('aria-label', 'Open Chatbot Window');
    this.element.addEventListener('click', () => this.onClick());
    this.parentContainer.appendChild(this.element);
    this.renderIcon();
  }

  public updateBranding(primaryColor: string, launcherIcon?: string) {
    this.primaryColor = primaryColor;
    this.launcherIcon = launcherIcon;
    this.element.style.backgroundColor = this.primaryColor;
    this.renderIcon();
  }

  public setOpenState(isOpen: boolean) {
    this.isOpen = isOpen;
    this.renderIcon();
  }

  private renderIcon() {
    if (this.isOpen) {
      this.element.innerHTML = `
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="animate-fade-in">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      `;
    } else {
      if (this.launcherIcon && this.launcherIcon.trim()) {
        if (this.launcherIcon.trim().startsWith('<svg')) {
          this.element.innerHTML = this.launcherIcon;
        } else {
          this.element.innerHTML = `<img src="${this.launcherIcon}" alt="Chat" class="w-8 h-8 rounded-full object-cover animate-fade-in" />`;
        }
      } else {
        this.element.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="animate-fade-in">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        `;
      }
    }
  }

  public getElement() { return this.element; }
}
