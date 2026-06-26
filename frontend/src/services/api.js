const API = {
  // Project
  createProject(path, name) {
    return this._post('/api/project/create', { path, name });
  },
  openProject(path) {
    return this._post('/api/project/open', { path });
  },
  saveProject(config) {
    return this._post('/api/project/save', { config });
  },
  getTrees() {
    return this._get('/api/project/trees');
  },
  createTree(name) {
    return this._post('/api/project/tree/create', { name });
  },

  // Graph
  loadGraph(path) {
    return this._get(`/api/graph/load?path=${encodeURIComponent(path)}`);
  },
  saveGraph(path, data) {
    return this._post('/api/graph/save', { path, data });
  },
  validateGraph(path) {
    return this._post('/api/graph/validate', { path });
  },
  deleteGraph(path) {
    return this._del(`/api/graph/delete?path=${encodeURIComponent(path)}`);
  },

  // Types
  listTypes() {
    return this._get('/api/types/list');
  },
  saveTypes(types) {
    return this._post('/api/types/save', { types });
  },
  checkTypes(from, to) {
    return this._get(`/api/types/check?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`);
  },

  // Build
  startBuild(targetNode, scope, mode, includeTestbench) {
    return this._post('/api/build', { target_node: targetNode, scope, mode, include_testbench: includeTestbench });
  },
  getBuildStatus(taskId) {
    return this._get(`/api/build/status/${taskId}`);
  },
  getBuildOutput(taskId) {
    return this._get(`/api/build/output/${taskId}`);
  },

  // Git
  commit(message) {
    return this._post('/api/git/commit', { message });
  },
  getGitLog(count) {
    return this._get(`/api/git/log?count=${count || 50}`);
  },
  checkoutGit(hash) {
    return this._post('/api/git/checkout', { hash });
  },

  // LLM Config
  getLLMConfig() {
    return this._get('/api/llm/config');
  },
  updateLLMConfig(config) {
    return this._post('/api/llm/config', config);
  },

  // Helpers
  async _get(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`GET ${url} failed: ${resp.status}`);
    return resp.json();
  },
  async _post(url, body) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!resp.ok) throw new Error(`POST ${url} failed: ${resp.status}`);
    return resp.json();
  },
  async _del(url) {
    const resp = await fetch(url, { method: 'DELETE' });
    if (!resp.ok) throw new Error(`DELETE ${url} failed: ${resp.status}`);
    return resp.json();
  }
};

export { API };
