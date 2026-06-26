class TypeEditor {
  constructor(typeSystem, onClose) {
    this._ts = typeSystem;
    this._onClose = onClose;
  }

  show() {
    this._overlay = document.createElement('div');
    this._overlay.className = 'dialog-overlay';

    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    dialog.style.width = '500px';
    dialog.innerHTML = '<h3>Type Definitions</h3>';

    const list = document.createElement('div');
    list.style.cssText = 'max-height:300px; overflow-y:auto; margin:8px 0;';

    const types = this._ts.getTypes();
    for (const [name, def] of Object.entries(types)) {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #333;';
      row.innerHTML = `<span><strong>${name}</strong> \u2014 ${def.description || ''}</span>`;
      const delBtn = document.createElement('button');
      delBtn.textContent = '\u00d7';
      delBtn.style.cssText = 'background:#a33; border:none; color:#fff; padding:2px 6px; cursor:pointer; border-radius:2px;';
      delBtn.addEventListener('click', () => {
        this._ts.removeType(name);
        dialog.remove();
        this.show();
      });
      row.appendChild(delBtn);
      list.appendChild(row);
    }
    dialog.appendChild(list);

    const addForm = document.createElement('div');
    addForm.style.cssText = 'margin-top:8px; display:flex; gap:4px;';
    const nameInput = document.createElement('input');
    nameInput.placeholder = 'Type name';
    nameInput.style.cssText = 'flex:1; background:#2d2d2d; border:1px solid #444; color:#ccc; padding:4px;';
    const descInput = document.createElement('input');
    descInput.placeholder = 'Description';
    descInput.style.cssText = 'flex:1; background:#2d2d2d; border:1px solid #444; color:#ccc; padding:4px;';
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add';
    addBtn.addEventListener('click', () => {
      if (nameInput.value) {
        this._ts.addType(nameInput.value, { description: descInput.value, category: 'user' });
        dialog.remove();
        this.show();
      }
    });
    addForm.appendChild(nameInput);
    addForm.appendChild(descInput);
    addForm.appendChild(addBtn);
    dialog.appendChild(addForm);

    const actions = document.createElement('div');
    actions.className = 'dialog-actions';
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.addEventListener('click', async () => {
      await this._save();
      this._close();
    });
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.addEventListener('click', () => this._close());
    actions.appendChild(saveBtn);
    actions.appendChild(closeBtn);
    dialog.appendChild(actions);

    this._overlay.appendChild(dialog);
    document.body.appendChild(this._overlay);
  }

  async _save() {
    try {
      await fetch('/api/types/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ types: this._ts.getTypes() })
      });
      showToast('Types saved');
    } catch (e) {
      showToast('Failed to save types: ' + e.message, 'error');
    }
  }

  _close() {
    if (this._overlay) this._overlay.remove();
    if (this._onClose) this._onClose();
  }
}

export { TypeEditor };
