// packages/chatbot-ui/src/tests/widget.test.ts

import { BrandingValidator } from '../branding/branding-validator';
import { CSSVariableMapper } from '../branding/css-variable-mapper';
import { DEFAULT_ENVOY_THEME } from '../branding/default-theme';
import { StreamParser } from '../streaming/stream-parser';
import { MarkdownRenderer } from '../streaming/markdown-renderer';
import { SSEClient } from '../streaming/sse-client';

// Polyfill TextEncoder/TextDecoder for jsdom
import { TextEncoder, TextDecoder } from 'util';
Object.assign(global, { TextEncoder, TextDecoder });

// ── Branding Ingestion & Theme Validation Tests ──────────────────

describe('BrandingValidator', () => {
  test('should validate valid and fallback on invalid color formats', () => {
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
    expect(validated.colors.secondaryColor).toBe(DEFAULT_ENVOY_THEME.colors.secondaryColor);
    expect(validated.colors.accentColor).toBe('rgb(0, 255, 0)');
    expect(validated.colors.textColor).toBe('#000000');
  });

  test('should default missing configuration categories', () => {
    const raw = {};
    const validated = BrandingValidator.validate(raw);
    expect(validated.colors.primaryColor).toBe(DEFAULT_ENVOY_THEME.colors.primaryColor);
    expect(validated.layout.chatWidth).toBe(DEFAULT_ENVOY_THEME.layout.chatWidth);
    expect(validated.featureFlags.fileUpload).toBe(DEFAULT_ENVOY_THEME.featureFlags.fileUpload);
  });
});

