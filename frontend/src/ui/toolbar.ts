import type { App } from '../app';

class Toolbar {
  _app: App;
  _el: HTMLElement | null;
  _saveBtn: HTMLButtonElement | null = null;
  _addBtn: HTMLButtonElement | null = null;
  _deleteBtn: HTMLButtonElement | null = null;
  _buildBtn: HTMLButtonElement | null = null;
  _zoomInBtn: HTMLButtonElement | null = null;
  _zoomOutBtn: HTMLButtonElement | null = null;
  _fitBtn: HTMLButtonElement | null = null;
  _typesBtn: HTMLButtonElement | null = null;

  constructor(app: App) {
    this._app = app;
    this._el = null;
  }

  init(container: HTMLElement): void {
    this._el = container;

    this._addButton('New', () => this._app.showNewProjectDialog());
    this._addButton('Open', () => this._app.showOpenProjectDialog());
    this._saveBtn = this._addButton('Save', () => this._app.saveCurrentGraph());
    this._addSeparator();
    this._addBtn = this._addButton('Add Subgraph', () => this._app.addSubgraphNode());
    this._deleteBtn = this._addButton('Delete', () => this._app.deleteSelectedNodes());
    this._addSeparator();
    this._zoomInBtn = this._addButton('Zoom In', () => this._app.zoomIn());
    this._zoomOutBtn = this._addButton('Zoom Out', () => this._app.zoomOut());
    this._fitBtn = this._addButton('Fit', () => this._app.zoomToFit());
    this._addSeparator();
    this._buildBtn = this._addButton('Build', () => this._app.showBuildDialog());
    this._typesBtn = this._addButton('Types', () => this._app.showTypeEditor());
    this._updateButtonStates();
  }

  _addButton(label: string, onClick: () => void): HTMLButtonElement {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    this._el!.appendChild(btn);
    return btn;
  }

  _addSeparator(): void {
    const sep = document.createElement('span');
    sep.className = 'separator';
    this._el!.appendChild(sep);
  }

  _updateButtonStates(): void {
    const hasProject = this._app._project && this._app._project.isOpen();
    const hasGraph = hasProject && this._app._graphManager && this._app._graphManager._graph;
    const hasSelection = hasGraph && this._app._canvas &&
      Object.keys(this._app._canvas.selected_nodes || {}).length > 0;

    if (this._saveBtn) this._saveBtn.disabled = !hasGraph;
    if (this._addBtn) this._addBtn.disabled = !hasGraph;
    if (this._deleteBtn) this._deleteBtn.disabled = !hasSelection;
    if (this._buildBtn) this._buildBtn.disabled = !hasGraph;
    if (this._zoomInBtn) this._zoomInBtn.disabled = !hasProject;
    if (this._zoomOutBtn) this._zoomOutBtn.disabled = !hasProject;
    if (this._fitBtn) this._fitBtn.disabled = !hasProject;
    if (this._typesBtn) this._typesBtn.disabled = !hasProject;
  }

  refresh(): void {
    this._updateButtonStates();
  }
}

export { Toolbar };
