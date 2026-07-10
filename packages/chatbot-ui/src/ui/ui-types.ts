// packages/chatbot-ui/src/ui/ui-types.ts

import { type ConversationState } from '../types';

export type ConversationEvent =
  | { type: 'SEND' }
  | { type: 'CONNECT' }
  | { type: 'CONNECTED' }
  | { type: 'SHOW_TYPING' }
  | { type: 'RECEIVE_TOKEN' }
  | { type: 'COMPLETE_STREAM' }
  | { type: 'FAIL_STREAM'; error: string }
  | { type: 'CANCEL_STREAM' }
  | { type: 'RETRY' }
  | { type: 'RECONNECT' }
  | { type: 'RESET' };

export type StateListener = (state: ConversationState, previousState: ConversationState) => void;
