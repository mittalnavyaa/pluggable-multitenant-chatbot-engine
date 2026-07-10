// packages/chatbot-ui/src/streaming/stream-parser.ts

export interface StreamingTextChunk {
  event: 'text';
  text: string;
}

export interface StreamingDoneChunk {
  event: 'done';
  message_id: string;
}

export interface StreamingErrorChunk {
  event: 'error';
  error: string;
}

export type StreamingChunk = StreamingTextChunk | StreamingDoneChunk | StreamingErrorChunk;

export class StreamParser {
  /**
   * Parses a single line from the SSE stream.
   * Returns a StreamingChunk if it is a valid data event, or null otherwise.
   */
  public parseLine(line: string): StreamingChunk | null {
    const trimmed = line.trim();
    if (!trimmed) return null;
    if (trimmed.startsWith(':')) return null; // SSE Heartbeat/comment

    if (trimmed.startsWith('data:')) {
      const dataValue = trimmed.substring(5).trim();
      if (dataValue === '[DONE]') {
        return { event: 'done', message_id: '' };
      }
      try {
        const parsed = JSON.parse(dataValue);
        if (parsed && typeof parsed === 'object' && 'event' in parsed) {
          return parsed as StreamingChunk;
        }
      } catch (err) {
        // Fallback: treat as raw text chunk if JSON parsing fails
        return { event: 'text', text: dataValue };
      }
    }
    return null;
  }
}
