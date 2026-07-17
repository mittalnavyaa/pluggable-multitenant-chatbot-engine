// packages/chatbot-ui/src/index.ts

import stylesText from './styles.css?inline';
import { type Message, type BrandingConfig, type WidgetState, type OverflowMenuItemConfig } from './types';
import { brandingStore } from './branding/branding-store';
import { CSSVariableMapper } from './branding/css-variable-mapper';
import { DEFAULT_ENVOY_THEME } from './branding/default-theme';
import { SSEClient } from './streaming/sse-client';

import { UIStateMachine } from './ui/ui-state-machine';
import { ErrorToastController, type ErrorType } from './ui/error-toast';
import { AutoScrollController } from './ui/auto-scroll';
import { RetryController } from './ui/retry-controller';

// Import newly refactored modular presentation components
import { Launcher } from './components/Launcher';
import { ChatWindow } from './components/ChatWindow';
import { Header } from './components/Header';
import { OverflowMenu } from './components/OverflowMenu';
import { MessageList } from './components/MessageList';
import { MessageBubble } from './components/MessageBubble';
import { SuggestionChips } from './components/SuggestionChips';
import { ChatInput } from './components/ChatInput';
import { TypingIndicator } from './components/TypingIndicator';

// Import persistence & export interfaces
import { type ConversationStorage, LocalStorageConversationStorage } from './persistence/storage';
import { ExporterRegistry } from './export/exporter';

export interface EnvoyChatbotConfig {
  productId?: string;
  botId?: string;
  apiBase?: string;
  branding?: Partial<BrandingConfig>;
  theme?: 'light' | 'dark' | 'auto';
  position?: {
    anchor?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
    offsetX?: number;
    offsetY?: number;
  };
  suggestedQuestions?: string[];
  overflowMenu?: OverflowMenuItemConfig[];
  storageProvider?: ConversationStorage;
  callbacks?: {
    onOpen?: () => void;
    onClose?: () => void;
    onConversationStarted?: () => void;
    onConversationRestarted?: () => void;
    onConversationCleared?: () => void;
    onMessageSent?: (text: string) => void;
    onMessageReceived?: (text: string) => void;
    onStreamingStarted?: () => void;
    onStreamingFinished?: (text: string) => void;
    onError?: (type: string, message: string) => void;
  };
}

export class EnvoyChatbot extends HTMLElement {
  private isOpen: boolean = false;
  private messages: Message[] = [];
  private branding: BrandingConfig = { ...DEFAULT_ENVOY_THEME };
  private botId: string = '';
  private apiBase: string = '';
  private conversationId: string = '';
  private currentStreamInterval: number | null = null;
  private activeSseClient: SSEClient | null = null;
  
  // Controllers
  private conversationStateMachine = new UIStateMachine();
  private retryController = new RetryController();
  private autoScrollController!: AutoScrollController;
  private errorToastController!: ErrorToastController;
  private storage: ConversationStorage = new LocalStorageConversationStorage();
  
  // Dynamic unified configurations
  private config: EnvoyChatbotConfig = {};

  // DOM Elements refs inside Shadow DOM
  private containerEl!: HTMLDivElement;
  private notificationsContainerEl!: HTMLDivElement;

  // Refactored presentation components
  private launcherComponent!: Launcher;
  private chatWindowComponent!: ChatWindow;
  private headerComponent!: Header;
  private overflowMenuComponent!: OverflowMenu;
  private messageListComponent!: MessageList;
  private suggestedChipsComponent!: SuggestionChips;
  private typingIndicatorComponent!: TypingIndicator;
  private chatInputComponent!: ChatInput;

