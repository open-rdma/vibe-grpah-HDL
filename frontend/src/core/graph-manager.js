class GraphManager {
  constructor(typeSystem) {
    this._typeSystem = typeSystem;
    this._graph = null;
    this._canvas = null;
  }

  setCanvas(canvas) {
    this._canvas = canvas;
    this._graph = canvas.graph;
  }

  newGraph(name) {
    this._graph.clear();
    this._graph.extra = { name: name };
    if (this._canvas) {
      this._canvas.draw(true, true);
    }
    return this._graph;
  }

  async loadGraph(path) {
    const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(path)}`);
    if (!resp.ok) throw new Error('Failed to load graph');
    const { data } = await resp.json();

    this._graph.clear();

    // Add module instance nodes
    const nodes = data.nodes || [];
    const nodeMap = {};
    for (const n of nodes) {
      const node = this._createNodeFromData(n);
      nodeMap[n.id] = node;
    }

    // Add connections
    const connections = data.connections || [];
    for (const conn of connections) {
      this._addConnection(conn, nodeMap);
    }

    this._graph.extra = {
      path: path,
      meta: data.meta || {},
      properties: data.properties || {},
      ports: data.ports || []
    };

    if (this._canvas) {
      this._canvas.draw(true, true);
    }

    return this._graph;
  }

  _createNodeFromData(nodeData) {
    const node = LiteGraph.createNode('rtl/module');
    node.title = nodeData.id;
    node._module_ref = nodeData.ref || '';
    node._module_data = nodeData;
    node.properties = nodeData.properties || {};

    // Load ref module's port list if available (async, but we do best-effort)
    if (nodeData.ref) {
      this._loadRefPorts(node, nodeData.ref);
    }

    this._graph.add(node);
    return node;
  }

  async _loadRefPorts(node, refPath) {
    try {
      const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(refPath)}`);
      if (!resp.ok) return;
      const { data } = await resp.json();
      node._subgraph_data = data;
      node.setPortsFromData(data);
      if (this._canvas) {
        this._canvas.draw(true, true);
      }
    } catch (e) {
      console.warn('Failed to load ref ports for', refPath, e);
    }
  }

  _addConnection(conn, nodeMap) {
    const fromNode = nodeMap[conn.from.node];
    const fromPort = this._findPortIndex(fromNode, 'outputs', conn.from.port);
    if (fromNode && fromPort >= 0) {
      for (const to of conn.to) {
        const toNode = nodeMap[to.node];
        const toPort = this._findPortIndex(toNode, 'inputs', to.port);
        if (toNode && toPort >= 0) {
          fromNode.connect(fromPort, toNode, toPort);
        }
      }
    }
  }

  _findPortIndex(node, slotType, portName) {
    const slots = node[slotType] || [];
    for (let i = 0; i < slots.length; i++) {
      if (slots[i].name === portName) return i;
    }
    return -1;
  }

  async saveGraph(path) {
    const yaml = this.toYAML();
    const resp = await fetch('/api/graph/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path, data: yaml })
    });
    if (!resp.ok) throw new Error('Failed to save graph');
    this._graph.extra.path = path;
    return true;
  }

  toYAML() {
    const data = {
      meta: this._graph.extra.meta || { name: '', description: '', test_method: '' },
      properties: this._graph.extra.properties || {},
      ports: this._graph.extra.ports || [],
      nodes: [],
      connections: []
    };

    // Serialize nodes
    for (const node of this._graph._nodes) {
      if (node.type === 'rtl/module') {
        data.nodes.push({
          id: node.title,
          ref: node._module_ref || '',
          description: node._module_data ? node._module_data.description : '',
          properties: node.properties || {}
        });
      }
    }

    // Serialize connections
    const linkMap = {};
    for (const node of this._graph._nodes) {
      for (const input of (node.inputs || [])) {
        if (input.link !== undefined && input.link !== null) {
          const link = this._graph.links[input.link];
          if (link) {
            const key = `${link.origin_id}:${link.origin_slot}`;
            if (!linkMap[key]) linkMap[key] = [];
            linkMap[key].push({ node: node.title || String(node.id), port: input.name });
          }
        }
      }
    }
    for (const [fromKey, toList] of Object.entries(linkMap)) {
      const [fromId, fromSlot] = fromKey.split(':');
      const fromNode = this._graph._nodes.find(n => String(n.id) === fromId);
      data.connections.push({
        from: { node: fromNode ? fromNode.title : fromId, port: fromNode ? fromNode.outputs[parseInt(fromSlot)].name : fromSlot },
        to: toList
      });
    }

    return data;
  }
}

export { GraphManager };
