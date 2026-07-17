// packages/chatbot-ui/src/export/exporter.ts

import { type Message } from '../types';

export interface ConversationExporter {
  export(messages: Message[]): string;
  getMimeType(): string;
  getFileExtension(): string;
}

export class PlainTextExporter implements ConversationExporter {
  public export(messages: Message[]): string {
    return messages
      .map(msg => `[${msg.timestamp}] ${msg.sender === 'user' ? 'User' : 'Assistant'}: ${msg.text}`)
      .join('\n\n');
  }

  public getMimeType(): string {
    return 'text/plain;charset=utf-8';
  }

  public getFileExtension(): string {
    return 'txt';
  }
}

export class MarkdownExporter implements ConversationExporter {
  public export(messages: Message[]): string {
    return messages
      .map(msg => `### ${msg.sender === 'user' ? 'User' : 'Assistant'} (${msg.timestamp})\n\n${msg.text}`)
      .join('\n\n---\n\n');
  }

  public getMimeType(): string {
    return 'text/markdown;charset=utf-8';
  }

  public getFileExtension(): string {
    return 'md';
  }
}

export class JsonExporter implements ConversationExporter {
  public export(messages: Message[]): string {
    return JSON.stringify(messages, null, 2);
  }

  public getMimeType(): string {
    return 'application/json;charset=utf-8';
  }

  public getFileExtension(): string {
    return 'json';
  }
}

export class ExporterRegistry {
  private static exporters: Record<string, ConversationExporter> = {
    txt: new PlainTextExporter(),
    md: new MarkdownExporter(),
    json: new JsonExporter(),
  };

  public static getExporter(format: string): ConversationExporter {
    const exporter = this.exporters[format.toLowerCase()];
    if (!exporter) {
      throw new Error(`Unsupported export format: ${format}`);
    }
    return exporter;
  }
}
