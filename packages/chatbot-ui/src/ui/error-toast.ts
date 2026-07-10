// packages/chatbot-ui/src/ui/error-toast.ts

import { type BrandingConfig } from '../types';

export type ErrorType =
  | 'network'
  | 'timeout'
  | 'unavailable'
  | 'auth'
  | 'interrupted'
  | 'unexpected';

export class ErrorToastController {
  private currentToast: HTMLDivElement | null = null;
  private dismissTimeout: number | null = null;

  constructor(
    private readonly container: HTMLDivElement,
    private readonly getBranding: () => BrandingConfig
  ) {}

  /**
   * Translates internal error codes to user-friendly text messages without exposing technical stack traces.
   */
  private getFriendlyMessage(type: ErrorType): string {
    const customError = this.getBranding().content.errorMessage;
    if (customError && type === 'unexpected') {
      return customError;
    }

    switch (type) {
      case 'network':
        return 'Network connection lost. Please check your internet connection and try again.';
      case 'timeout':
        return 'Connection timed out. The server is taking too long to respond.';
      case 'unavailable':
        return 'Chat service is currently unavailable. Please try again later.';
      case 'auth':
        return 'Failed to authenticate your session. Please try reloading the page.';
      case 'interrupted':
        return 'The connection was interrupted. Please try again.';
      case 'unexpected':
      default:
        return 'An unexpected error occurred. Please try sending your message again.';
    }
  }

  /**
   * Displays a non-blocking, accessible error toast with optionally defined action.
   */
  public show(type: ErrorType, onRetry?: () => void, autoDismissMs: number = 8000) {
    this.dismiss();

    const message = this.getFriendlyMessage(type);
    const toast = document.createElement('div');
    toast.className = 'envoy-error-toast flex items-start gap-2.5 p-3 rounded-lg border text-xs shadow-md pointer-events-auto transition-all duration-300 opacity-100 translate-y-0';
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');

    const isRecoverable = type !== 'auth';

    toast.innerHTML = `
      <svg class="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
      <div class="flex-1 flex flex-col gap-1">
        <span class="font-medium">${message}</span>
        <div class="flex items-center gap-2 mt-1">
          ${isRecoverable && onRetry ? `<button type="button" class="envoy-toast-retry-btn px-2 py-0.5 rounded font-semibold cursor-pointer focus:outline-none focus:ring-1 focus:ring-offset-1 transition-colors">Retry</button>` : ''}
          <button type="button" class="envoy-toast-dismiss-btn px-2 py-0.5 rounded border font-semibold cursor-pointer focus:outline-none focus:ring-1 focus:ring-offset-1 transition-colors">Dismiss</button>
        </div>
      </div>
    `;

    this.container.appendChild(toast);
    this.currentToast = toast;

    // Hook listeners
    if (isRecoverable && onRetry) {
      const retryBtn = toast.querySelector('.envoy-toast-retry-btn') as HTMLButtonElement;
      if (retryBtn) {
        retryBtn.addEventListener('click', () => {
          this.dismiss();
          onRetry();
        });
      }
    }

    const dismissBtn = toast.querySelector('.envoy-toast-dismiss-btn') as HTMLButtonElement;
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        this.dismiss();
      });
    }

    // Set auto dismiss timeout
    if (autoDismissMs > 0) {
      this.dismissTimeout = window.setTimeout(() => {
        this.dismiss();
      }, autoDismissMs);
    }
  }

  /**
   * Dismiss the currently active toast.
   */
  public dismiss() {
    if (this.dismissTimeout) {
      clearTimeout(this.dismissTimeout);
      this.dismissTimeout = null;
    }

    if (this.currentToast) {
      const toast = this.currentToast;
      this.currentToast = null;
      
      toast.classList.remove('opacity-100', 'translate-y-0');
      toast.classList.add('opacity-0', '-translate-y-2');
      
      setTimeout(() => {
        if (toast.parentNode === this.container) {
          this.container.removeChild(toast);
        }
      }, 300);
    }
  }
}
