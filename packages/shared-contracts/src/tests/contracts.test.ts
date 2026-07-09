// packages/shared-contracts/src/tests/contracts.test.ts

import { PayloadValidator } from '../validation';

describe('Shared API Contracts Validation Suite', () => {
  describe('WidgetInitRequest payload checks', () => {
    test('should pass with valid bot_id string', () => {
      const valid = { bot_id: 'bot-12345' };
      const res = PayloadValidator.validateWidgetInitRequest(valid);
      expect(res.bot_id).toBe('bot-12345');
    });

    test('should throw error on missing bot_id', () => {
      const invalid = {};
      expect(() => {
        PayloadValidator.validateWidgetInitRequest(invalid);
      }).toThrow('bot_id');
    });
  });

  describe('ChatRequest validation rules', () => {
    test('should validate normal chat payload', () => {
      const payload = {
        bot_id: 'bot_123',
        conversation_id: 'conv_abc',
        prompt: 'How to build an SDK?',
        stream: true
      };
      const res = PayloadValidator.validateChatRequest(payload);
      expect(res.bot_id).toBe('bot_123');
      expect(res.conversation_id).toBe('conv_abc');
      expect(res.prompt).toBe('How to build an SDK?');
      expect(res.stream).toBe(true);
    });

    test('should fail when prompt exceeds character limit', () => {
      const longPrompt = 'a'.repeat(4001);
      const payload = {
        bot_id: 'bot_123',
        conversation_id: 'conv_abc',
        prompt: longPrompt,
        stream: false
      };
      expect(() => {
        PayloadValidator.validateChatRequest(payload, 4000);
      }).toThrow('exceeds the maximum permitted length');
    });

    test('should fail when conversation_id is missing', () => {
      const payload = {
        bot_id: 'bot_123',
        prompt: 'test prompt',
        stream: false
      };
      expect(() => {
        PayloadValidator.validateChatRequest(payload);
      }).toThrow('conversation_id');
    });
  });

  describe('Utility validations regex matches', () => {
    test('should validate hex/rgb color strings formats', () => {
      expect(PayloadValidator.validateColorString('#fff')).toBe(true);
      expect(PayloadValidator.validateColorString('#abcdef')).toBe(true);
      expect(PayloadValidator.validateColorString('rgb(255, 255, 0)')).toBe(true);
      expect(PayloadValidator.validateColorString('rgba(0, 0, 0, 0.5)')).toBe(true);
      expect(PayloadValidator.validateColorString('invalid')).toBe(false);
    });

    test('should validate UUID schema structure', () => {
      expect(PayloadValidator.validateUUID('3f9f9db1-d419-4a00-ab64-77e8fb1cb8ba')).toBe(true);
      expect(PayloadValidator.validateUUID('invalid-uuid')).toBe(false);
    });
  });
});
