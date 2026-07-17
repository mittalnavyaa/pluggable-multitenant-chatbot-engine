// packages/chatbot-ui/src/index.ts

import stylesText from './styles.css?raw';
import { type Message, type BrandingConfig, type WidgetState } from './types';
import { brandingStore } from './branding/branding-store';
import { CSSVariableMapper } from './branding/css-variable-mapper';
import { DEFAULT_ENVOY_THEME } from './branding/default-theme';
import { SSEClient } from './streaming/sse-client';
import { MarkdownRenderer } from './streaming/markdown-renderer';

import { UIStateMachine } from './ui/ui-state-machine';
import { TypingIndicator } from './ui/typing-indicator';
import { ErrorToastController, type ErrorType } from './ui/error-toast';
import { AutoScrollController } from './ui/auto-scroll';
import { RetryController } from './ui/retry-controller';
import { LoadingStateController } from './ui/loading-state';

export class EnvoyChatbot extends HTMLElement {
  private isOpen: boolean = false;
  private messages: Message[] = [];
  private branding: BrandingConfig = { ...DEFAULT_ENVOY_THEME };
  private botId: string = '';
  private apiBase: string = '';
  private currentStreamInterval: number | null = null;
  private activeSseClient: SSEClient | null = null;
  private conversationId: string = '';

  // Interactive Response UI State Management properties
  private conversationStateMachine = new UIStateMachine();
  private typingIndicatorController!: TypingIndicator;
  private errorToastController!: ErrorToastController;
  private autoScrollController!: AutoScrollController;
  private retryController = new RetryController();
  private loadingStateController!: LoadingStateController;
  private notificationsContainerEl!: HTMLDivElement;

