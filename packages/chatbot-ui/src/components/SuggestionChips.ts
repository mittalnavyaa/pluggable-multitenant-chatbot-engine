// packages/chatbot-ui/src/components/SuggestionChips.ts

export class SuggestionChips {
  private element: HTMLDivElement;

  constructor(
    private parentContainer: HTMLElement,
    private onChipClick: (text: string) => void
  ) {
    this.element = document.createElement('div');
    this.element.id = 'envoy-suggestions';
    this.element.className = 'hidden px-4 py-2.5 bg-lt-bg dark:bg-dk-bg flex flex-col gap-1.5 border-t border-lt-border/30 dark:border-dk-border/30 select-none';
    this.parentContainer.appendChild(this.element);
  }

  public setQuestions(questions: string[], primaryColor: string) {
    this.element.innerHTML = '';
    if (!questions || questions.length === 0) {
      this.hide();
      return;
    }

    questions.forEach(text => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'envoy-suggest-btn text-left px-3 py-2 rounded-lg border border-lt-border dark:border-dk-border bg-white dark:bg-dk-surface text-lt-text dark:text-dk-text text-xs hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer transition-all duration-200 border-l-4 font-medium shadow-sm hover:scale-[1.01] active:scale-[0.99]';
      btn.style.borderLeftColor = primaryColor || '#2563eb';
      btn.textContent = text;
      
      btn.addEventListener('click', () => {
        this.onChipClick(text);
      });

      this.element.appendChild(btn);
    });

    this.show();
  }

  public show() {
    this.element.classList.remove('hidden');
  }

  public hide() {
    this.element.classList.add('hidden');
  }

  public getElement() { return this.element; }
}
