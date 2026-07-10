// packages/chatbot-ui/src/ui/loading-state.ts

import { type ConversationState } from '../types';

export class LoadingStateController {
  private originalSendBtnContent: string = '';

  constructor(
    private readonly inputEl: HTMLTextAreaElement,
    private readonly sendBtnEl: HTMLButtonElement,
    private readonly statusDotEl: HTMLSpanElement | null
  ) {
    if (this.sendBtnEl) {
      this.originalSendBtnContent = this.sendBtnEl.innerHTML;
    }
  }

  /**
   * Synchronizes visual loading cues, form disable states, and title status indicator.
   */
  public updateState(state: ConversationState) {
    const isWorking = [
      'sending',
      'connecting',
      'waiting',
      'typing',
      'streaming',
      'reconnecting'
    ].includes(state);

    // Update Input Textarea
    if (this.inputEl) {
      this.inputEl.disabled = isWorking;
      if (isWorking) {
        this.inputEl.classList.add('opacity-60', 'cursor-not-allowed');
      } else {
        this.inputEl.classList.remove('opacity-60', 'cursor-not-allowed');
      }
    }

    // Update Send Button
    if (this.sendBtnEl) {
      this.sendBtnEl.disabled = isWorking;
      if (isWorking) {
        this.sendBtnEl.classList.add('opacity-60', 'cursor-not-allowed');
        // Render a small CSS spinner inside the send button
        this.sendBtnEl.innerHTML = `
          <svg class="animate-spin h-4.5 w-4.5 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        `;
      } else {
        this.sendBtnEl.classList.remove('opacity-60', 'cursor-not-allowed');
        this.sendBtnEl.innerHTML = this.originalSendBtnContent;
      }
    }

    // Update Status Indicator Dot
    if (this.statusDotEl) {
      // Reset classes
      this.statusDotEl.className = 'w-2.5 h-2.5 rounded-full transition-all duration-300';
      
      switch (state) {
        case 'connecting':
        case 'reconnecting':
        case 'sending':
          this.statusDotEl.classList.add('bg-amber-400', 'animate-pulse');
          this.statusDotEl.setAttribute('title', 'Connecting...');
          break;
        case 'waiting':
        case 'typing':
        case 'streaming':
          this.statusDotEl.classList.add('bg-blue-400', 'animate-pulse');
          this.statusDotEl.setAttribute('title', 'Responding...');
          break;
        case 'failed':
          this.statusDotEl.classList.add('bg-red-500');
          this.statusDotEl.setAttribute('title', 'Connection error');
          break;
        case 'idle':
        case 'completed':
        case 'cancelled':
        default:
          this.statusDotEl.classList.add('bg-green-400', 'animate-pulse');
          this.statusDotEl.setAttribute('title', 'Online');
          break;
      }
    }
  }
}
