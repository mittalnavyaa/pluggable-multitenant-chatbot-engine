// packages/chatbot-ui/src/ui/auto-scroll.ts

export class AutoScrollController {
  private isAutoScrollActive = true;
  private readonly threshold = 50; // pixels from bottom threshold
  private isProgrammaticScroll = false;

  constructor(private readonly container: HTMLDivElement) {
    this.container.addEventListener('scroll', this.handleScroll.bind(this));
  }

  private handleScroll() {
    if (this.isProgrammaticScroll) {
      this.isProgrammaticScroll = false;
      return;
    }

    const { scrollTop, scrollHeight, clientHeight } = this.container;
    const atBottom = scrollHeight - scrollTop - clientHeight <= this.threshold;

    this.isAutoScrollActive = atBottom;
  }

  /**
   * Scrolls smoothly to the bottom if the user is at the bottom.
   */
  public scroll() {
    if (!this.isAutoScrollActive) return;

    this.isProgrammaticScroll = true;
    this.container.scrollTo({
      top: this.container.scrollHeight,
      behavior: 'smooth'
    });
  }

  /**
   * Force scrolls to the bottom and resumes auto-scroll tracking.
   */
  public forceScroll() {
    this.isAutoScrollActive = true;
    this.isProgrammaticScroll = true;
    this.container.scrollTo({
      top: this.container.scrollHeight,
      behavior: 'smooth'
    });
  }
}
