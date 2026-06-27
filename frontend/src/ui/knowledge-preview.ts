export class KnowledgePreview {
  /**
   * Show a fullscreen floating overlay with merged knowledge text.
   * @param title  Entity path label (e.g., "Port clk · top/top.yaml")
   * @param content  The full merged knowledge text to display
   */
  static show(title: string, content: string): void {
    const overlay = document.createElement('div');
    overlay.style.cssText =
      'position:fixed; top:0; left:0; right:0; bottom:0;' +
      'background:rgba(0,0,0,0.7); z-index:10000;' +
      'display:flex; align-items:center; justify-content:center;';

    const box = document.createElement('div');
    box.style.cssText =
      'background:#1e1e1e; border:1px solid #444; border-radius:8px;' +
      'max-width:800px; width:90vw; max-height:80vh;' +
      'display:flex; flex-direction:column; overflow:hidden;';

    // Header bar
    const header = document.createElement('div');
    header.style.cssText =
      'display:flex; align-items:center; gap:12px;' +
      'padding:10px 16px; border-bottom:1px solid #333; flex-shrink:0;';
    const titleEl = document.createElement('span');
    titleEl.style.cssText = 'flex:1; font-size:14px; font-weight:600; color:#ddd;';
    titleEl.textContent = '\u270E Knowledge Preview \u2014 ' + title;

    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy';
    copyBtn.style.cssText =
      'padding:4px 12px; font-size:12px; background:#3a3a3a; color:#ccc;' +
      'border:1px solid #555; border-radius:4px; cursor:pointer;';
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
      } catch {
        copyBtn.textContent = 'Failed';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
      }
    });

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '\u2715 Close';
    closeBtn.style.cssText =
      'padding:4px 12px; font-size:12px; background:#3a3a3a; color:#ccc;' +
      'border:1px solid #555; border-radius:4px; cursor:pointer;';
    closeBtn.addEventListener('click', () => KnowledgePreview._close(overlay));

    header.appendChild(titleEl);
    header.appendChild(copyBtn);
    header.appendChild(closeBtn);

    // Content area
    const contentEl = document.createElement('pre');
    contentEl.style.cssText =
      'flex:1; overflow:auto; padding:16px; margin:0;' +
      'font-family:Consolas,monospace; font-size:12px; line-height:1.6;' +
      'color:#ccc; white-space:pre-wrap; word-break:break-word;';
    contentEl.textContent = content;

    box.appendChild(header);
    box.appendChild(contentEl);
    overlay.appendChild(box);

    // Close on backdrop click
    overlay.addEventListener('click', (e: MouseEvent) => {
      if (e.target === overlay) KnowledgePreview._close(overlay);
    });

    // Close on Escape
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        KnowledgePreview._close(overlay);
        document.removeEventListener('keydown', onKey);
      }
    };
    document.addEventListener('keydown', onKey);

    document.body.appendChild(overlay);
  }

  private static _close(overlay: HTMLDivElement): void {
    overlay.remove();
  }
}
