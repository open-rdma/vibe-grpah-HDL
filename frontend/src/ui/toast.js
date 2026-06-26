function showToast(message, type) {
  type = type || 'info';
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(function() {
    el.remove();
  }, 3000);
}

window.__showToast = showToast;
export { showToast };
