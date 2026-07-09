// packages/chatbot-ui/src/tests/widget.test.ts

import { EnvoyChatbot } from '../index';
import { BrandingValidator } from '../branding/branding-validator';
import { CSSVariableMapper } from '../branding/css-variable-mapper';
import { DEFAULT_ENVOY_THEME } from '../branding/default-theme';

describe('EnvoyChatbot Web Component', () => {
  let element: EnvoyChatbot;

  beforeEach(() => {
    element = document.createElement('envoy-chatbot') as EnvoyChatbot;
    element.setAttribute('data-bot-id', 'test-bot-id');
    element.setAttribute('data-api-base', 'http://localhost:8000');
    document.body.appendChild(element);
  });

  afterEach(() => {
    if (element && element.parentNode) {
      element.parentNode.removeChild(element);
    }
  });

  test('should initialize and attach open shadow root', () => {
    expect(element.shadowRoot).not.toBeNull();
    expect(element.shadowRoot?.mode).toBe('open');
  });

  test('should parse configuration attributes correctly', () => {
    expect(element.getAttribute('data-bot-id')).toBe('test-bot-id');
    expect(element.getAttribute('data-api-base')).toBe('http://localhost:8000');
  });

  test('should render launcher button inside Shadow DOM', () => {
    const shadow = element.shadowRoot;
    const launcher = shadow?.querySelector('#envoy-launcher');
    expect(launcher).not.toBeNull();
    expect(launcher?.tagName.toLowerCase()).toBe('button');
  });

  test('should render closed chat window by default', () => {
    const shadow = element.shadowRoot;
    const chatWindow = shadow?.querySelector('#envoy-chat-window');
    expect(chatWindow).not.toBeNull();
    expect(chatWindow?.classList.contains('hidden')).toBe(true);
  });

  test('should open chat window when open() API is called', () => {
    element.open();
    const shadow = element.shadowRoot;
    const chatWindow = shadow?.querySelector('#envoy-chat-window');
    expect(chatWindow?.classList.contains('hidden')).toBe(false);
  });

  test('should close chat window when close() API is called', () => {
    element.open();
    element.close();
    const shadow = element.shadowRoot;
    const chatWindow = shadow?.querySelector('#envoy-chat-window');
    expect(chatWindow?.classList.contains('hidden')).toBe(true);
  });

  test('should toggle chat window state when toggle() API is called', () => {
    element.toggle(); // opens
    let chatWindow = element.shadowRoot?.querySelector('#envoy-chat-window');
    expect(chatWindow?.classList.contains('hidden')).toBe(false);

    element.toggle(); // closes
    chatWindow = element.shadowRoot?.querySelector('#envoy-chat-window');
    expect(chatWindow?.classList.contains('hidden')).toBe(true);
  });

  test('should reset messages history on resetConversation()', () => {
    element.sendMessage('Test message');
    element.resetConversation();
    
    const shadow = element.shadowRoot;
    const messages = shadow?.querySelector('#envoy-messages');
    expect(messages?.children.length).toBe(1);
  });

  // ── Branding Ingestion & Theme Validation Tests ──────────────────
  
  test('BrandingValidator should validate valid and fallback on invalid color formats', () => {
    const raw = {
      colors: {
        primaryColor: '#ff0000',
        secondaryColor: 'invalid-color-string',
        accentColor: 'rgb(0, 255, 0)',
        textColor: '#000000'
      }
    };
    const validated = BrandingValidator.validate(raw);
    expect(validated.colors.primaryColor).toBe('#ff0000');
    expect(validated.colors.secondaryColor).toBe(DEFAULT_ENVOY_THEME.colors.secondaryColor); // fallback
    expect(validated.colors.accentColor).toBe('rgb(0, 255, 0)');
    expect(validated.colors.textColor).toBe('#000000');
  });

  test('BrandingValidator should default missing configuration categories', () => {
    const raw = {};
    const validated = BrandingValidator.validate(raw);
    expect(validated.colors.primaryColor).toBe(DEFAULT_ENVOY_THEME.colors.primaryColor);
    expect(validated.layout.chatWidth).toBe(DEFAULT_ENVOY_THEME.layout.chatWidth);
    expect(validated.featureFlags.fileUpload).toBe(DEFAULT_ENVOY_THEME.featureFlags.fileUpload);
  });

  test('CSSVariableMapper should map layout sizes to CSS variables', () => {
    const config = {
      ...DEFAULT_ENVOY_THEME,
      layout: {
        chatWidth: '400px',
        chatHeight: '600px',
        borderRadius: '20px'
      }
    };
    const variables = CSSVariableMapper.mapToCSS(config);
    expect(variables['--envoy-chat-width']).toBe('400px');
    expect(variables['--envoy-chat-height']).toBe('600px');
    expect(variables['--envoy-border-radius']).toBe('20px');
  });

  test('should render/hide upload and voice buttons based on feature flags', () => {
    // By default, voiceInput is disabled in DEFAULT_ENVOY_THEME
    const voiceBtn = element.shadowRoot?.querySelector('#envoy-voice-btn');
    expect(voiceBtn?.classList.contains('hidden')).toBe(true);
  });
});
