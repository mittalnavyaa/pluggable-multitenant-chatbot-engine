// packages/chatbot-ui/src/streaming/stream-reader.ts

export class StreamReader {
  private decoder = new TextDecoder();
  private buffer = '';

  /**
   * Reads from a ReadableStream reader, decodes the chunks, and streams complete lines to onLine.
   */
  public async read(
    reader: ReadableStreamDefaultReader<Uint8Array>,
    onLine: (line: string) => void
  ): Promise<void> {
    try {
      while (true) {
        const { done, value } = await reader.read();

        // Decode value. stream: true ensures decoder state is maintained for partial sequences.
        const chunk = value ? this.decoder.decode(value, { stream: true }) : '';
        this.buffer += chunk;

        let newlineIndex;
        while ((newlineIndex = this.buffer.indexOf('\n')) !== -1) {
          const line = this.buffer.slice(0, newlineIndex);
          this.buffer = this.buffer.slice(newlineIndex + 1);
          onLine(line);
        }

        if (done) {
          // Flush any residual decoder buffer
          const finalDecode = this.decoder.decode();
          if (finalDecode) {
            this.buffer += finalDecode;
          }
          if (this.buffer) {
            onLine(this.buffer);
            this.buffer = '';
          }
          break;
        }
      }
    } finally {
      // Release stream lock
      try {
        reader.releaseLock();
      } catch {
        // Safe to ignore if stream is already closed
      }
    }
  }
}
