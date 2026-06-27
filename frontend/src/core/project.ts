import { API } from '../services/api';

class Project {
  private _config: Record<string, any> | null = null;
  private _trees: string[] = [];

  async create(path: string, name: string): Promise<void> {
    const data = await API.createProject(path, name);
    this._applyResponse(data);
  }

  async open(path: string): Promise<void> {
    const data = await API.openProject(path);
    this._applyResponse(data);
  }

  private _applyResponse(data: any): void {
    this._config = data.project;
    this._trees = data.trees;
  }

  async close(): Promise<void> {
    await API.closeProject();
    this._config = null;
    this._trees = [];
  }

  async save(): Promise<void> {
    if (!this._config) throw new Error('No project open');
    await API.saveProject(this._config);
  }

  getTrees(): string[] { return this._trees; }
  getConfig(): Record<string, any> | null { return this._config; }
  isOpen(): boolean { return !!this._config; }
}

export { Project };
