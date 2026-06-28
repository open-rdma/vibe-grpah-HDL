import { showToast } from './toast';
import { API } from '../services/api';
import type { TypeSystem } from '../core/type-system';

class TypeEditor {
  _ts: TypeSystem;
  _onClose: (() => void) | null;
  _overlay: HTMLDivElement | null;
  _dirty: boolean;

  constructor(typeSystem: TypeSystem, onClose?: () => void) {
    this._ts = typeSystem;
    this._onClose = onClose || null;
    this._overlay = null;
    this._dirty = false;
  }

  show(): void {
    this._overlay = document.createElement('div');
    this._overlay.className = 'dialog-overlay';

    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    dialog.style.width = '500px';
    dialog.innerHTML = '<h3>Type Definitions</h3>';

    const list = document.createElement('div');
    list.className = 'type-editor-list';
    this._renderList(list);
    dialog.appendChild(list);

    const addForm = document.createElement('div');
    addForm.className = 'type-editor-add-form';
    const nameInput = document.createElement('input');
    nameInput.placeholder = 'Type name';
    nameInput.className = 'type-editor-input';
    const descInput = document.createElement('input');
    descInput.placeholder = 'Description';
    descInput.className = 'type-editor-input';
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add';
    addBtn.addEventListener('click', () => {
      if (nameInput.value) {
        this._ts.addType(nameInput.value, { description: descInput.value, category: 'user' });
        nameInput.value = '';
        descInput.value = '';
        this._dirty = true;
        this._renderList(list);
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
      this._dirty = false;
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

  _renderList(list: HTMLElement): void {
    list.innerHTML = '';
    const types = this._ts.getTypes();
    for (const [name, def] of Object.entries(types)) {
      const row = document.createElement('div');
      row.className = 'type-editor-row';
      const strong = document.createElement('strong');
      strong.textContent = name;
      const span = document.createElement('span');
      span.appendChild(strong);
      span.appendChild(document.createTextNode(' \u2014 ' + (def.description || '')));
      row.appendChild(span);
      const delBtn = document.createElement('button');
      delBtn.textContent = '\u00d7';
      delBtn.className = 'type-editor-delete-btn';
      delBtn.addEventListener('click', () => {
        if (!confirm(`Delete type "${name}"?`)) return;
        this._ts.removeType(name);
        this._dirty = true;
        this._renderList(list);
      });
      row.appendChild(delBtn);
      list.appendChild(row);
    }
  }

  async _save(): Promise<void> {
    try {
      await API.saveTypes(this._ts.getTypes());
      showToast('Types saved');
    } catch (e: any) {
      showToast('Failed to save types: ' + e.message, 'error');
    }
  }

  _close(): void {
    if (this._dirty && !confirm('You have unsaved changes. Discard them?')) return;
    if (this._overlay) this._overlay.remove();
    if (this._onClose) this._onClose();
  }
}

export { TypeEditor };
