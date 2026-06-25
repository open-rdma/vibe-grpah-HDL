class TypeSystem {
  constructor() {
    this._types = {};
  }

  async loadFromServer() {
    try {
      const resp = await fetch('/api/types/list');
      const data = await resp.json();
      this._types = data.types || {};
    } catch (e) {
      console.warn('Failed to load types from server, using defaults', e);
    }
  }

  getTypes() {
    return this._types;
  }

  getType(name) {
    return this._types[name] || null;
  }

  addType(name, definition) {
    this._types[name] = definition;
  }

  removeType(name) {
    delete this._types[name];
  }

  areCompatible(typeA, typeB) {
    if (!typeA || !typeB) return true;
    if (typeA === typeB) return true;

    // Parse bus types like logic[7:0]
    const parse = (t) => {
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
