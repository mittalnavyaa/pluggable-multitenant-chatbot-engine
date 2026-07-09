// packages/chatbot-ui/src/index.ts

import stylesText from './styles.css?raw';
import { type Message, type BrandingConfig, type WidgetState } from './types';

export class EnvoyChatbot extends HTMLElement {
  private isOpen: boolean = false;
  private state: WidgetState = 'idle';
  private messages: Message[] = [];
  private branding: BrandingConfig = {
    primaryColor: '#2563eb',
    accentColor: '#10b981',
    widgetTitle: 'Envoy AI Agent',
    launcherLabel: 'Chat with Envoy AI',
    welcomeMessage: 'Hello! I am Envoy AI, your helpful assistant. How can I help you today?',
    borderRadius: '12px',
    fontFamily: 'Inter, system-ui, sans-serif'
  };

  private botId: string = '';
  private apiBase: string = '';
  private currentStreamInterval: number | null = null;

  // DOM Elements refs inside Shadow DOM
  private containerEl!: HTMLDivElement;
  private launcherEl!: HTMLButtonElement;
  private chatWindowEl!: HTMLDivElement;
  private messagesContainerEl!: HTMLDivElement;
  private inputEl!: HTMLTextAreaElement;
  private sendBtnEl!: HTMLButtonElement;
  private typingIndicatorEl!: HTMLDivElement;

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
    } else if (name === 'data-api-base') {
      this.apiBase = newValue;
    }
  }

  async connectedCallback() {
    this.botId = this.getAttribute('data-bot-id') || '';
    this.apiBase = this.getAttribute('data-api-base') || window.location.origin;

    // Build DOM structure
    this.renderStructure();
    
    // Fetch branding configuration
    await this.loadBranding();
    
    // Setup event listeners
    this.setupListeners();
    this.applyTheme();
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
    this.addWelcomeMessage();
    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }
    this.typingIndicatorEl.classList.add('hidden');
    this.state = 'idle';
  }

  public async sendMessage(text: string) {
    if (!text.trim() || this.state === 'loading') return;
    
    // Append User Message
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: text,
      timestamp: new Date().toISOString()
    };
    this.messages.push(userMsg);
    this.appendMessageDOM(userMsg);
    this.scrollToBottom();

    this.dispatchEvent(new CustomEvent('envoy-message-sent', { 
      detail: { text }, 
      bubbles: true, 
      composed: true 
    }));

    // Trigger typing response simulation
    await this.generateBotResponse(text);
  }

  public destroy() {
    this.cleanup();
    this.remove();
  }

  // ------------------------------------------------------------------ #
  //  Internal Layout & Logic                                           #
  // ------------------------------------------------------------------ #

  private renderStructure() {
    const root = this.shadowRoot!;
    
    // Inject Styles text directly into Shadow DOM
    const style = document.createElement('style');
    style.textContent = stylesText;
    root.appendChild(style);

    // Host styling variables setup
    this.containerEl = document.createElement('div');
    this.containerEl.className = 'fixed bottom-5 right-5 z-[9999] font-sans text-sm select-none antialiased';
    this.containerEl.innerHTML = `
      <!-- Floating Launcher Button -->
      <button type="button" id="envoy-launcher" class="w-14 h-14 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 hover:scale-105 active:scale-95 cursor-pointer text-white focus:outline-none focus:ring-4 focus:ring-blue-300" aria-label="Open Chatbot Window">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>

      <!-- Expandable Chat Window -->
      <div id="envoy-chat-window" class="hidden absolute bottom-16 right-0 w-[380px] h-[520px] bg-white dark:bg-dk-surface border border-lt-border dark:border-dk-border rounded-xl shadow-2xl flex-col overflow-hidden transition-all duration-200">
        <!-- Header -->
        <header id="envoy-header" class="px-4 py-3 flex items-center justify-between text-white shadow-md">
          <div class="flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full bg-green-400 animate-pulse"></span>
            <span id="envoy-title" class="font-semibold truncate max-w-[200px]">${this.branding.widgetTitle}</span>
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

        <!-- Message Area -->
        <div id="envoy-messages" class="flex-1 p-4 overflow-y-auto bg-lt-bg dark:bg-dk-bg flex flex-col gap-3 envoy-messages-container">
          <!-- Dynamically populated -->
        </div>

        <!-- Typing Indicator -->
        <div id="envoy-typing" class="hidden px-4 py-1 text-xs text-lt-muted dark:text-dk-muted bg-lt-bg dark:bg-dk-bg flex items-center gap-1.5">
          <span class="flex gap-1 items-center">
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-500 animate-bounce" style="animation-delay: 300ms"></span>
          </span>
          <span>Agent is typing...</span>
        </div>

        <!-- Input Area -->
        <form id="envoy-input-form" class="p-3 border-t border-lt-border dark:border-dk-border bg-white dark:bg-dk-surface flex gap-2 items-center">
          <textarea id="envoy-input" placeholder="Type a message..." rows="1" class="flex-1 px-3 py-2 bg-lt-bg dark:bg-dk-bg text-lt-text dark:text-dk-text border border-lt-border dark:border-dk-border rounded-lg resize-none outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 max-h-[80px]" aria-label="Chat input field"></textarea>
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
  }

  private async loadBranding() {
    if (!this.botId) return;
    try {
      const response = await fetch(`${this.apiBase}/api/v1/products/${this.botId}`);
      if (response.ok) {
        const data = await response.json();
        // Map product response UI variables config schema
        const cfg = data.ui_theme_config || {};
        this.branding = {
          primaryColor: cfg.primaryColor || this.branding.primaryColor,
          accentColor: cfg.accentColor || this.branding.accentColor,
          widgetTitle: cfg.widgetTitle || data.name || this.branding.widgetTitle,
          launcherLabel: cfg.launcherLabel || this.branding.launcherLabel,
          welcomeMessage: cfg.welcomeMessage || this.branding.welcomeMessage,
          borderRadius: cfg.borderRadius || this.branding.borderRadius,
          fontFamily: cfg.fontFamily || this.branding.fontFamily
        };
      }
    } catch (err) {
      console.warn('[envoy-chatbot] Backend configuration unreachable. Falling back to default branding.');
    }
    
    // Add default initial welcome message
    this.resetConversation();
  }

  private applyTheme() {
    const pc = this.branding.primaryColor || '#2563eb';
    const ac = this.branding.accentColor || '#10b981';
    const br = this.branding.borderRadius || '12px';

    this.launcherEl.style.backgroundColor = pc;
    this.sendBtnEl.style.backgroundColor = pc;
    this.chatWindowEl.style.borderRadius = br;

    const header = this.shadowRoot!.getElementById('envoy-header');
    if (header) {
      header.style.backgroundColor = pc;
    }

    const titleEl = this.shadowRoot!.getElementById('envoy-title');
    if (titleEl) {
      titleEl.textContent = this.branding.widgetTitle || 'Envoy AI Agent';
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
  }

  private addWelcomeMessage() {
    const welcomeMsg: Message = {
      id: 'welcome',
      sender: 'bot',
      text: this.branding.welcomeMessage || 'Hello! How can I help you today?',
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
      bubble.style.backgroundColor = this.branding.primaryColor || '#2563eb';
    }

    bubble.setAttribute('id', `msg-${msg.id}`);
    bubble.textContent = msg.text;
    
    // Append container
    this.messagesContainerEl.appendChild(bubble);
  }

  private async generateBotResponse(userPrompt: string) {
    this.state = 'loading';
    this.typingIndicatorEl.classList.remove('hidden');
    this.scrollToBottom();

    // SSE/Streaming call attempts or fallback simulation
    const streamUrl = `${this.apiBase}/api/v1/chat/stream?bot_id=${this.botId}&prompt=${encodeURIComponent(userPrompt)}`;
    let streamSucceeded = false;

    try {
      // Future backend SSE call attempt
      const response = await fetch(streamUrl);
      if (response.ok && response.body) {
        streamSucceeded = true;
        this.typingIndicatorEl.classList.add('hidden');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        const botMsg: Message = {
          id: `bot-${Date.now()}`,
          sender: 'bot',
          text: '',
          timestamp: new Date().toISOString(),
          isStreaming: true
        };
        this.messages.push(botMsg);
        this.appendMessageDOM(botMsg);
        const bubble = this.shadowRoot!.getElementById(`msg-${botMsg.id}`) as HTMLDivElement;

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          // SSE data parse
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data:')) {
              const dataText = line.substring(5).trim();
              if (dataText === '[DONE]') break;
              try {
                const parsed = JSON.parse(dataText);
                botMsg.text += parsed.text || '';
                if (bubble) bubble.textContent = botMsg.text;
                this.scrollToBottom();
              } catch {
                botMsg.text += dataText;
                if (bubble) bubble.textContent = botMsg.text;
                this.scrollToBottom();
              }
            }
          }
        }
        botMsg.isStreaming = false;
        this.dispatchEvent(new CustomEvent('envoy-message-received', {
          detail: { text: botMsg.text },
          bubbles: true,
          composed: true
        }));
      }
    } catch {
      // Failures go to fallback simulated SSE streams
    }

    if (!streamSucceeded) {
      // Simulate typing speed of SSE stream response
      await new Promise(resolve => setTimeout(resolve, 1000));
      this.typingIndicatorEl.classList.add('hidden');

      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sender: 'bot',
        text: '',
        timestamp: new Date().toISOString(),
        isStreaming: true
      };
      this.messages.push(botMsg);
      this.appendMessageDOM(botMsg);
      const bubble = this.shadowRoot!.getElementById(`msg-${botMsg.id}`) as HTMLDivElement;

      // Realistic reply content based on user prompt keywords
      const reply = this.getSimulatedReply(userPrompt);
      let wordIndex = 0;
      
      this.currentStreamInterval = window.setInterval(() => {
        if (wordIndex < reply.length) {
          botMsg.text += reply[wordIndex];
          if (bubble) bubble.textContent = botMsg.text;
          wordIndex++;
          this.scrollToBottom();
        } else {
          if (this.currentStreamInterval) {
            clearInterval(this.currentStreamInterval);
            this.currentStreamInterval = null;
          }
          botMsg.isStreaming = false;
          this.state = 'idle';
          
          this.dispatchEvent(new CustomEvent('envoy-message-received', {
            detail: { text: botMsg.text },
            bubbles: true,
            composed: true
          }));
        }
      }, 30);
    } else {
      this.state = 'idle';
    }
  }

  private getSimulatedReply(prompt: string): string {
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

  private scrollToBottom() {
    this.messagesContainerEl.scrollTop = this.messagesContainerEl.scrollHeight;
  }

  private cleanup() {
    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }
  }
}

// Register Web Component Custom Element
if (!customElements.get('envoy-chatbot')) {
  customElements.define('envoy-chatbot', EnvoyChatbot);
}