  // DOM Elements refs inside Shadow DOM
  private containerEl!: HTMLDivElement;
  private launcherEl!: HTMLButtonElement;
  private chatWindowEl!: HTMLDivElement;
  private messagesContainerEl!: HTMLDivElement;
  private inputEl!: HTMLTextAreaElement;
  private sendBtnEl!: HTMLButtonElement;
  private typingIndicatorEl!: HTMLDivElement;
  private suggestionsEl!: HTMLDivElement;
  private uploadBtnEl!: HTMLButtonElement;
  private voiceBtnEl!: HTMLButtonElement;

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }


  static get observedAttributes() {
    return ['data-bot-id', 'data-api-base'];
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    if (oldValue === newValue) return;
    if (name === 'data-bot-id') {
      this.botId = newValue;
      this.refreshBranding();
    } else if (name === 'data-api-base') {
      this.apiBase = newValue;
      this.refreshBranding();
    }
  }

  async connectedCallback() {
    this.botId = this.getAttribute('data-bot-id') || '';
    this.apiBase = this.getAttribute('data-api-base') || window.location.origin;

    // Build DOM structure
    this.renderStructure();

    // Initialize Interactive UI Controller systems
    this.notificationsContainerEl = this.shadowRoot!.getElementById('envoy-notifications') as HTMLDivElement;
    this.typingIndicatorController = new TypingIndicator(this.typingIndicatorEl);
    this.errorToastController = new ErrorToastController(
      this.notificationsContainerEl,
      () => this.branding
    );
    this.autoScrollController = new AutoScrollController(this.messagesContainerEl);

    const statusDot = this.shadowRoot!.getElementById('envoy-status-dot') as HTMLSpanElement;
    this.loadingStateController = new LoadingStateController(
      this.inputEl,
      this.sendBtnEl,
      statusDot
    );

    // Bind state machine listeners
    this.conversationStateMachine.addListener((state) => {
      this.loadingStateController.updateState(state);

      if (state === 'typing') {
        this.typingIndicatorController.show();
      } else {
        this.typingIndicatorController.hide();
      }
    });

    // Setup store listener
    brandingStore.addListener(this.onBrandingUpdate.bind(this));

    // Initial load
    this.refreshBranding();

    // Setup event listeners
    this.setupListeners();
  }


  disconnectedCallback() {
    this.cleanup();
  }

  // ------------------------------------------------------------------ #
  //  Public Javascript APIs                                             #
  // ------------------------------------------------------------------ #

  public open() {
    if (this.isOpen) return;
    this.isOpen = true;
    this.containerEl.classList.add('envoy-open');
    this.chatWindowEl.classList.remove('hidden');
    this.chatWindowEl.classList.add('flex');
    this.inputEl.focus();
    this.dispatchEvent(new CustomEvent('envoy-chat-opened', { bubbles: true, composed: true }));
  }

  public close() {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.containerEl.classList.remove('envoy-open');
    this.chatWindowEl.classList.add('hidden');
    this.chatWindowEl.classList.remove('flex');
    this.dispatchEvent(new CustomEvent('envoy-chat-closed', { bubbles: true, composed: true }));
  }

  public toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  public resetConversation() {
    this.messages = [];
    this.messagesContainerEl.innerHTML = '';
    
    if (this.branding.featureFlags.conversationHistory) {
      localStorage.removeItem(`envoy-chat-history-${this.botId}`);
      localStorage.removeItem(`envoy-chat-conv-id-${this.botId}`);
    }
    this.conversationId = '';

    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }

    this.addWelcomeMessage();
    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }
    
    this.conversationStateMachine.transition({ type: 'RESET' });
    this.retryController.clear();
    if (this.errorToastController) {
      this.errorToastController.dismiss();
    }
  }


  public async sendMessage(text: string, isRetry = false) {
    const currentState = this.conversationStateMachine.getState();
    const isWorking = ['sending', 'connecting', 'waiting', 'typing', 'streaming', 'reconnecting'].includes(currentState);
    if (!text.trim() || isWorking) return;
    
    // Clear any existing error toast when sending a message
    if (this.errorToastController) {
      this.errorToastController.dismiss();
    }

    if (!isRetry) {
      // Cache the prompt for potential future retries
      this.retryController.saveLastPrompt(text);

      // Append User Message
      const userMsg: Message = {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: text,
        timestamp: new Date().toISOString()
      };
      this.messages.push(userMsg);
      this.appendMessageDOM(userMsg);
      if (this.autoScrollController) {
        this.autoScrollController.forceScroll();
      }
    }

    // Save history if enabled
    if (this.branding.featureFlags.conversationHistory) {
      this.saveHistory();
    }

    // Hide suggestions once user has interacted
    this.suggestionsEl.classList.add('hidden');

    this.dispatchEvent(new CustomEvent('envoy-message-sent', { 
      detail: { text }, 
      bubbles: true, 
      composed: true 
    }));

    // Trigger state machine transition: SEND
    this.conversationStateMachine.transition({ type: 'SEND' });

    // Trigger responses
    await this.generateBotResponse(text, isRetry);
  }


  public destroy() {
    this.cleanup();
    this.remove();
  }

  // ------------------------------------------------------------------ #
  //  Internal Layout & Logic                                           #
  // ------------------------------------------------------------------ #

  private onBrandingUpdate(config: BrandingConfig, _state: WidgetState) {
    this.branding = config;

    this.applyTheme();
    this.applyFeatureFlags();
  }

  private async refreshBranding() {
    if (this.botId) {
      await brandingStore.loadBranding(this.botId, this.apiBase);
    }
  }

  private renderStructure() {
    const root = this.shadowRoot!;
    
    // Inject Styles text directly into Shadow DOM
    const style = document.createElement('style');
    style.textContent = stylesText;
    root.appendChild(style);

    // Host styling variables setup
    this.containerEl = document.createElement('div');
    this.containerEl.className = 'fixed bottom-5 right-5 z-[9999] font-sans text-sm select-none antialiased envoy-theme-font';
    this.containerEl.innerHTML = `
      <!-- Floating Launcher Button -->
      <button type="button" id="envoy-launcher" class="w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 hover:scale-105 active:scale-95 cursor-pointer text-white focus:outline-none focus:ring-4 focus:ring-blue-300" aria-label="Open Chatbot Window">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>

      <!-- Expandable Chat Window -->
      <div id="envoy-chat-window" class="hidden absolute bottom-16 right-0 flex-col overflow-hidden transition-all duration-200 bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border shadow-2xl">
        <!-- Header -->
        <header id="envoy-header" class="px-4 py-3 flex items-center justify-between text-white shadow-md">
          <div class="flex items-center gap-2">
            <span id="envoy-status-dot" class="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse"></span>
            <span id="envoy-title" class="font-semibold truncate max-w-[200px]">${this.branding.content.widgetTitle}</span>
          </div>
          <div class="flex items-center gap-1">
            <button type="button" id="envoy-reset-btn" class="p-1 rounded hover:bg-white/10 text-white cursor-pointer" title="Reset conversation">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M23 4v6h-6M1 20v-6h6"></path>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
            </button>
            <button type="button" id="envoy-close-btn" class="p-1 rounded hover:bg-white/10 text-white cursor-pointer" aria-label="Close Chat Window">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </header>

        <!-- Notification Toast Container -->
        <div id="envoy-notifications" class="absolute top-14 left-4 right-4 z-[1000] pointer-events-none flex flex-col gap-2"></div>

        <!-- Message Area -->

        <div id="envoy-messages" class="flex-1 p-4 overflow-y-auto bg-lt-bg dark:bg-dk-bg flex flex-col gap-3 envoy-messages-container">
          <!-- Dynamically populated -->
        </div>

        <!-- Suggested Questions / Quick Actions -->
        <div id="envoy-suggestions" class="hidden px-4 py-2 bg-lt-bg dark:bg-dk-bg flex flex-col gap-1.5 border-t border-lt-border/50 dark:border-dk-border/50">
          <!-- Dynamically populated suggestions -->
        </div>

        <!-- Typing Indicator -->
        <div id="envoy-typing" class="hidden px-4 py-1 text-xs text-lt-muted dark:text-dk-muted bg-lt-bg dark:bg-dk-bg flex items-center gap-1.5">
          <span class="flex gap-1 items-center">
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 300ms"></span>
          </span>
          <span id="envoy-typing-text">${this.branding.content.typingIndicatorText}</span>
        </div>

        <!-- Input Area -->
        <form id="envoy-input-form" class="p-3 border-t border-lt-border dark:border-dk-border bg-white dark:bg-dk-surface flex gap-1.5 items-center">
          <!-- Optional attachment button -->
          <button type="button" id="envoy-upload-btn" class="hidden p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500" aria-label="Upload File">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
            </svg>
          </button>
          
          <textarea id="envoy-input" placeholder="Type a message..." rows="1" class="flex-1 px-3 py-2 bg-lt-bg dark:bg-dk-bg text-lt-text dark:text-dk-text border border-lt-border dark:border-dk-border rounded-lg resize-none outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 max-h-[80px]" aria-label="Chat input field"></textarea>
          
          <!-- Optional voice input button -->
          <button type="button" id="envoy-voice-btn" class="hidden p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500" aria-label="Voice input microphone">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="22"></line>
            </svg>
          </button>

          <button type="submit" id="envoy-send-btn" class="p-2 rounded-lg flex items-center justify-center text-white cursor-pointer hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2" aria-label="Send Message">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </form>
      </div>
    `;

    root.appendChild(this.containerEl);

    // Bind element selectors
    this.launcherEl = root.getElementById('envoy-launcher') as HTMLButtonElement;
    this.chatWindowEl = root.getElementById('envoy-chat-window') as HTMLDivElement;
    this.messagesContainerEl = root.getElementById('envoy-messages') as HTMLDivElement;
    this.inputEl = root.getElementById('envoy-input') as HTMLTextAreaElement;
    this.sendBtnEl = root.getElementById('envoy-send-btn') as HTMLButtonElement;
    this.typingIndicatorEl = root.getElementById('envoy-typing') as HTMLDivElement;
    this.suggestionsEl = root.getElementById('envoy-suggestions') as HTMLDivElement;
    this.uploadBtnEl = root.getElementById('envoy-upload-btn') as HTMLButtonElement;
    this.voiceBtnEl = root.getElementById('envoy-voice-btn') as HTMLButtonElement;
  }

  private applyTheme() {
    const cssVars = CSSVariableMapper.mapToCSS(this.branding);
    for (const [key, value] of Object.entries(cssVars)) {
      this.style.setProperty(key, value);
    }

    // Set layout sizes on chat window container dynamically
    this.chatWindowEl.style.width = this.branding.layout.chatWidth || '380px';
    this.chatWindowEl.style.height = this.branding.layout.chatHeight || '520px';
    this.chatWindowEl.style.borderRadius = this.branding.layout.borderRadius || '12px';

    this.launcherEl.style.backgroundColor = this.branding.colors.primaryColor || '#2563eb';
    this.sendBtnEl.style.backgroundColor = this.branding.colors.primaryColor || '#2563eb';

    const header = this.shadowRoot!.getElementById('envoy-header');
    if (header) {
      header.style.backgroundColor = this.branding.colors.primaryColor || '#2563eb';
    }

    const titleEl = this.shadowRoot!.getElementById('envoy-title');
    if (titleEl) {
      titleEl.textContent = this.branding.content.widgetTitle || 'Envoy AI Agent';
    }

    const placeholder = this.branding.content.placeholderText || 'Type a message...';
    this.inputEl.setAttribute('placeholder', placeholder);

    const typingTextEl = this.shadowRoot!.getElementById('envoy-typing-text');
    if (typingTextEl) {
      typingTextEl.textContent = this.branding.content.typingIndicatorText || 'Agent is typing...';
    }
  }

  private applyFeatureFlags() {
    const flags = this.branding.featureFlags;

    // File Upload Flag toggle
    if (flags.fileUpload) {
      this.uploadBtnEl.classList.remove('hidden');
    } else {
      this.uploadBtnEl.classList.add('hidden');
    }

    // Voice Input Flag toggle
    if (flags.voiceInput) {
      this.voiceBtnEl.classList.remove('hidden');
    } else {
      this.voiceBtnEl.classList.add('hidden');
    }

    // Render/Hide Suggested questions
    if (flags.suggestedQuestions && this.messages.length <= 1) {
      this.renderSuggestions();
    } else {
      this.suggestionsEl.classList.add('hidden');
    }

    // Load History if enabled
    if (flags.conversationHistory && this.messages.length <= 1) {
      this.loadHistory();
    }
  }

  private renderSuggestions() {
    this.suggestionsEl.innerHTML = '';
    const prompts = [
      'How to sync chatbot brain?',
      'Can I change colors & branding?',
      'Tell me about file indexing'
    ];

    prompts.forEach(text => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'envoy-suggest-btn text-left px-3 py-1.5 rounded-lg border border-lt-border dark:border-dk-border bg-white dark:bg-dk-surface text-lt-text dark:text-dk-text text-xs hover:bg-slate-50 cursor-pointer transition-all border-l-4';
      btn.style.borderLeftColor = this.branding.colors.primaryColor || '#2563eb';
      btn.textContent = text;
      
      btn.addEventListener('click', () => {
        this.inputEl.value = text;
        this.sendMessage(text);
        this.inputEl.value = '';
      });

      this.suggestionsEl.appendChild(btn);
    });

    this.suggestionsEl.classList.remove('hidden');
  }

  private loadHistory() {
    try {
      const stored = localStorage.getItem(`envoy-chat-history-${this.botId}`);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          this.messages = parsed;
          this.messagesContainerEl.innerHTML = '';
          this.messages.forEach(msg => this.appendMessageDOM(msg));
          this.scrollToBottom();
          this.suggestionsEl.classList.add('hidden');
        }
      }
    } catch (err) {
      console.warn('[envoy-history] Failed loading chat history.', err);
    }
  }

  private saveHistory() {
    try {
      localStorage.setItem(`envoy-chat-history-${this.botId}`, JSON.stringify(this.messages));
    } catch (err) {
      console.warn('[envoy-history] Failed saving chat history.', err);
    }
  }

  private setupListeners() {
    // Toggle opened/closed window triggers
    this.launcherEl.addEventListener('click', () => this.toggle());
    
    const closeBtn = this.shadowRoot!.getElementById('envoy-close-btn');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    const resetBtn = this.shadowRoot!.getElementById('envoy-reset-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => this.resetConversation());
    }

    // Submit user forms input
    const form = this.shadowRoot!.getElementById('envoy-input-form');
    if (form) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = this.inputEl.value.trim();
        if (text) {
          this.sendMessage(text);
          this.inputEl.value = '';
        }
      });
    }

    // Enter submits message, shift+enter inserts newlines
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const text = this.inputEl.value.trim();
        if (text) {
          this.sendMessage(text);
          this.inputEl.value = '';
        }
      }
    });

    // File Upload Action click alert (Mock)
    this.uploadBtnEl.addEventListener('click', () => {
      alert('File upload initiated. Envoy chatbot supports indexing local PDFs and text files.');
    });

    // Voice Input Action click alert (Mock)
    this.voiceBtnEl.addEventListener('click', () => {
      alert('Microphone input activated. Speak to submit your prompt.');
    });
  }

  private addWelcomeMessage() {
    const welcomeMsg: Message = {
      id: 'welcome',
      sender: 'bot',
      text: this.branding.content.welcomeMessage || 'Hello! How can I help you today?',
      timestamp: new Date().toISOString()
    };
    this.messages.push(welcomeMsg);
    this.appendMessageDOM(welcomeMsg);
  }

  private appendMessageDOM(msg: Message) {
    const isBot = msg.sender === 'bot';
    
    // Create wrapper message bubble
    const bubble = document.createElement('div');
    bubble.className = `max-w-[80%] px-3 py-2 rounded-lg text-xs leading-relaxed break-words ${
      isBot 
        ? 'bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border text-lt-text dark:text-dk-text self-start rounded-bl-none shadow-sm'
        : 'text-white self-end rounded-br-none shadow-md'
    }`;
    
    if (!isBot) {
      bubble.style.backgroundColor = this.branding.colors.primaryColor || '#2563eb';
    }

    bubble.setAttribute('id', `msg-${msg.id}`);
    
    if (isBot) {
      bubble.innerHTML = MarkdownRenderer.render(msg.text);
      if (msg.isStreaming) {
        bubble.classList.add('envoy-streaming');
      }
    } else {
      bubble.textContent = msg.text;
    }
    
    // Append container
    this.messagesContainerEl.appendChild(bubble);
  }

  private mapErrorToType(errorMsg: string, streamSucceeded: boolean): ErrorType {
    if (streamSucceeded) {
      return 'interrupted';
    }
    const msg = errorMsg.toLowerCase();
    if (msg.includes('timeout') || msg.includes('time out')) {
      return 'timeout';
    }
    if (msg.includes('401') || msg.includes('403') || msg.includes('auth') || msg.includes('unauthorized')) {
      return 'auth';
    }
    if (msg.includes('502') || msg.includes('503') || msg.includes('504') || msg.includes('unavailable')) {
      return 'unavailable';
    }
    if (msg.includes('network') || msg.includes('fetch') || msg.includes('failed to fetch') || msg.includes('typeerror')) {
      return 'network';
    }
    return 'unexpected';
  }

  private async generateBotResponse(userPrompt: string, isRetry = false) {
    // Transition UI State: CONNECT (or RECONNECT if retrying from fail/reconnect)
    if (isRetry) {
      this.conversationStateMachine.transition({ type: 'RECONNECT' });
    } else {
      this.conversationStateMachine.transition({ type: 'CONNECT' });
    }

    // Disconnect any existing active client
    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }

    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }

    // Move to waiting / typing state
    this.conversationStateMachine.transition({ type: 'CONNECTED' });
    if (this.branding.featureFlags.typingAnimation) {
      this.conversationStateMachine.transition({ type: 'SHOW_TYPING' });
    }
    if (this.autoScrollController) {
      this.autoScrollController.scroll();
    }

    let streamSucceeded = false;

    if (this.branding.featureFlags.streamingResponses) {
      try {
        const botMsg: Message = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: '',
          timestamp: new Date().toISOString(),
          isStreaming: true
        };

        let bubbleAppended = false;
        let bubble: HTMLDivElement | null = null;

        this.activeSseClient = new SSEClient({
          apiBase: this.apiBase,
          botId: this.botId,
          prompt: userPrompt,
          onStatusChange: (status) => {
            if (status === 'streaming') {
              this.conversationStateMachine.transition({ type: 'RECEIVE_TOKEN' });
            } else if (status === 'completed') {
              this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });
              if (botMsg.isStreaming) {
                botMsg.isStreaming = false;
                if (bubble) {
                  bubble.classList.remove('envoy-streaming');
                }
              }
            }
          },
          onToken: (token) => {
            streamSucceeded = true;
            this.conversationStateMachine.transition({ type: 'RECEIVE_TOKEN' });

            if (!bubbleAppended) {
              bubbleAppended = true;
              this.messages.push(botMsg);
              this.appendMessageDOM(botMsg);
              bubble = this.shadowRoot!.getElementById(`msg-${botMsg.id}`) as HTMLDivElement;
            }
            botMsg.text += token;
            if (bubble) {
              bubble.innerHTML = MarkdownRenderer.render(botMsg.text);
            }
            if (this.autoScrollController) {
              this.autoScrollController.scroll();
            }
          },
          onComplete: () => {
            this.activeSseClient = null;
            this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });
            if (this.branding.featureFlags.conversationHistory) {
              this.saveHistory();
            }
            this.dispatchEvent(new CustomEvent('envoy-message-received', {
              detail: { text: botMsg.text },
              bubbles: true,
              composed: true
            }));
          },
          onError: (errorMsg) => {
            this.activeSseClient = null;
            console.error('[envoy-chatbot] SSE Streaming error:', errorMsg);

            // Transition UI state to failed
            this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: errorMsg });

            // Display non-blocking error toast with a retry trigger
            const errorType = this.mapErrorToType(errorMsg, streamSucceeded);
            this.errorToastController.show(errorType, () => {
              this.sendMessage(userPrompt, true);
            });

            // If some tokens were streamed, clean up stream indicator
            if (streamSucceeded && bubble) {
              botMsg.isStreaming = false;
              bubble.classList.remove('envoy-streaming');
            }
            if (this.autoScrollController) {
              this.autoScrollController.scroll();
            }
          }
        });

        await this.activeSseClient.connect();
        return;
      } catch (err: any) {
        console.warn('[envoy-chatbot] Failed establishing stream, falling back.', err);
        // Transition to failed state and show toast
        this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: err.message || 'Connection failed' });
        const errorType = this.mapErrorToType(err.message || '', false);
        this.errorToastController.show(errorType, () => {
          this.sendMessage(userPrompt, true);
        });
      }
    } else {
      try {
        const response = await fetch(`${this.apiBase}/api/v1/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            bot_id: this.botId,
            prompt: userPrompt,
            stream: false,
            conversation_id: this.getOrCreateConversationId()
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const responseData = await response.json();
        
        let responseText = '';
        if (responseData && responseData.success && responseData.message) {
          responseText = responseData.message.text;
        } else if (responseData && responseData.text) {
          responseText = responseData.text;
        } else {
          responseText = JSON.stringify(responseData);
        }

        const botMsg: Message = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: responseText,
          timestamp: new Date().toISOString(),
          isStreaming: false
        };

        this.messages.push(botMsg);
        this.appendMessageDOM(botMsg);
        if (this.autoScrollController) {
          this.autoScrollController.forceScroll();
        }
        this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });

        if (this.branding.featureFlags.conversationHistory) {
          this.saveHistory();
        }

        this.dispatchEvent(new CustomEvent('envoy-message-received', {
          detail: { text: botMsg.text },
          bubbles: true,
          composed: true
        }));
      } catch (err: any) {
        console.error('[envoy-chatbot] Synchronous chat error:', err);
        this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: err.message || 'Connection failed' });
        const errorType = this.mapErrorToType(err.message || '', false);
        this.errorToastController.show(errorType, () => {
          this.sendMessage(userPrompt, true);
        });
      }
    }
  }

  public async runSimulatedResponse(userPrompt: string) {
    if (this.branding.featureFlags.typingAnimation) {
      await new Promise(resolve => setTimeout(resolve, 800));
    }

    const botMsg: Message = {
      id: `bot-${Date.now()}`,
      sender: 'bot',
      text: '',
      timestamp: new Date().toISOString(),
      isStreaming: true
    };

    const reply = this.getSimulatedReply(userPrompt);

    if (this.branding.featureFlags.streamingResponses) {
      this.conversationStateMachine.transition({ type: 'RECEIVE_TOKEN' });
      this.messages.push(botMsg);
      this.appendMessageDOM(botMsg);
      const bubble = this.shadowRoot!.getElementById(`msg-${botMsg.id}`) as HTMLDivElement;

      let wordIndex = 0;
      this.currentStreamInterval = window.setInterval(() => {
        if (wordIndex < reply.length) {
          botMsg.text += reply[wordIndex];
          if (bubble) {
            bubble.innerHTML = MarkdownRenderer.render(botMsg.text);
          }
          wordIndex++;
          if (this.autoScrollController) {
            this.autoScrollController.scroll();
          }
        } else {
          if (this.currentStreamInterval) {
            clearInterval(this.currentStreamInterval);
            this.currentStreamInterval = null;
          }
          botMsg.isStreaming = false;
          if (bubble) {
            bubble.classList.remove('envoy-streaming');
          }
          this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });

          if (this.branding.featureFlags.conversationHistory) {
            this.saveHistory();
          }

          this.dispatchEvent(new CustomEvent('envoy-message-received', {
            detail: { text: botMsg.text },
            bubbles: true,
            composed: true
          }));
        }
      }, 25);
    } else {
      botMsg.text = reply;
      botMsg.isStreaming = false;
      this.messages.push(botMsg);
      this.appendMessageDOM(botMsg);
      if (this.autoScrollController) {
        this.autoScrollController.forceScroll();
      }
      this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });

      if (this.branding.featureFlags.conversationHistory) {
        this.saveHistory();
      }

      this.dispatchEvent(new CustomEvent('envoy-message-received', {
        detail: { text: botMsg.text },
        bubbles: true,
        composed: true
      }));
    }
  }

  public getSimulatedReply(prompt: string): string {

    const q = prompt.toLowerCase();
    if (q.includes('hello') || q.includes('hi')) {
      return `Hello there! I am your Envoy AI agent. How can I help you configure or manage your chatbot workspace today?`;
    }
    if (q.includes('sync') || q.includes('synchronize')) {
      return `To synchronize the chatbot brain manually, navigate to the "Knowledge Metrics" workspace tab in your dashboard, click "Synchronize Brain" and verify the list of pending documents in the confirmation dialog.`;
    }
    if (q.includes('branding') || q.includes('color')) {
      return `You can customize theme layouts, launcher text, welcome prompts, and colors directly inside the "Branding" config panel. These values are automatically loaded at runtime inside this chatbot widget.`;
    }
    return `That's an interesting question about "${prompt}". Envoy AI is currently fully configured to parse context from documents stored in Qdrant collections. Let me know if you would like assistance indexing files!`;
  }

  private getOrCreateConversationId(): string {
    if (!this.conversationId) {
      const historyKey = `envoy-chat-conv-id-${this.botId}`;
      if (this.branding.featureFlags.conversationHistory) {
        const stored = localStorage.getItem(historyKey);
        if (stored) {
          this.conversationId = stored;
          return this.conversationId;
        }
      }
      this.conversationId = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
      if (this.branding.featureFlags.conversationHistory) {
        localStorage.setItem(historyKey, this.conversationId);
      }
    }
    return this.conversationId;
  }

  private scrollToBottom() {
    this.messagesContainerEl.scrollTop = this.messagesContainerEl.scrollHeight;
  }

  private cleanup() {
    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }
    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }
    if (this.errorToastController) {
      this.errorToastController.dismiss();
    }
  }
}

// Register Web Component Custom Element
if (!customElements.get('envoy-chatbot')) {
  customElements.define('envoy-chatbot', EnvoyChatbot);
}
