// packages/chatbot-ui/src/streaming/sse-client.ts

import { type SSEClientOptions, type StreamStatus } from './stream-types';
import { StreamReader } from './stream-reader';
import { StreamParser } from './stream-parser';

export class SSEClient {
  private status: StreamStatus = 'idle';
  private abortController: AbortController | null = null;
  private retryCount = 0;
  private isCancelled = false;

  constructor(private readonly options: SSEClientOptions) {}

  public getStatus(): StreamStatus {
    return this.status;
  }

  private setStatus(status: StreamStatus, error?: string) {
    this.status = status;
    if (this.options.onStatusChange) {
      this.options.onStatusChange(status, error);
    }
  }

  /**
   * Establishes the SSE stream connection.
   */
  public async connect(): Promise<void> {
    this.isCancelled = false;
    this.retryCount = 0;
    await this.attemptConnect();
  }

  private async attemptConnect(): Promise<void> {
    if (this.isCancelled) return;

    this.setStatus('connecting');
    this.abortController = new AbortController();

    const botId = encodeURIComponent(this.options.botId);
    const prompt = encodeURIComponent(this.options.prompt);
    const url = `${this.options.apiBase}/api/v1/chat/stream?bot_id=${botId}&prompt=${prompt}`;

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          ...(this.options.headers || {})
        },
        signal: this.abortController.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null or not readable.');
      }

      // Connection succeeded, reset retries
      this.retryCount = 0;

      const reader = response.body.getReader();
      const streamReader = new StreamReader();
      const parser = new StreamParser();

      await streamReader.read(reader, (line) => {
        if (this.isCancelled) return;

        const chunk = parser.parseLine(line);
        if (!chunk) return;

        if (chunk.event === 'text') {
          if (this.status !== 'streaming') {
            this.setStatus('streaming');
          }
          if (this.options.onToken) {
            this.options.onToken(chunk.text);
          }
        } else if (chunk.event === 'done') {
          this.setStatus('completed');
          if (this.options.onComplete) {
            this.options.onComplete(chunk.message_id);
          }
        } else if (chunk.event === 'error') {
          this.handleFailure(new Error(chunk.error));
        }
      });

      // If streaming finished without done chunk, finalize state
      if (this.status === 'streaming') {
        this.setStatus('completed');
        if (this.options.onComplete) {
          this.options.onComplete(`msg_end_${Date.now()}`);
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError' || this.isCancelled) {
        return; // Aborted by user
      }
      this.handleFailure(err);
    }
  }

  private handleFailure(error: Error) {
    const maxRetries = this.options.maxRetries ?? 3;
    const retryInterval = this.options.retryInterval ?? 1000;

    if (this.retryCount < maxRetries) {
      this.retryCount++;
      const backoff = retryInterval * Math.pow(2, this.retryCount - 1);
      console.warn(`[sse-client] Connection lost: ${error.message}. Retrying in ${backoff}ms... (${this.retryCount}/${maxRetries})`);
      
      setTimeout(() => {
        this.attemptConnect();
      }, backoff);
    } else {
      this.setStatus('failed', error.message);
      if (this.options.onError) {
        this.options.onError(error.message);
      }
    }
  }

  /**
   * Disconnects the stream client.
   */
  public disconnect() {
    this.isCancelled = true;
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    this.setStatus('idle');
  }
}
