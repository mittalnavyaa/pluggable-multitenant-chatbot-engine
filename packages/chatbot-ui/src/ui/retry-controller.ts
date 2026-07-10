// packages/chatbot-ui/src/ui/retry-controller.ts

export class RetryController {
  private lastPrompt: string | null = null;

  /**
   * Caches the last user message text that was sent.
   */
  public saveLastPrompt(prompt: string) {
    this.lastPrompt = prompt;
  }

  /**
   * Retrieves the cached last user prompt.
   */
  public getLastPrompt(): string | null {
    return this.lastPrompt;
  }

  /**
   * Clears the cached last prompt.
   */
  public clear() {
    this.lastPrompt = null;
  }
}