describe('CSSVariableMapper', () => {
  test('should map layout sizes to CSS variables', () => {
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
});

// ── StreamParser Tests ──────────────────────────────────────────

describe('StreamParser', () => {
  let parser: StreamParser;

  beforeEach(() => {
    parser = new StreamParser();
  });

  test('should parse text chunk event', () => {
    const res = parser.parseLine('data: {"event": "text", "text": "hello"}');
    expect(res).toEqual({ event: 'text', text: 'hello' });
  });

  test('should parse done chunk event', () => {
    const res = parser.parseLine('data: {"event": "done", "message_id": "msg_abc"}');
    expect(res).toEqual({ event: 'done', message_id: 'msg_abc' });
  });

  test('should return done event for [DONE] string', () => {
    const res = parser.parseLine('data: [DONE]');
    expect(res).toEqual({ event: 'done', message_id: '' });
  });

  test('should ignore empty lines', () => {
    expect(parser.parseLine('')).toBeNull();
    expect(parser.parseLine('   ')).toBeNull();
  });

  test('should ignore SSE heartbeat/comment lines', () => {
    const res = parser.parseLine(':ping');
    expect(res).toBeNull();
  });

  test('should parse raw text as text chunk if JSON parsing fails', () => {
    const res = parser.parseLine('data: simple text');
    expect(res).toEqual({ event: 'text', text: 'simple text' });
  });

  test('should parse error chunk event', () => {
    const res = parser.parseLine('data: {"event": "error", "error": "LLM Timeout"}');
    expect(res).toEqual({ event: 'error', error: 'LLM Timeout' });
  });

  test('should return null for non-data lines', () => {
    expect(parser.parseLine('event: text')).toBeNull();
    expect(parser.parseLine('id: 123')).toBeNull();
  });
});

// ── StreamReader Tests ──────────────────────────────────────────

describe('StreamReader', () => {
  // Import after polyfill is applied
  let StreamReader: any;

  beforeAll(async () => {
    StreamReader = (await import('../streaming/stream-reader')).StreamReader;
  });

  test('should decode and emit complete lines from reader', async () => {
    const reader = new StreamReader();
    const encoder = new TextEncoder();
    const mockChunks = [
      encoder.encode('data: {"event": "text", "t'),
      encoder.encode('ext": "hello"}\n'),
      encoder.encode('data: [DONE]\n')
    ];

    let chunkIndex = 0;
    const mockReadableStreamReader = {
      read: jest.fn().mockImplementation(() => {
        if (chunkIndex < mockChunks.length) {
          return Promise.resolve({ done: false, value: mockChunks[chunkIndex++] });
        }
        return Promise.resolve({ done: true, value: undefined });
      }),
      releaseLock: jest.fn()
    } as any;

    const lines: string[] = [];
    await reader.read(mockReadableStreamReader, (line: string) => {
      lines.push(line);
    });

    expect(lines).toEqual([
      'data: {"event": "text", "text": "hello"}',
      'data: [DONE]'
    ]);
    expect(mockReadableStreamReader.releaseLock).toHaveBeenCalled();
  });

  test('should handle single-chunk complete lines', async () => {
    const reader = new StreamReader();
    const encoder = new TextEncoder();
    const mockChunks = [
      encoder.encode('data: {"event": "text", "text": "full"}\n')
    ];

    let chunkIndex = 0;
    const mockReadableStreamReader = {
      read: jest.fn().mockImplementation(() => {
        if (chunkIndex < mockChunks.length) {
          return Promise.resolve({ done: false, value: mockChunks[chunkIndex++] });
        }
        return Promise.resolve({ done: true, value: undefined });
      }),
      releaseLock: jest.fn()
    } as any;

    const lines: string[] = [];
    await reader.read(mockReadableStreamReader, (line: string) => {
      lines.push(line);
    });

    expect(lines).toEqual(['data: {"event": "text", "text": "full"}']);
  });

  test('should flush remaining buffer on stream end', async () => {
    const reader = new StreamReader();
    const encoder = new TextEncoder();
    // No trailing newline — should be flushed on done
    const mockChunks = [
      encoder.encode('data: final')
    ];

    let chunkIndex = 0;
    const mockReadableStreamReader = {
      read: jest.fn().mockImplementation(() => {
        if (chunkIndex < mockChunks.length) {
          return Promise.resolve({ done: false, value: mockChunks[chunkIndex++] });
        }
        return Promise.resolve({ done: true, value: undefined });
      }),
      releaseLock: jest.fn()
    } as any;

    const lines: string[] = [];
    await reader.read(mockReadableStreamReader, (line: string) => {
      lines.push(line);
    });

    expect(lines).toEqual(['data: final']);
  });
});

// ── MarkdownRenderer Tests ──────────────────────────────────────

describe('MarkdownRenderer', () => {
  test('should render headers correctly', () => {
    const h1 = MarkdownRenderer.render('# Hello');
    expect(h1).toContain('<h1');
    expect(h1).toContain('Hello');
    expect(h1).toContain('</h1>');

    const h3 = MarkdownRenderer.render('### Title');
    expect(h3).toContain('<h3');
    expect(h3).toContain('Title');
  });

  test('should render bold text', () => {
    const result = MarkdownRenderer.render('**bold text**');
    expect(result).toContain('<strong>bold text</strong>');
  });

  test('should render italic text', () => {
    const result = MarkdownRenderer.render('*italic text*');
    expect(result).toContain('<em>italic text</em>');
  });

  test('should render inline code', () => {
    const result = MarkdownRenderer.render('Use `console.log` here');
    expect(result).toContain('<code');
    expect(result).toContain('console.log');
    expect(result).toContain('</code>');
  });

  test('should render links', () => {
    const result = MarkdownRenderer.render('[Click](https://example.com)');
    expect(result).toContain('<a href="https://example.com"');
    expect(result).toContain('Click');
    expect(result).toContain('target="_blank"');
  });

  test('should leave unclosed bold formatting as plain escaped text', () => {
    const result = MarkdownRenderer.render('**unclosed');
    expect(result).toContain('**unclosed');
    expect(result).toContain('<p');
  });

  test('should auto-close unclosed code blocks safely (stream safety)', () => {
    const rendered = MarkdownRenderer.render('```js\nconsole.log(123);');
    expect(rendered).toContain('<pre');
    expect(rendered).toContain('<code');
    expect(rendered).toContain('console.log(123);');
    expect(rendered).toContain('</code>');
    expect(rendered).toContain('</pre>');
  });

  test('should auto-close lists safely (stream safety)', () => {
    const rendered = MarkdownRenderer.render('- Item 1\n- Item 2');
    expect(rendered).toContain('<ul');
    expect(rendered).toContain('<li>Item 1</li>');
    expect(rendered).toContain('<li>Item 2</li>');
    expect(rendered).toContain('</ul>');
  });

  test('should render ordered lists', () => {
    const rendered = MarkdownRenderer.render('1. First\n2. Second');
    expect(rendered).toContain('<ol');
    expect(rendered).toContain('<li>First</li>');
    expect(rendered).toContain('<li>Second</li>');
    expect(rendered).toContain('</ol>');
  });

  test('should render complete tables', () => {
    const complete = MarkdownRenderer.render('| Header A |\n|---|\n| Value A |');
    expect(complete).toContain('<table');
    expect(complete).toContain('<thead>');
    expect(complete).toContain('Header A');
    expect(complete).toContain('Value A');
  });

  test('should fallback incomplete tables to formatted text', () => {
    const incomplete = MarkdownRenderer.render('| Header A |\n|---|');
    expect(incomplete).not.toContain('<table');
  });

  test('should return empty string for empty input', () => {
    expect(MarkdownRenderer.render('')).toBe('');
  });

  test('should escape HTML tags to prevent XSS', () => {
    const result = MarkdownRenderer.render('<script>alert("xss")</script>');
    expect(result).not.toContain('<script>');
    expect(result).toContain('&lt;script&gt;');
  });
});

// ── SSEClient Tests ─────────────────────────────────────────────

describe('SSEClient', () => {
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
    jest.useFakeTimers();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.useRealTimers();
  });

  test('should start with idle status', () => {
    const client = new SSEClient({
      apiBase: 'http://localhost:8000',
      botId: 'test',
      prompt: 'hello'
    });
    expect(client.getStatus()).toBe('idle');
  });

  test('should transition to connecting on connect()', async () => {
    // Fetch that never resolves (pending connection)
    global.fetch = jest.fn().mockReturnValue(new Promise(() => {}));
    
    const onStatusChange = jest.fn();
    const client = new SSEClient({
      apiBase: 'http://localhost:8000',
      botId: 'test',
      prompt: 'hello',
      maxRetries: 0,
      onStatusChange
    });

    // Don't await — the connect will hang on the pending fetch
    client.connect();

    // Status should have been set to connecting
    expect(onStatusChange).toHaveBeenCalledWith('connecting', undefined);
    
    // Cleanup
    client.disconnect();
  });

  test('should call onError after exhausting retries', async () => {
    jest.useRealTimers(); // Need real timers for retry delays
    
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));
    
    const onError = jest.fn();
    const onStatusChange = jest.fn();

    const client = new SSEClient({
      apiBase: 'http://localhost:8000',
      botId: 'test-bot',
      prompt: 'hello',
      maxRetries: 1,
      retryInterval: 10,
      onStatusChange,
      onError
    });

    await client.connect();

    // Wait long enough for 1 retry with exponential backoff (10ms * 2^0 = 10ms)
    await new Promise(resolve => setTimeout(resolve, 150));

    expect(onError).toHaveBeenCalledWith('Network error');
    expect(onStatusChange).toHaveBeenCalledWith('failed', 'Network error');
  });

  test('should disconnect cleanly', () => {
    const onStatusChange = jest.fn();
    const client = new SSEClient({
      apiBase: 'http://localhost:8000',
      botId: 'test',
      prompt: 'hello',
      onStatusChange
    });

    client.disconnect();
    expect(client.getStatus()).toBe('idle');
    expect(onStatusChange).toHaveBeenCalledWith('idle', undefined);
  });

  test('should process tokens from a successful stream', async () => {
    jest.useRealTimers();

    const encoder = new TextEncoder();
    const chunks = [
      encoder.encode('data: {"event":"text","text":"Hello"}\n\n'),
      encoder.encode('data: {"event":"text","text":" world"}\n\n'),
      encoder.encode('data: {"event":"done","message_id":"msg_1"}\n\n'),
    ];

    let chunkIndex = 0;
    const mockReader = {
      read: jest.fn().mockImplementation(() => {
        if (chunkIndex < chunks.length) {
          return Promise.resolve({ done: false, value: chunks[chunkIndex++] });
        }
        return Promise.resolve({ done: true, value: undefined });
      }),
      releaseLock: jest.fn()
    };

    const mockBody = {
      getReader: () => mockReader
    };

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      body: mockBody,
      status: 200
    });

    const tokens: string[] = [];
    const onToken = jest.fn((token: string) => tokens.push(token));
    const onComplete = jest.fn();
    const onStatusChange = jest.fn();

    const client = new SSEClient({
      apiBase: 'http://localhost:8000',
      botId: 'test-bot',
      prompt: 'hello',
      onToken,
      onComplete,
      onStatusChange
    });

    await client.connect();

    expect(onToken).toHaveBeenCalledTimes(2);
    expect(tokens).toEqual(['Hello', ' world']);
    expect(onComplete).toHaveBeenCalledWith('msg_1');
    expect(onStatusChange).toHaveBeenCalledWith('streaming', undefined);
    expect(onStatusChange).toHaveBeenCalledWith('completed', undefined);
  });
});
