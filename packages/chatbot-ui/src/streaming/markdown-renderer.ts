// packages/chatbot-ui/src/streaming/markdown-renderer.ts

export class MarkdownRenderer {
  /**
   * Escape HTML helper to prevent XSS.
   */
  public static escapeHtml(html: string): string {
    return html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  /**
   * Safe incremental Markdown compiler.
   */
  public static render(markdown: string): string {
    if (!markdown) return '';

    const lines = markdown.split('\n');
    let html = '';
    let inCodeBlock = false;
    let codeLanguage = '';
    let codeContent: string[] = [];
    let inList: 'ul' | 'ol' | null = null;

    // Table parsing buffer
    let inTable = false;
    let tableRows: string[][] = [];

    const closeList = () => {
      if (inList) {
        const tag = inList;
        inList = null;
        return `</${tag}>`;
      }
      return '';
    };

    const closeTable = (force = false): string => {
      if (!inTable) return '';
      inTable = false;

      // Tables are only rendered as proper HTML tables if complete (contains header + separator + rows)
      if (tableRows.length >= 2 && !force) {
        let tableHtml = '<div class="overflow-x-auto my-2"><table class="min-w-full border-collapse border border-lt-border dark:border-dk-border text-xs">';
        
        // Header row
        const headerCols = tableRows[0] || [];
        tableHtml += '<thead><tr class="bg-slate-100 dark:bg-slate-800">';
        headerCols.forEach(col => {
          tableHtml += `<th class="border border-lt-border dark:border-dk-border px-3 py-1.5 font-semibold text-left">${this.renderInline(col)}</th>`;
        });
        tableHtml += '</tr></thead>';

        // Body rows
        if (tableRows.length > 2) {
          tableHtml += '<tbody>';
          for (let i = 2; i < tableRows.length; i++) {
            tableHtml += '<tr class="odd:bg-white even:bg-slate-50/50 dark:odd:bg-dk-surface dark:even:bg-dk-bg/30">';
            const cols = tableRows[i];
            for (let j = 0; j < headerCols.length; j++) {
              const val = cols[j] || '';
              tableHtml += `<td class="border border-lt-border dark:border-dk-border px-3 py-1.5">${this.renderInline(val)}</td>`;
            }
            tableHtml += '</tr>';
          }
          tableHtml += '</tbody>';
        }
        tableHtml += '</table></div>';
        tableRows = [];
        return tableHtml;
      } else if (force && tableRows.length > 0) {
        // If we are forcing a close (end of text) and have rows, render complete rows
        // or print as formatted rows if separator is valid
        const hasSeparator = tableRows.length >= 2 && tableRows[1].every(c => c.startsWith('-') || c === '');
        if (hasSeparator && tableRows.length > 2) {
          // Render as table
          inTable = true;
          const result = closeTable(false);
          return result;
        }
        
        // Fallback to text paragraphs
        const rawLines = tableRows.map(row => '| ' + row.join(' | ') + ' |').join('\n');
        tableRows = [];
        return `<p class="my-1.5 font-mono text-xs whitespace-pre bg-slate-50 dark:bg-dk-surface/50 p-2 border border-lt-border dark:border-dk-border rounded">${this.escapeHtml(rawLines)}</p>`;
      }
      tableRows = [];
      return '';
    };

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // --- Code Blocks ---
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          inCodeBlock = false;
          html += `<pre class="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto my-2 font-mono text-xs"><code class="language-${codeLanguage}">${this.escapeHtml(codeContent.join('\n'))}</code></pre>`;
          codeContent = [];
          codeLanguage = '';
        } else {
          inCodeBlock = true;
          codeLanguage = line.trim().substring(3).trim() || 'plaintext';
        }
        continue;
      }

      if (inCodeBlock) {
        codeContent.push(line);
        continue;
      }

      // --- Table Lines ---
      if (line.trim().startsWith('|')) {
        html += closeList();
        inTable = true;
        const cols = line.split('|')
          .map(c => c.trim())
          .filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
        tableRows.push(cols);
        continue;
      } else if (inTable) {
        html += closeTable();
      }

      // --- List Items ---
      const uListMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
      const oListMatch = line.match(/^(\s*)\d+\.\s+(.*)$/);

      if (uListMatch) {
        const content = uListMatch[2];
        if (inList !== 'ul') {
          html += closeList();
          inList = 'ul';
          html += '<ul class="list-disc pl-5 my-2 flex flex-col gap-1">';
        }
        html += `<li>${this.renderInline(content)}</li>`;
        continue;
      } else if (oListMatch) {
        const content = oListMatch[2];
        if (inList !== 'ol') {
          html += closeList();
          inList = 'ol';
          html += '<ol class="list-decimal pl-5 my-2 flex flex-col gap-1">';
        }
        html += `<li>${this.renderInline(content)}</li>`;
        continue;
      } else {
        html += closeList();
      }

      // --- Blank Line ---
      if (!line.trim()) {
        html += '<div class="h-2"></div>';
        continue;
      }

      // --- Headings ---
      const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
      if (headingMatch) {
        const level = headingMatch[1].length;
        const text = headingMatch[2];
        html += `<h${level} class="font-bold my-2 text-lt-text dark:text-dk-text ${
          level === 1 ? 'text-lg border-b border-lt-border dark:border-dk-border pb-1' : level === 2 ? 'text-base' : 'text-sm'
        }">${this.renderInline(text)}</h${level}>`;
        continue;
      }

      // --- Paragraph ---
      html += `<p class="my-1.5">${this.renderInline(line)}</p>`;
    }

    // --- Stream Safety Auto-Closure ---
    if (inCodeBlock) {
      html += `<pre class="bg-slate-900 text-slate-100 p-3 rounded-lg overflow-x-auto my-2 font-mono text-xs"><code class="language-${codeLanguage}">${this.escapeHtml(codeContent.join('\n'))}</code></pre>`;
    }

    if (inTable) {
      html += closeTable(true);
    }

    html += closeList();

    return html;
  }

  /**
   * Render inline syntax: Bold, Italics, Inline Code, and Links.
   */
  private static renderInline(text: string): string {
    let escaped = this.escapeHtml(text);

    // 1. Inline code: `code`
    escaped = escaped.replace(/`([^`]+)`/g, '<code class="bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-[11px] text-pink-600 dark:text-pink-400">$1</code>');

    // 2. Bold: **text**
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    escaped = escaped.replace(/__([^_]+)__/g, '<strong>$1</strong>');

    // 3. Italics: *text*
    escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    escaped = escaped.replace(/_([^_]+)_/g, '<em>$1</em>');

    // 4. Links: [text](url)
    escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 dark:text-blue-400 hover:underline font-medium">$1</a>');

    return escaped;
  }
}
