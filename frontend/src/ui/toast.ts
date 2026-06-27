let _toasts: HTMLDivElement[] = [];

function showToast(message: string, type?: string): void {
  type = type || 'info';
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = message;
  _toasts.push(el);
  _reflowToasts();
  document.body.appendChild(el);
  setTimeout(function() {
    el.remove();
    _toasts = _toasts.filter(t => t !== el);
    _reflowToasts();
  }, 3000);
}

function _reflowToasts(): void {
  for (let i = 0; i < _toasts.length; i++) {
    _toasts[i].style.bottom = (40 + i * 32) + 'px';
  }
}

export { showToast };
