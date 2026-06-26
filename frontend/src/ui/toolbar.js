class Toolbar {
  constructor(app) {
    this._app = app;
  }

  init(container) {
    this._el = container;

    this._addButton('New', () => this._app.showNewProjectDialog());
    this._addButton('Open', () => this._app.showOpenProjectDialog());
    this._addButton('Save', () => this._app.saveCurrentGraph());
    this._addSeparator();
    this._addButton('Add Subgraph', () => this._app.addSubgraphNode());
    this._addButton('Delete', () => this._app.deleteSelectedNodes());
    this._addSeparator();
    this._addButton('Zoom In', () => this._app.zoomIn());
    this._addButton('Zoom Out', () => this._app.zoomOut());
    this._addButton('Fit', () => this._app.zoomToFit());
    this._addSeparator();
    this._addButton('Build', () => this._app.showBuildDialog());
    this._addButton('Types', () => this._app.showTypeEditor());
  }

  _addButton(label, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    this._el.appendChild(btn);
    return btn;
  }

  _addSeparator() {
    const sep = document.createElement('span');
    sep.className = 'separator';
    this._el.appendChild(sep);
  }
}

export { Toolbar };
