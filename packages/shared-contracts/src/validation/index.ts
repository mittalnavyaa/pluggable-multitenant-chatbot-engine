// packages/shared-contracts/src/validation/index.ts

import { type ChatRequest, type WidgetInitRequest } from '../types';

export class PayloadValidator {
  private static readonly UUID_REGEX = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
  private static readonly COLOR_HEX_REGEX = /^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;
  private static readonly COLOR_RGB_REGEX = /^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$/;
  private static readonly COLOR_RGBA_REGEX = /^rgba\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(0|1|0?\.\d+)\s*\)$/;

  /**
   * Validates inbound widget initialization queries bot ID parameter.
   */
  public static validateWidgetInitRequest(payload: any): WidgetInitRequest {
    if (!payload || typeof payload !== 'object') {
      throw new Error('Payload must be a JSON object');
    }
    if (typeof payload.bot_id !== 'string' || !payload.bot_id.trim()) {
      throw new Error('Parameter "bot_id" is required and must be a non-empty string');
    }
    return {
      bot_id: payload.bot_id.trim()
    };
  }

  /**
   * Validates inbound chat query parameters, enforcing limits on prompt length.
   */
  public static validateChatRequest(payload: any, maxPromptLength = 4000): ChatRequest {
    if (!payload || typeof payload !== 'object') {
      throw new Error('Payload must be a JSON object');
    }
    if (typeof payload.bot_id !== 'string' || !payload.bot_id.trim()) {
      throw new Error('Parameter "bot_id" is required and must be a non-empty string');
    }
    if (typeof payload.conversation_id !== 'string' || !payload.conversation_id.trim()) {
      throw new Error('Parameter "conversation_id" is required and must be a non-empty string');
    }
    if (typeof payload.prompt !== 'string' || !payload.prompt.trim()) {
      throw new Error('Parameter "prompt" is required and must be a non-empty string');
    }
    if (payload.prompt.length > maxPromptLength) {
      throw new Error(`Parameter "prompt" exceeds the maximum permitted length of ${maxPromptLength} characters`);
    }
    if (payload.stream !== undefined && typeof payload.stream !== 'boolean') {
      throw new Error('Parameter "stream" must be a boolean value');
    }

    return {
      bot_id: payload.bot_id.trim(),
      conversation_id: payload.conversation_id.trim(),
      prompt: payload.prompt.trim(),
      stream: payload.stream === true,
      metadata: typeof payload.metadata === 'object' ? payload.metadata : undefined
    };
  }

  /**
   * Validates hex, rgb, or rgba color formatting.
   */
  public static validateColorString(color: string): boolean {
    if (typeof color !== 'string') return false;
    const trimmed = color.trim();
    return (
      this.COLOR_HEX_REGEX.test(trimmed) ||
      this.COLOR_RGB_REGEX.test(trimmed) ||
      this.COLOR_RGBA_REGEX.test(trimmed)
    );
  }

  /**
   * Asserts string complies with UUID schema patterns.
   */
  public static validateUUID(id: string): boolean {
    if (typeof id !== 'string') return false;
    return this.UUID_REGEX.test(id.trim());
  }
}
