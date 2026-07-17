// packages/chatbot-ui/src/components/ChatInput.ts

import { type BrandingConfig } from '../types';

export class ChatInput {
  private element: HTMLFormElement;
  private textareaEl!: HTMLTextAreaElement;
  private sendBtnEl!: HTMLButtonElement;
  private uploadBtnEl!: HTMLButtonElement;
  private voiceBtnEl!: HTMLButtonElement;
  private isStreaming: boolean = false;
  private isDisabled: boolean = false;
  private primaryColor: string = '#2563eb';

  constructor(
    private parentContainer: HTMLElement,
    private callbacks: {
      onSend: (text: string) => void;
      onStop: () => void;
      onUploadClick?: () => void;
      onVoiceClick?: () => void;
    }
  ) {
    this.element = document.createElement('form');
    this.element.id = 'envoy-input-form';
    this.element.className = 'p-3 border-t border-lt-border dark:border-dk-border bg-white dark:bg-dk-surface flex gap-2 items-end select-none';
    this.parentContainer.appendChild(this.element);

    this.render();
  }

  private render() {
    this.element.innerHTML = `
      <!-- Upload Attachment Button (Mock) -->
      <button type="button" id="envoy-upload-btn" class="p-2.5 rounded-xl text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300" aria-label="Upload File">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
        </svg>
      </button>
      
      <!-- Textarea input -->
      <textarea id="envoy-input" placeholder="Type a message..." rows="1" class="flex-1 px-3.5 py-2.5 bg-lt-bg dark:bg-dk-bg text-lt-text dark:text-dk-text border border-lt-border dark:border-dk-border rounded-xl resize-none outline-none focus:ring-2 focus:ring-primary focus:border-primary max-h-[140px] text-xs transition-all leading-relaxed" aria-label="Chat input field"></textarea>
      
      <!-- Voice Input Button (Mock) -->
      <button type="button" id="envoy-voice-btn" class="hidden p-2.5 rounded-xl text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-slate-300" aria-label="Voice input microphone">
        <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" y1="19" x2="12" y2="22"></line>
        </svg>
      </button>

      <!-- Submit / Stop Button -->
      <button type="submit" id="envoy-send-btn" class="p-2.5 rounded-xl flex items-center justify-center text-white cursor-pointer hover:opacity-90 active:scale-95 transition-all focus:outline-none focus:ring-2 focus:ring-offset-2" aria-label="Send Message">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    `;

    // Bind elements
    this.textareaEl = this.element.querySelector('#envoy-input') as HTMLTextAreaElement;
    this.sendBtnEl = this.element.querySelector('#envoy-send-btn') as HTMLButtonElement;
    this.uploadBtnEl = this.element.querySelector('#envoy-upload-btn') as HTMLButtonElement;
    this.voiceBtnEl = this.element.querySelector('#envoy-voice-btn') as HTMLButtonElement;

    // Setup input listeners
    this.element.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });

    this.textareaEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.handleSubmit();
      }
    });

    this.textareaEl.addEventListener('input', () => {
      this.autoGrow();
    });

    // Dummy placeholders triggers
    this.uploadBtnEl.addEventListener('click', () => {
      if (this.callbacks.onUploadClick) {
        this.callbacks.onUploadClick();
      } else {
        alert('File upload placeholder: integrating local PDFs and text files is supported.');
      }
    });

    this.voiceBtnEl.addEventListener('click', () => {
      if (this.callbacks.onVoiceClick) {
        this.callbacks.onVoiceClick();
      } else {
        alert('Microphone input placeholder: speak to transcribe prompts.');
      }
    });
  }

  private handleSubmit() {
    if (this.isStreaming) {
      this.callbacks.onStop();
      return;
    }

    if (this.isDisabled) return;

    const text = this.textareaEl.value.trim();
    if (text) {
      this.callbacks.onSend(text);
      this.textareaEl.value = '';
      this.autoGrow();
    }
  }

  private autoGrow() {
    this.textareaEl.style.height = 'auto';
    this.textareaEl.style.height = `${Math.min(this.textareaEl.scrollHeight, 140)}px`;
  }

  public setStreaming(isStreaming: boolean) {
    this.isStreaming = isStreaming;
    
    if (isStreaming) {
      // Replace Send with Stop Generation (square icon, maybe red/accent)
      this.sendBtnEl.setAttribute('aria-label', 'Stop Generation');
      this.sendBtnEl.style.backgroundColor = '#ef4444'; // Red-500 for Stop
      this.sendBtnEl.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor" class="animate-pulse">
          <rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect>
        </svg>
      `;
      // Ensure it is clickable
      this.sendBtnEl.disabled = false;
      this.sendBtnEl.classList.remove('opacity-60', 'cursor-not-allowed');
      
      // Let's keep textarea enabled during streaming so they can type the next question if they want,
      // or disabled as the project initially had. We'll follow "Do not completely disable the input area" concept
      // but let's disable typing while streaming if we want to mimic standard AI chatbot style.
      // Wait, let's keep input disabled during connecting but during streaming the user can click Stop.
      this.textareaEl.disabled = true;
      this.textareaEl.classList.add('opacity-60', 'cursor-not-allowed');
    } else {
      // Revert to Send
      this.sendBtnEl.setAttribute('aria-label', 'Send Message');
      this.sendBtnEl.style.backgroundColor = this.primaryColor;
      this.sendBtnEl.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      `;
      
      this.textareaEl.disabled = this.isDisabled;
      if (this.isDisabled) {
        this.textareaEl.classList.add('opacity-60', 'cursor-not-allowed');
      } else {
        this.textareaEl.classList.remove('opacity-60', 'cursor-not-allowed');
        // If not working and not streaming, focus on textarea
        this.textareaEl.focus();
      }
    }
  }

  public setDisabled(isDisabled: boolean) {
    this.isDisabled = isDisabled;
    this.textareaEl.disabled = isDisabled;
    this.sendBtnEl.disabled = isDisabled;

    if (isDisabled) {
      this.textareaEl.classList.add('opacity-60', 'cursor-not-allowed');
      this.sendBtnEl.classList.add('opacity-60', 'cursor-not-allowed');
      if (!this.isStreaming) {
        // Show spinner icon on sendBtnEl if working (not streaming)
        this.sendBtnEl.innerHTML = `
          <svg class="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        `;
      }
    } else {
      this.textareaEl.classList.remove('opacity-60', 'cursor-not-allowed');
      this.sendBtnEl.classList.remove('opacity-60', 'cursor-not-allowed');
      this.setStreaming(this.isStreaming);
    }
  }

  public updateBranding(branding: BrandingConfig) {
    this.primaryColor = branding.colors.primaryColor || '#2563eb';
    if (!this.isStreaming) {
      this.sendBtnEl.style.backgroundColor = this.primaryColor;
    }

    const placeholder = branding.content.placeholderText || 'Type a message...';
    this.textareaEl.setAttribute('placeholder', placeholder);

    // Toggle attachment buttons based on flags
    if (branding.featureFlags.fileUpload) {
      this.uploadBtnEl.classList.remove('hidden');
    } else {
      this.uploadBtnEl.classList.add('hidden');
    }

    if (branding.featureFlags.voiceInput) {
      this.voiceBtnEl.classList.remove('hidden');
    } else {
      this.voiceBtnEl.classList.add('hidden');
    }
  }

  public focus() {
    this.textareaEl.focus();
  }

  public getElement() { return this.element; }
}
