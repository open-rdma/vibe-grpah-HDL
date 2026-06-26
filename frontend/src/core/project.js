class Project {
  constructor() {
    this._config = null;
    this._trees = [];
    this._projectPath = '';
  }

  async create(path, name) {
    const resp = await fetch('/api/project/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, name })
    });
    if (!resp.ok) throw new Error('Failed to create project');
    const data = await resp.json();
    this._config = data.project;
    this._trees = data.trees;
    this._projectPath = path;
  }

  async open(path) {
    const resp = await fetch('/api/project/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    if (!resp.ok) throw new Error('Failed to open project');
    const data = await resp.json();
    this._config = data.project;
    this._trees = data.trees;
    this._projectPath = path;
  }

  async save() {
    if (!this._config) throw new Error('No project open');
    const resp = await fetch('/api/project/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: this._config })
    });
    if (!resp.ok) throw new Error('Failed to save project');
  }

  getTrees() { return this._trees; }
  getConfig() { return this._config; }
  getPath() { return this._projectPath; }
  isOpen() { return !!this._config; }
}

export { Project };
