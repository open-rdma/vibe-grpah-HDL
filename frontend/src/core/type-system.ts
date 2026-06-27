import type { TypeDefinition } from '../types/graph-types';
import { API } from '../services/api';
import { showToast } from '../ui/toast';

class TypeSystem {
  private _types: Record<string, TypeDefinition> = {};

  async loadFromServer(): Promise<void> {
    try {
      const data = await API.listTypes();
      this._types = data.types || {};
    } catch (e: any) {
      showToast('Failed to load type definitions from server', 'error');
    }
  }

  getTypes(): Record<string, TypeDefinition> {
    return this._types;
  }

  getType(name: string): TypeDefinition | null {
    return this._types[name] || null;
  }

  addType(name: string, definition: TypeDefinition): void {
    this._types[name] = definition;
  }

  removeType(name: string): void {
    delete this._types[name];
  }

  areCompatible(typeA: string, typeB: string): boolean {
    if (!typeA || !typeB) return true;
    if (typeA === typeB) return true;

    // Parse bus types like logic[7:0]
    const parse = (t: string): { base: string; width?: number } => {
      const m = t.match(/^(\w+)(?:\[(\d+):(\d+)\])?$/);
      if (!m) return { base: t };
      return { base: m[1], width: Math.abs(parseInt(m[2]) - parseInt(m[3])) + 1 };
    };

    const pa = parse(typeA);
    const pb = parse(typeB);
    if (pa.base !== pb.base) return false;
    if (pa.width && pb.width && pa.width !== pb.width) return false;
    return true;
  }
}

export { TypeSystem };