  // Media Query listener for Auto Theme
  private themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
  private themeListener = (e: MediaQueryListEvent) => {
    if (this.getCurrentTheme() === 'auto') {
      this.applyThemeMode(e.matches ? 'dark' : 'light');
    }
  };

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get observedAttributes() {
    return [
      'data-bot-id',
      'data-api-base',
      'data-position',
      'data-theme',
      'data-welcome-message',
      'data-primary-color',
      'data-suggested-questions'
    ];
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    if (oldValue === newValue) return;

    if (name === 'data-bot-id') {
      this.botId = newValue;
      this.refreshBranding();
    } else if (name === 'data-api-base') {
      this.apiBase = newValue;
      this.refreshBranding();
    } else if (name === 'data-position') {
      const parsed = this.parsePositionString(newValue);
      if (parsed) {
        this.config.position = parsed;
        this.applyPosition();
      }
    } else if (name === 'data-theme') {
      if (newValue === 'light' || newValue === 'dark' || newValue === 'auto') {
        this.config.theme = newValue;
        this.applyThemeMode(this.getCurrentTheme() === 'auto' ? (this.themeMediaQuery.matches ? 'dark' : 'light') : (newValue as 'light' | 'dark'));
      }
    } else if (name === 'data-welcome-message') {
      if (this.branding.content) {
        this.branding.content.welcomeMessage = newValue;
        this.resetConversation(false); // Reload welcome
      }
    } else if (name === 'data-primary-color') {
      if (this.branding.colors) {
        this.branding.colors.primaryColor = newValue;
        this.applyThemeStyles();
      }
    } else if (name === 'data-suggested-questions') {
      try {
        const questions = JSON.parse(newValue);
        if (Array.isArray(questions)) {
          this.config.suggestedQuestions = questions;
          this.applyFeatureFlags();
        }
      } catch {
        const questions = newValue.split(',').map(q => q.trim()).filter(Boolean);
        this.config.suggestedQuestions = questions;
        this.applyFeatureFlags();
      }
    }
  }

