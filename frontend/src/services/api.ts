import type { APIResponse, GraphData } from '../types/graph-types';

const API = {
  // Project
  createProject(path: string, name: string): Promise<APIResponse> {
    return this._post('/api/project/create', { path, name });
  },
  openProject(path: string): Promise<APIResponse> {
    return this._post('/api/project/open', { path });
  },
  saveProject(config: Record<string, any>): Promise<APIResponse> {
    return this._post('/api/project/save', { config });
  },
  closeProject(): Promise<APIResponse> {
    return this._post('/api/project/close', {});
  },
  createTree(name: string): Promise<APIResponse> {
    return this._post('/api/project/tree/create', { name });
  },

  // Graph
  loadGraph(path: string): Promise<{ path: string; data: GraphData }> {
    return this._get(`/api/graph/load?path=${encodeURIComponent(path)}`);
  },
  saveGraph(path: string, data: GraphData): Promise<APIResponse> {
    return this._post('/api/graph/save', { path, data });
  },
  deleteGraph(path: string): Promise<APIResponse> {
    return this._del(`/api/graph/delete?path=${encodeURIComponent(path)}`);
  },

  // Types
  listTypes(): Promise<{ types: Record<string, any> }> {
    return this._get('/api/types/list');
  },
  saveTypes(types: Record<string, any>): Promise<APIResponse> {
    return this._post('/api/types/save', { types });
  },

  // Build
  startBuild(targetNode: string, scope: string, mode: string, includeTestbench: boolean, knowledge: string): Promise<{ task_id: string }> {
    return this._post('/api/build', { target_node: targetNode, scope, mode, include_testbench: includeTestbench, knowledge });
  },
  getBuildStatus(taskId: string): Promise<{ status: string; error?: string }> {
    return this._get(`/api/build/status/${taskId}`);
  },

  // Unified fetch helper with timeout
  async _fetch<T = any>(method: string, url: string, body?: Record<string, any>): Promise<T> {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 30000);
    try {
      const opts: RequestInit = { method, signal: ctrl.signal };
      if (body) {
        opts.headers = { 'Content-Type': 'application/json' };
        opts.body = JSON.stringify(body);
      }
      const resp = await fetch(url, opts);
      if (!resp.ok) throw new Error(`${method} ${url} failed: ${resp.status}`);
      return resp.json();
    } finally {
      clearTimeout(timer);
    }
  },
  _get<T = any>(url: string): Promise<T> { return this._fetch('GET', url); },
  _post<T = any>(url: string, body: Record<string, any>): Promise<T> { return this._fetch('POST', url, body); },
  _del<T = any>(url: string): Promise<T> { return this._fetch('DELETE', url); }
};

export { API };
