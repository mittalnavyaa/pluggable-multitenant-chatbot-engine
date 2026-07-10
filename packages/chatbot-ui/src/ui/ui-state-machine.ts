// packages/chatbot-ui/src/ui/ui-state-machine.ts

import { type ConversationState } from '../types';
import { type ConversationEvent, type StateListener } from './ui-types';

export class UIStateMachine {
  private currentState: ConversationState = 'idle';
  private previousState: ConversationState = 'idle';
  private listeners: Set<StateListener> = new Set();

  public getState(): ConversationState {
    return this.currentState;
  }

  public getPreviousState(): ConversationState {
    return this.previousState;
  }

  public addListener(listener: StateListener) {
    this.listeners.add(listener);
    // Notify immediately with initial state
    listener(this.currentState, this.previousState);
  }

  public removeListener(listener: StateListener) {
    this.listeners.delete(listener);
  }

  public transition(event: ConversationEvent): boolean {
    const nextState = this.getNextState(this.currentState, event);
    if (!nextState) {
      console.warn(`[ui-state-machine] Invalid transition from ${this.currentState} with event ${event.type}`);
      return false;
    }

    this.previousState = this.currentState;
    this.currentState = nextState;

    this.notify();
    return true;
  }

  private getNextState(current: ConversationState, event: ConversationEvent): ConversationState | null {
    // RESET is always valid and moves the machine back to idle
    if (event.type === 'RESET') {
      return 'idle';
    }

    switch (current) {
      case 'idle':
        if (event.type === 'SEND') return 'sending';
        break;

      case 'sending':
        if (event.type === 'CONNECT') return 'connecting';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'connecting':
        if (event.type === 'CONNECTED') return 'waiting';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'waiting':
        if (event.type === 'SHOW_TYPING') return 'typing';
        if (event.type === 'RECEIVE_TOKEN') return 'streaming';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'typing':
        if (event.type === 'RECEIVE_TOKEN') return 'streaming';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'streaming':
        if (event.type === 'RECEIVE_TOKEN') return 'streaming';
        if (event.type === 'COMPLETE_STREAM') return 'completed';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'completed':
        if (event.type === 'SEND') return 'sending';
        break;

      case 'failed':
        if (event.type === 'RETRY') return 'sending';
        if (event.type === 'RECONNECT') return 'reconnecting';
        if (event.type === 'SEND') return 'sending';
        break;

      case 'reconnecting':
        if (event.type === 'CONNECTED') return 'waiting';
        if (event.type === 'FAIL_STREAM') return 'failed';
        if (event.type === 'CANCEL_STREAM') return 'cancelled';
        break;

      case 'cancelled':
        if (event.type === 'SEND') return 'sending';
        break;
    }

    return null;
  }

  private notify() {
    for (const listener of this.listeners) {
      try {
        listener(this.currentState, this.previousState);
      } catch (err) {
        console.error('[ui-state-machine] Listener callback failed:', err);
      }
    }
  }
}