  private parsePositionString(posStr: string) {
    // Expected formats: "bottom-left" or "{anchor: 'bottom-left', offsetX: 20, offsetY: 20}"
    if (!posStr) return null;
    const clean = posStr.trim();
    if (['bottom-right', 'bottom-left', 'top-right', 'top-left'].includes(clean)) {
      return { anchor: clean as any };
    }
    try {
      const parsed = JSON.parse(clean.replace(/'/g, '"'));
      if (parsed && typeof parsed === 'object') {
        return parsed;
      }
    } catch {}
    return null;
  }

  async connectedCallback() {
    this.botId = this.getAttribute('data-bot-id') || '';
    this.apiBase = this.getAttribute('data-api-base') || window.location.origin;

    // Load initial parameters from element properties if set prior to mounting
    const elementTheme = this.getAttribute('data-theme') as any;
    if (elementTheme) this.config.theme = elementTheme;

    // Build UI DOM structure
    this.renderStructure();

    // Bind state machine listeners to update loading states and typing status
    this.conversationStateMachine.addListener((state) => {
      // Manage disable/loading visual state of input elements
      const isWorking = ['sending', 'connecting', 'waiting', 'reconnecting'].includes(state);
      this.chatInputComponent.setDisabled(isWorking);
      
      // Manage streaming toggle on textinput (Stop Generation trigger)
      this.chatInputComponent.setStreaming(state === 'streaming');

      if (state === 'typing') {
        this.typingIndicatorComponent.show();
      } else {
        this.typingIndicatorComponent.hide();
      }

      // Update status dot visual styles in header
      const statusDot = this.headerComponent.getStatusDot();
      if (statusDot) {
        statusDot.className = 'absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white/20 transition-all duration-300';
        switch (state) {
          case 'connecting':
          case 'reconnecting':
          case 'sending':
            statusDot.classList.add('bg-amber-400', 'animate-pulse');
            statusDot.setAttribute('title', 'Connecting...');
            break;
          case 'waiting':
          case 'typing':
          case 'streaming':
            statusDot.classList.add('bg-blue-400', 'animate-pulse');
            statusDot.setAttribute('title', 'Responding...');
            break;
          case 'failed':
            statusDot.classList.add('bg-red-500');
            statusDot.setAttribute('title', 'Connection error');
            break;
          case 'idle':
          case 'completed':
          case 'cancelled':
          default:
            if (this.branding.content.onlineStatus === 'offline' || this.branding.content.onlineStatus === false) {
              statusDot.classList.add('bg-slate-400');
              statusDot.setAttribute('title', 'Offline');
            } else {
              statusDot.classList.add('bg-green-400', 'animate-pulse');
              statusDot.setAttribute('title', 'Online');
            }
            break;
        }
      }
    });

    // Register listener on store changes
    brandingStore.addListener(this.onBrandingUpdate.bind(this));

    // Register system color updates
    this.themeMediaQuery.addEventListener('change', this.themeListener);

    // Initial load
    this.refreshBranding();
  }

  disconnectedCallback() {
    this.cleanup();
    this.themeMediaQuery.removeEventListener('change', this.themeListener);
  }

  // ------------------------------------------------------------------ #
  //  Public Javascript SDK Control APIs                                #
  // ------------------------------------------------------------------ #

  public setConfiguration(config: EnvoyChatbotConfig) {
    this.config = { ...this.config, ...config };
    
    if (config.botId) this.botId = config.botId;
    if (config.apiBase) this.apiBase = config.apiBase;
    if (config.storageProvider) this.storage = config.storageProvider;
    
    this.refreshBranding(true);
  }

  public getConfiguration(): EnvoyChatbotConfig {
    return this.config;
  }

  public open() {
    if (this.isOpen) return;
    this.isOpen = true;
    this.launcherComponent.setOpenState(true);
    this.chatWindowComponent.setOpen(true);
    this.chatInputComponent.focus();
    this.emitSDKEvent('envoy-chat-opened');
  }

  public close() {
    if (!this.isOpen) return;
    this.isOpen = false;
    this.launcherComponent.setOpenState(false);
    this.chatWindowComponent.setOpen(false);
    this.overflowMenuComponent.close();
    this.emitSDKEvent('envoy-chat-closed');
  }

  public toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  public restart() {
    this.resetConversation(true);
  }

  public clear() {
    this.messages = [];
    this.messageListComponent.clear();
    this.storage.clearConversation(this.botId);
    this.emitSDKEvent('envoy-conversation-cleared');
  }

  public resetConversation(userInitiated = true) {
    this.messages = [];
    this.messageListComponent.clear();
    
    // Clear persistence
    this.storage.clearConversation(this.botId);
    
    // Reset conversation ID
    this.conversationId = '';

    // Disconnect active streaming channels
    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }

    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }

    // Add welcome message
    this.addWelcomeMessage();
    
    this.conversationStateMachine.transition({ type: 'RESET' });
    this.retryController.clear();
    if (this.errorToastController) {
      this.errorToastController.dismiss();
    }

    if (userInitiated) {
      this.emitSDKEvent('envoy-conversation-restarted');
    }
  }

