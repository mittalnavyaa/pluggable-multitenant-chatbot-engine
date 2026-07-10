// packages/chatbot-ui/src/tests/conversation-state.test.ts

import { UIStateMachine } from '../ui/ui-state-machine';
import { TypingIndicator } from '../ui/typing-indicator';
import { AutoScrollController } from '../ui/auto-scroll';
import { RetryController } from '../ui/retry-controller';
import { LoadingStateController } from '../ui/loading-state';
import { ErrorToastController } from '../ui/error-toast';
import { type BrandingConfig } from '../types';

describe('UIStateMachine', () => {
  let stateMachine: UIStateMachine;

  beforeEach(() => {
    stateMachine = new UIStateMachine();
  });

  test('should initialize in idle state', () => {
    expect(stateMachine.getState()).toBe('idle');
  });

  test('should validate sequential valid transitions', () => {
    expect(stateMachine.transition({ type: 'SEND' })).toBe(true);
    expect(stateMachine.getState()).toBe('sending');

    expect(stateMachine.transition({ type: 'CONNECT' })).toBe(true);
    expect(stateMachine.getState()).toBe('connecting');

    expect(stateMachine.transition({ type: 'CONNECTED' })).toBe(true);
    expect(stateMachine.getState()).toBe('waiting');

    expect(stateMachine.transition({ type: 'SHOW_TYPING' })).toBe(true);
    expect(stateMachine.getState()).toBe('typing');

    expect(stateMachine.transition({ type: 'RECEIVE_TOKEN' })).toBe(true);
    expect(stateMachine.getState()).toBe('streaming');

    expect(stateMachine.transition({ type: 'COMPLETE_STREAM' })).toBe(true);
    expect(stateMachine.getState()).toBe('completed');
  });

  test('should reject invalid transitions without changing state', () => {
    const initial = stateMachine.getState();
    expect(stateMachine.transition({ type: 'COMPLETE_STREAM' })).toBe(false);
    expect(stateMachine.getState()).toBe(initial);
  });

  test('should allow reset from failed states', () => {
    stateMachine.transition({ type: 'SEND' });
    stateMachine.transition({ type: 'FAIL_STREAM', error: 'Test error' });
    expect(stateMachine.getState()).toBe('failed');

    expect(stateMachine.transition({ type: 'RESET' })).toBe(true);
    expect(stateMachine.getState()).toBe('idle');
  });

  test('should notify registered listeners on state change', () => {
    const mockListener = jest.fn();
    stateMachine.addListener(mockListener);

    // Initial load notifies once
    expect(mockListener).toHaveBeenCalledTimes(1);

    stateMachine.transition({ type: 'SEND' });
    expect(mockListener).toHaveBeenCalledTimes(2);
    expect(mockListener).toHaveBeenLastCalledWith('sending', 'idle');
  });
});

describe('TypingIndicator', () => {
  let element: HTMLDivElement;
  let indicator: TypingIndicator;

  beforeEach(() => {
    element = document.createElement('div');
    element.innerHTML = '<span id="envoy-typing-text"></span>';
    indicator = new TypingIndicator(element);
  });

  test('should configure accessible ARIA settings', () => {
    expect(element.getAttribute('role')).toBe('status');
    expect(element.getAttribute('aria-live')).toBe('polite');
    expect(element.getAttribute('aria-label')).toBe('Agent is typing');
  });

  test('should toggle visibility class names', () => {
    indicator.show('Custom text...');
    expect(element.classList.contains('hidden')).toBe(false);
    expect(element.getAttribute('aria-hidden')).toBe('false');

    const textSpan = element.querySelector('#envoy-typing-text');
    expect(textSpan?.textContent).toBe('Custom text...');

    indicator.hide();
    expect(element.classList.contains('hidden')).toBe(true);
    expect(element.getAttribute('aria-hidden')).toBe('true');
  });
});

describe('AutoScrollController', () => {
  let container: HTMLDivElement;
  let controller: AutoScrollController;

  beforeEach(() => {
    container = document.createElement('div');
    container.scrollTo = jest.fn();
    controller = new AutoScrollController(container);
  });

  test('should scroll to the bottom when forced', () => {
    controller.forceScroll();
    expect(container.scrollTo).toHaveBeenCalledWith({
      top: container.scrollHeight,
      behavior: 'smooth',
    });
  });
});

describe('RetryController', () => {
  let controller: RetryController;

  beforeEach(() => {
    controller = new RetryController();
  });

  test('should preserve and clear search prompt cache', () => {
    expect(controller.getLastPrompt()).toBeNull();
    controller.saveLastPrompt('Test input prompt');
    expect(controller.getLastPrompt()).toBe('Test input prompt');
    controller.clear();
    expect(controller.getLastPrompt()).toBeNull();
  });
});

describe('LoadingStateController', () => {
  let textarea: HTMLTextAreaElement;
  let button: HTMLButtonElement;
  let statusDot: HTMLSpanElement;
  let controller: LoadingStateController;

  beforeEach(() => {
    textarea = document.createElement('textarea');
    button = document.createElement('button');
    statusDot = document.createElement('span');
    controller = new LoadingStateController(textarea, button, statusDot);
  });

  test('should lock forms during active streaming states', () => {
    controller.updateState('streaming');
    expect(textarea.disabled).toBe(true);
    expect(button.disabled).toBe(true);
    expect(statusDot.classList.contains('bg-blue-400')).toBe(true);

    controller.updateState('completed');
    expect(textarea.disabled).toBe(false);
    expect(button.disabled).toBe(false);
    expect(statusDot.classList.contains('bg-green-400')).toBe(true);
  });
});

describe('ErrorToastController', () => {
  let container: HTMLDivElement;
  let controller: ErrorToastController;
  const mockBranding = (): BrandingConfig => ({
    colors: {},
    typography: {},
    layout: {},
    assets: {},
    content: { errorMessage: 'Fallback config error message' },
    featureFlags: {},
  } as any);

  beforeEach(() => {
    jest.useFakeTimers();
    container = document.createElement('div');
    controller = new ErrorToastController(container, mockBranding);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should create error notifications in container', () => {
    controller.show('network');
    const toast = container.querySelector('.envoy-error-toast');
    expect(toast).not.toBeNull();
    expect(toast?.textContent).toContain('Network connection lost');

    controller.dismiss();
    // Verify toast fade out and removal
    jest.advanceTimersByTime(400);
    expect(container.querySelector('.envoy-error-toast')).toBeNull();
  });
});