  public async sendMessage(text: string, isRetry = false) {
    const currentState = this.conversationStateMachine.getState();
    const isWorking = ['sending', 'connecting', 'waiting', 'typing', 'streaming', 'reconnecting'].includes(currentState);
    if (!text.trim() || isWorking) return;
    
    if (this.errorToastController) {
      this.errorToastController.dismiss();
    }

    if (!isRetry) {
      this.retryController.saveLastPrompt(text);

      const userMsg: Message = {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: text,
        timestamp: new Date().toISOString()
      };
      
      const isFirstMessage = this.messages.length <= 1; // Only welcome exists
      this.messages.push(userMsg);
      this.messageListComponent.appendMessage(userMsg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
      
      if (isFirstMessage) {
        this.emitSDKEvent('envoy-conversation-started');
      }
      this.autoScrollController.forceScroll();
    }

    // Save history if feature flag enabled
    if (this.branding.featureFlags.conversationHistory) {
      this.storage.saveConversation(this.botId, this.messages, this.getOrCreateConversationId());
    }

    // Hide quick suggestion chips on interaction
    this.suggestedChipsComponent.hide();

    this.emitSDKEvent('envoy-message-sent', text);

    this.conversationStateMachine.transition({ type: 'SEND' });

    // Stream/fetch response
    await this.generateBotResponse(text, isRetry);
  }

  public destroy() {
    this.cleanup();
    this.remove();
  }

  // ------------------------------------------------------------------ #
  //  Internal Setup and Orchestration                                  #
  // ------------------------------------------------------------------ #

  private renderStructure() {
    const root = this.shadowRoot!;
    
    // Inject styles
    const style = document.createElement('style');
    style.textContent = stylesText;
    root.appendChild(style);

    // Host position container
    this.containerEl = document.createElement('div');
    this.containerEl.id = 'envoy-widget-container';
    this.containerEl.className = 'fixed z-[9999] font-sans text-sm select-none antialiased envoy-theme-font envoy-position-bottom-right';
    
    // Create UI sub-components
    // 1. Launcher button
    this.launcherComponent = new Launcher(this.containerEl, () => this.toggle());

    // 2. Chat dialog container
    this.chatWindowComponent = new ChatWindow(this.containerEl);
    const win = this.chatWindowComponent.getElement();

    // 3. Header bar
    this.headerComponent = new Header(win, {
      onCloseClick: () => this.close(),
      onRestartClick: () => this.restart(),
      onOverflowToggle: () => this.overflowMenuComponent.toggle()
    });

    // 4. Overflow Dropdown menu
    this.overflowMenuComponent = new OverflowMenu(win, (item) => this.handleOverflowItemClick(item));

    // 5. Notifications Area
    this.notificationsContainerEl = document.createElement('div');
    this.notificationsContainerEl.id = 'envoy-notifications';
    this.notificationsContainerEl.className = 'absolute top-14 left-4 right-4 z-[1000] pointer-events-none flex flex-col gap-2';
    win.appendChild(this.notificationsContainerEl);
    
    this.errorToastController = new ErrorToastController(
      this.notificationsContainerEl,
      () => this.branding
    );

    // 6. Messages List area
    this.messageListComponent = new MessageList(win);
    this.autoScrollController = new AutoScrollController(this.messageListComponent.getElement());

    // 7. Suggestions quick action chips
    this.suggestedChipsComponent = new SuggestionChips(win, (text) => this.sendMessage(text));

    // 8. Typing indicator
    this.typingIndicatorComponent = new TypingIndicator(win);

    // 9. Form input controls
    this.chatInputComponent = new ChatInput(win, {
      onSend: (text) => this.sendMessage(text),
      onStop: () => this.stopGeneration()
    });

    root.appendChild(this.containerEl);
  }

  private onBrandingUpdate(config: BrandingConfig, _state: WidgetState) {
    // Merge backend branding config with SDK properties config if defined
    let merged = { ...config };
    if (this.config.branding) {
      merged = {
        ...merged,
        ...this.config.branding,
        colors: { ...merged.colors, ...this.config.branding.colors },
        typography: { ...merged.typography, ...this.config.branding.typography },
        layout: { ...merged.layout, ...this.config.branding.layout },
        assets: { ...merged.assets, ...this.config.branding.assets },
        content: { ...merged.content, ...this.config.branding.content },
        featureFlags: { ...merged.featureFlags, ...this.config.branding.featureFlags }
      };
    }

    this.branding = merged;

    // Apply configurations to visual items
    this.applyThemeStyles();
    this.applyPosition();
    const theme = this.getCurrentTheme();
    this.applyThemeMode(theme === 'auto' ? (this.themeMediaQuery.matches ? 'dark' : 'light') : (theme as 'light' | 'dark'));
    this.applyFeatureFlags();
  }

  private async refreshBranding(force = false) {
    if (this.botId) {
      await brandingStore.loadBranding(this.botId, this.apiBase, force);
    }
  }

  private applyThemeStyles() {
    const cssVars = CSSVariableMapper.mapToCSS(this.branding);
    for (const [key, value] of Object.entries(cssVars)) {
      this.style.setProperty(key, value);
    }

    // Pass styling rules to widgets
    this.chatWindowComponent.updateLayout(this.branding);
    this.launcherComponent.updateBranding(this.branding.colors.primaryColor || '#2563eb', this.branding.assets.launcherIcon);
    this.headerComponent.updateBranding(this.branding);
    this.chatInputComponent.updateBranding(this.branding);
    this.typingIndicatorComponent.updateTheme(this.branding);
  }

  private applyPosition() {
    const pos = this.config.position || this.branding.layout.position || {};
    const anchor = pos.anchor || 'bottom-right';
    
    // Clear class lists
    this.containerEl.classList.remove(
      'envoy-position-bottom-right',
      'envoy-position-bottom-left',
      'envoy-position-top-right',
      'envoy-position-top-left'
    );
    this.containerEl.classList.add(`envoy-position-${anchor}`);

    if (pos.offsetX !== undefined) {
      this.style.setProperty('--envoy-offset-x', `${pos.offsetX}px`);
    } else {
      this.style.removeProperty('--envoy-offset-x');
    }

    if (pos.offsetY !== undefined) {
      this.style.setProperty('--envoy-offset-y', `${pos.offsetY}px`);
    } else {
      this.style.removeProperty('--envoy-offset-y');
    }

    this.chatWindowComponent.updateLayout(this.branding);
  }

  private applyThemeMode(mode: 'light' | 'dark') {
    if (mode === 'dark') {
      this.containerEl.classList.add('dark');
    } else {
      this.containerEl.classList.remove('dark');
    }
  }

  private getCurrentTheme(): 'light' | 'dark' | 'auto' {
    return this.config.theme || this.branding.theme || 'auto';
  }

  private applyFeatureFlags() {
    const flags = this.branding.featureFlags;

    // Suggested Questions
    const questions = this.config.suggestedQuestions || this.branding.content.suggestedQuestions || [];
    if (flags.suggestedQuestions && this.messages.length <= 1 && questions.length > 0) {
      this.suggestedChipsComponent.setQuestions(questions, this.branding.colors.primaryColor || '#2563eb');
    } else {
      this.suggestedChipsComponent.hide();
    }

    // Overflow Menu config update
    const menuItems = this.config.overflowMenu || this.branding.overflowMenu || [];
    this.overflowMenuComponent.setConfig(menuItems);

    // Dynamic History loading
    if (flags.conversationHistory && this.messages.length === 0) {
      this.loadHistory();
    } else if (this.messages.length === 0) {
      this.addWelcomeMessage();
    }
  }

  private addWelcomeMessage() {
    const welcomeMsg: Message = {
      id: 'welcome',
      sender: 'bot',
      text: this.branding.content.welcomeMessage || 'Hello! How can I help you today?',
      timestamp: new Date().toISOString()
    };
    this.messages.push(welcomeMsg);
    this.messageListComponent.appendMessage(welcomeMsg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
  }

  private loadHistory() {
    const data = this.storage.loadConversation(this.botId);
    if (data && data.messages.length > 0) {
      this.conversationId = data.conversationId;
      this.messages = data.messages;
      this.messageListComponent.clear();
      this.messages.forEach(msg => {
        this.messageListComponent.appendMessage(msg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
      });
      this.autoScrollController.forceScroll();
      this.suggestedChipsComponent.hide();
    } else {
      this.addWelcomeMessage();
    }
  }

  private handleMessageAction(action: 'copy' | 'regenerate' | 'thumbs-up' | 'thumbs-down', messageId: string) {
    if (action === 'copy') {
      const msg = this.messages.find(m => m.id === messageId);
      if (msg) {
        navigator.clipboard.writeText(msg.text).catch(err => {
          console.error('[envoy-chatbot] Clipboard write failed:', err);
        });
      }
    } else if (action === 'regenerate') {
      const msgIdx = this.messages.findIndex(m => m.id === messageId);
      if (msgIdx >= 0) {
        // Find preceding user prompt
        let userPrompt = '';
        for (let i = msgIdx - 1; i >= 0; i--) {
          if (this.messages[i].sender === 'user') {
            userPrompt = this.messages[i].text;
            break;
          }
        }
        if (userPrompt) {
          // Splice conversation to strip the bot response
          this.messages.splice(msgIdx);
          this.messageListComponent.clear();
          this.messages.forEach(msg => {
            this.messageListComponent.appendMessage(msg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
          });
          this.autoScrollController.forceScroll();

          this.conversationStateMachine.transition({ type: 'SEND' });
          this.generateBotResponse(userPrompt, true);
        }
      }
    } else {
      // Emit Thumbs Up / Thumbs Down feedback to host application
      this.emitSDKEvent('envoy-feedback', { messageId, rating: action });
    }
  }

  private handleOverflowItemClick(item: OverflowMenuItemConfig) {
    if (item.actionType === 'restart') {
      this.restart();
    } else if (item.actionType === 'clear') {
      this.clear();
    } else if (item.actionType === 'download') {
      this.downloadConversation(item.id);
    } else if (item.actionType === 'url') {
      if (item.url) {
        window.open(item.url, '_blank', 'noopener,noreferrer');
      }
    } else if (item.actionType === 'callback') {
      // Trigger host callback custom event
      this.emitSDKEvent(item.eventName || `envoy-${item.id}-clicked`, item);
    }
  }

  private downloadConversation(formatId: string) {
    const format = formatId === 'download' ? 'txt' : formatId;
    let exporter;
    try {
      exporter = ExporterRegistry.getExporter(format);
    } catch {
      exporter = ExporterRegistry.getExporter('txt');
    }

    const output = exporter.export(this.messages);
    const blob = new Blob([output], { type: exporter.getMimeType() });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${this.botId || 'history'}.${exporter.getFileExtension()}`;
    a.click();
    
    URL.revokeObjectURL(url);
  }

  private stopGeneration() {
    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }
    this.conversationStateMachine.transition({ type: 'CANCEL_STREAM' });
    this.emitSDKEvent('envoy-chat-closed'); // Also closes indicator, triggers completion hooks
  }

  private emitSDKEvent(name: string, detail?: any) {
    // Dispatch custom event
    this.dispatchEvent(new CustomEvent(name, { bubbles: true, composed: true, detail }));
    
    // Call property callbacks if configured
    const cbName = this.mapEventToCallbackName(name);
    if (this.config.callbacks && (this.config.callbacks as any)[cbName]) {
      try {
        (this.config.callbacks as any)[cbName](detail);
      } catch (err) {
        console.error(`[envoy-chatbot] Callback ${cbName} error:`, err);
      }
    }
  }

  private mapEventToCallbackName(name: string): string {
    const mapping: Record<string, string> = {
      'envoy-chat-opened': 'onOpen',
      'envoy-chat-closed': 'onClose',
      'envoy-conversation-started': 'onConversationStarted',
      'envoy-conversation-restarted': 'onConversationRestarted',
      'envoy-conversation-cleared': 'onConversationCleared',
      'envoy-message-sent': 'onMessageSent',
      'envoy-message-received': 'onMessageReceived',
      'envoy-streaming-started': 'onStreamingStarted',
      'envoy-streaming-finished': 'onStreamingFinished',
      'envoy-error': 'onError'
    };
    return mapping[name] || '';
  }

  private async generateBotResponse(userPrompt: string, isRetry = false) {
    if (isRetry) {
      this.conversationStateMachine.transition({ type: 'RECONNECT' });
    } else {
      this.conversationStateMachine.transition({ type: 'CONNECT' });
    }

    if (this.activeSseClient) {
      this.activeSseClient.disconnect();
      this.activeSseClient = null;
    }

    if (this.currentStreamInterval) {
      clearInterval(this.currentStreamInterval);
      this.currentStreamInterval = null;
    }

    this.conversationStateMachine.transition({ type: 'CONNECTED' });
    if (this.branding.featureFlags.typingAnimation) {
      this.conversationStateMachine.transition({ type: 'SHOW_TYPING' });
    }
    this.autoScrollController.scroll();

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
        let bubble: MessageBubble | null = null;

        this.activeSseClient = new SSEClient({
          apiBase: this.apiBase,
          botId: this.botId,
          prompt: userPrompt,
          onStatusChange: (status, errorMsg) => {
            if (status === 'streaming') {
              this.conversationStateMachine.transition({ type: 'RECEIVE_TOKEN' });
              this.emitSDKEvent('envoy-streaming-started');
            } else if (status === 'completed') {
              this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });
              if (botMsg.isStreaming) {
                botMsg.isStreaming = false;
                if (bubble) bubble.setStreaming(false);
              }
            } else if (status === 'failed') {
              this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: errorMsg || 'Stream error' });
            }
          },
          onToken: (token) => {
            streamSucceeded = true;
            this.conversationStateMachine.transition({ type: 'RECEIVE_TOKEN' });

            if (!bubbleAppended) {
              bubbleAppended = true;
              this.messages.push(botMsg);
              // Append using the MessageList component
              bubble = this.messageListComponent.appendMessage(botMsg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
            }
            botMsg.text += token;
            if (bubble) {
              bubble.updateText(botMsg.text);
            }
            this.autoScrollController.scroll();
          },
          onComplete: () => {
            this.activeSseClient = null;
            this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });
            
            if (this.branding.featureFlags.conversationHistory) {
              this.storage.saveConversation(this.botId, this.messages, this.getOrCreateConversationId());
            }

            this.emitSDKEvent('envoy-message-received', botMsg.text);
            this.emitSDKEvent('envoy-streaming-finished', botMsg.text);
          },
          onError: (errorMsg) => {
            this.activeSseClient = null;
            console.error('[envoy-chatbot] SSE Streaming error:', errorMsg);

            this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: errorMsg });
            this.emitSDKEvent('envoy-error', { type: 'streaming', message: errorMsg });

            const errorType = this.mapErrorToType(errorMsg, streamSucceeded);
            this.errorToastController.show(errorType, () => {
              this.sendMessage(userPrompt, true);
            });

            if (streamSucceeded && bubble) {
              botMsg.isStreaming = false;
              bubble.setStreaming(false);
            }
            this.autoScrollController.scroll();
          }
        });

        await this.activeSseClient.connect();
        return;
      } catch (err: any) {
        console.warn('[envoy-chatbot] SSE connection establishment failed, retrying synchronously.', err);
        this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: err.message || 'Stream connection failed' });
        this.emitSDKEvent('envoy-error', { type: 'connection', message: err.message || 'SSE connection failed' });
        
        const errorType = this.mapErrorToType(err.message || '', false);
        this.errorToastController.show(errorType, () => {
          this.sendMessage(userPrompt, true);
        });
      }
    } else {
      // Synchronous post fallback
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
        this.messageListComponent.appendMessage(botMsg, this.branding.colors.primaryColor || '#2563eb', this.handleMessageAction.bind(this));
        
        this.autoScrollController.forceScroll();
        this.conversationStateMachine.transition({ type: 'COMPLETE_STREAM' });

        if (this.branding.featureFlags.conversationHistory) {
          this.storage.saveConversation(this.botId, this.messages, this.getOrCreateConversationId());
        }

        this.emitSDKEvent('envoy-message-received', botMsg.text);
      } catch (err: any) {
        console.error('[envoy-chatbot] Synchronous chat error:', err);
        this.conversationStateMachine.transition({ type: 'FAIL_STREAM', error: err.message || 'Fetch failed' });
        this.emitSDKEvent('envoy-error', { type: 'fetch', message: err.message || 'Fetch failed' });
        
        const errorType = this.mapErrorToType(err.message || '', false);
        this.errorToastController.show(errorType, () => {
          this.sendMessage(userPrompt, true);
        });
      }
    }
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

  private getOrCreateConversationId(): string {
    if (!this.conversationId) {
      const data = this.storage.loadConversation(this.botId);
      if (data && data.conversationId) {
        this.conversationId = data.conversationId;
      } else {
        this.conversationId = `conv_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
        this.storage.saveConversation(this.botId, this.messages, this.conversationId);
      }
    }
    return this.conversationId;
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
