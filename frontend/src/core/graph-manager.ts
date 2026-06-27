import type { GraphData } from '../types/graph-types';
import type { TypeSystem } from './type-system';
import { API } from '../services/api';
import { showToast } from '../ui/toast';

export function createEmptyGraphData(name: string = ''): GraphData {
  return {
    meta: { name, description: '', test_method: '' },
    properties: {},
    ports: [],
    nodes: [],
    connections: []
  };
}

class GraphManager {
  _typeSystem: TypeSystem;
  _graph: LGraph | null;
  _canvas: LGraphCanvas | null;
  _dirty: boolean;
  _stateCache: Map<string, GraphData>;

  constructor(typeSystem: TypeSystem) {
    this._typeSystem = typeSystem;
    this._graph = null;
    this._canvas = null;
    this._dirty = false;
    this._stateCache = new Map();
  }

  markDirty(): void {
    this._dirty = true;
  }

  markClean(): void {
    this._dirty = false;
  }

  isDirty(): boolean {
    return this._dirty;
  }

  /** True if any graph (current or cached) has unsaved changes. */
  hasAnyUnsavedChanges(): boolean {
    return this._dirty || this._stateCache.size > 0;
  }

  /** True if the graph at the given path has unsaved changes. */
  isGraphDirty(path: string): boolean {
    if (this._stateCache.has(path)) return true;
    const currentPath = this._graph?.extra?.path;
    if (currentPath === path && this._dirty) return true;
    return false;
  }

  setCanvas(canvas: LGraphCanvas | null): void {
    this._canvas = canvas;
    this._graph = canvas ? canvas.graph : null;
    if (this._graph) this._installDeleteGuard(this._graph);
  }

  /**
   * Re-sync _graph from the canvas. Call after openSubgraph/closeSubgraph,
   * which change canvas.graph via attachCanvas without going through setCanvas.
   */
  _syncFromCanvas(): void {
    if (!this._canvas) {
      this._graph = null;
      return;
    }
    this._graph = this._canvas.graph;
    if (this._graph) {
      this._installDeleteGuard(this._graph);
    }
  }

  reset(): void {
    this._stateCache.clear();
    this._dirty = false;
    this._graph = null;
    this._canvas = null;
  }

  private _requireGraph(): LGraph {
    if (!this._graph) throw new Error('Graph not initialized — call setCanvas first');
    return this._graph;
  }

  _installDeleteGuard(graph: LGraph): void {
    const originalRemove = graph.remove.bind(graph);
    graph.remove = function(node: LGraphNode) {
      if (node._is_boundary) {
        showToast('Boundary nodes are auto-managed and cannot be deleted', 'warning');
        return;
      }
      return originalRemove(node);
    };
  }

  _cacheCurrentState(): void {
    const graph = this._graph;
    if (!graph || !this._dirty) return;
    const path = graph.extra?.path;
    if (!path) return;
    this._stateCache.set(path, this.toYAML());
  }

  newGraph(name: string): LGraph {
    this._cacheCurrentState();
    const graph = this._requireGraph();
    graph.clear();
    graph.extra = { meta: { name: name, description: '', test_method: '' }, properties: {}, ports: [] };
    this._ensureBoundaryNodes(graph);
    if (this._canvas) {
      this._canvas.draw(true, true);
    }
    this._dirty = false;
    return graph;
  }

  /**
   * Populate an existing LGraph from GraphData.
   * Sets graph.extra, creates boundary nodes, module nodes, and connections.
   * Does NOT set graph.extra.path — the caller must set it before or after.
   * Does NOT restore canvas viewport — caller handles that if needed.
   * Does NOT call graph.clear() — caller must clear the graph first.
   */
  private async _populateGraph(graph: LGraph, data: GraphData): Promise<void> {
    graph.extra = {
      ...graph.extra,
      meta: data.meta || {},
      properties: data.properties || {},
      ports: data.ports || []
    };

    const nodeMap: Record<string, LGraphNode> = {};

    // Ensure boundary nodes exist BEFORE module nodes and connections
    this._ensureBoundaryNodes(graph);
    for (const node of graph._nodes) {
      if (node._is_boundary) {
        nodeMap[node.title] = node;
      }
    }

    // Add module instance nodes
    const nodes = data.nodes || [];
    for (const n of nodes) {
      const node = await this._createNodeFromDataForGraph(n, graph);
      nodeMap[n.id] = node;
    }

    // Add connections (boundary nodes now exist in nodeMap)
    const connections = data.connections || [];
    for (const conn of connections) {
      this._addConnection(conn, nodeMap);
    }
  }

  /**
   * Build a subgraph LGraph from in-memory GraphData (already fetched via _loadRefPorts).
   * The returned graph has onAfterChange wired for dirty tracking.
   * Caller must set graph._subgraph_node = node before calling openSubgraph.
   */
  async buildSubgraphFromData(data: GraphData, refPath: string): Promise<LGraph> {
    const graph = new LiteGraph.LGraph();

    // Set path first so _populateGraph can extend graph.extra
    graph.extra = { path: refPath };

    // Check state cache first — cached edits take precedence over original data
    const cached = this._stateCache.get(refPath);
    await this._populateGraph(graph, cached || data);

    // Wire dirty tracking for edits inside the subgraph
    graph.onAfterChange = () => {
      this.markDirty();
    };

    return graph;
  }

  async loadGraph(path: string): Promise<LGraph> {
    // Cache current unsaved state before switching
    this._cacheCurrentState();

    // Restore from cache if available, otherwise load from disk
    let data: GraphData;
    const cached = this._stateCache.get(path);
    if (cached) {
      data = cached;
      // Keep cache entry until explicit save, so unsaved changes survive
      // multiple round-trips (switch away → switch back → switch away → …).
    } else {
      const resp = await API.loadGraph(path);
      data = resp.data;
    }

    const graph = this._requireGraph();
    graph.clear();

    // Set path before populate so boundary nodes can read ports from graph.extra
    graph.extra = { path: path };

    await this._populateGraph(graph, data);

    // Restore canvas viewport
    if (this._canvas && data.canvas) {
      const { offset_x, offset_y, scale } = data.canvas;
      this._canvas.ds.offset = [offset_x || 0, offset_y || 0];
      this._canvas.ds.scale = scale || 1;
    }

    if (this._canvas) {
      this._canvas.draw(true, true);
    }

    // When restored from cache, the graph already has unsaved changes,
    // so it must remain dirty so _cacheCurrentState re-caches it on the
    // next switch.  When loaded fresh from disk, it starts clean.
    this._dirty = !!cached;
    return graph;
  }

  async _createNodeFromData(nodeData: any): Promise<LGraphNode> {
    return this._createNodeFromDataForGraph(nodeData, this._requireGraph());
  }

  private async _createNodeFromDataForGraph(nodeData: any, graph: LGraph): Promise<LGraphNode> {
    const node = LiteGraph.createNode('rtl/module');
    node.title = nodeData.id;
    node.pos = [nodeData.pos_x || 0, nodeData.pos_y || 0];
    if (nodeData.size_w || nodeData.size_h) {
      node.size = [nodeData.size_w || node.size[0], nodeData.size_h || node.size[1]];
    }
    if (nodeData.collapsed) {
      node.flags.collapsed = true;
    }
    node._module_ref = nodeData.ref || '';
    node._module_data = nodeData;
    node.properties = nodeData.properties || {};

    if (nodeData.ref) {
      await this._loadRefPorts(node, nodeData.ref);
    }

    graph.add(node);
    return node;
  }

  async _loadRefPorts(node: LGraphNode, refPath: string): Promise<void> {
    try {
      // Check state cache first — unsaved edits take precedence over on-disk data
      let data: GraphData;
      const cached = this._stateCache.get(refPath);
      if (cached) {
        data = cached;
      } else {
        const resp = await API.loadGraph(refPath);
        data = resp.data;
      }
      node._subgraph_data = data;
      if (node.setPortsFromData) {
        node.setPortsFromData(data);
      }
      if (this._canvas) {
        this._canvas.draw(true, true);
      }
    } catch (e: any) {
      showToast('Failed to load ports for ' + refPath + ': ' + (e.message || 'unknown error'), 'error');
    }
  }

  _addConnection(conn: any, nodeMap: Record<string, LGraphNode>): void {
    const fromNode = nodeMap[conn.from.node];
    if (!fromNode) {
      console.warn('Connection references missing node:', conn.from.node);
      return;
    }
    const fromPort = this._findPortIndex(fromNode, 'outputs', conn.from.port);
    if (fromPort >= 0) {
      for (const to of conn.to) {
        const toNode = nodeMap[to.node];
        if (!toNode) {
          console.warn('Connection target references missing node:', to.node);
          continue;
        }
        const toPort = this._findPortIndex(toNode, 'inputs', to.port);
        if (toPort >= 0) {
          fromNode.connect(fromPort, toNode, toPort);
        }
      }
    }
  }

  _findPortIndex(node: LGraphNode, slotType: 'inputs' | 'outputs', portName: string): number {
    const slots: LGraphNodePort[] = node[slotType] || [];
    for (let i = 0; i < slots.length; i++) {
      if (slots[i].name === portName) return i;
    }
    return -1;
  }

  /**
   * Ensure boundary nodes (graph_input, graph_output) exist on the graph
   * and are synced with graph.extra.ports. Creates them if missing.
   */
  _ensureBoundaryNodes(graph: LGraph): void {
    if (!graph) return;

    const nodes: LGraphNode[] = graph._nodes || [];
    let inputNode: LGraphNode | null = null;
    let outputNode: LGraphNode | null = null;

    for (const node of nodes) {
      if (node.type === 'rtl/graph_input') inputNode = node;
      if (node.type === 'rtl/graph_output') outputNode = node;
    }

    const ports = (graph.extra && graph.extra.ports) || [];

    if (!inputNode) {
      inputNode = LiteGraph.createNode('rtl/graph_input');
      inputNode.pos = [40, 100];
      graph.add(inputNode);
    }
    inputNode.syncWithGraphPorts?.(graph);

    if (!outputNode) {
      outputNode = LiteGraph.createNode('rtl/graph_output');
      outputNode.pos = [600, 100];
      graph.add(outputNode);
    }
    outputNode.syncWithGraphPorts?.(graph);
  }

  /**
   * Public method to re-sync boundary nodes with current graph ports.
   * Called externally after port changes.
   */
  syncBoundaryNodes(): void {
    if (this._graph) {
      this._ensureBoundaryNodes(this._graph);
    }
  }

  /**
   * Generate a unique node name at the current graph level.
   */
  uniqueNodeName(baseName: string): string {
    if (!this._graph) return baseName;
    const existing = new Set<string>();
    for (const node of this._graph._nodes) {
      if (!node._is_boundary) {
        existing.add(node.title);
      }
    }
    if (!existing.has(baseName)) return baseName;
    let i = 2;
    while (existing.has(`${baseName}_${i}`)) {
      i++;
    }
    return `${baseName}_${i}`;
  }

  isNodeNameUnique(name: string, excludeNode?: LGraphNode): boolean {
    if (!this._graph) return true;
    for (const node of this._graph._nodes) {
      if (node._is_boundary) continue;
      if (excludeNode && node === excludeNode) continue;
      if (node.title === name) return false;
    }
    return true;
  }

  async saveGraph(path: string): Promise<boolean> {
    const yaml = this.toYAML();
    await API.saveGraph(path, yaml);
    this._requireGraph().extra.path = path;
    this._stateCache.delete(path);
    this._dirty = false;
    return true;
  }

  toYAML(): GraphData {
    const graph = this._graph;
    if (!graph) {
      return createEmptyGraphData();
    }
    const data: GraphData = {
      meta: graph.extra.meta || { name: '', description: '', test_method: '' },
      properties: graph.extra.properties || {},
      ports: graph.extra.ports || [],
      nodes: [],
      connections: []
    };

    // Serialize canvas viewport
    if (this._canvas) {
      const ds = this._canvas.ds;
      data.canvas = {
        offset_x: ds.offset[0],
        offset_y: ds.offset[1],
        scale: ds.scale
      };
    }

    // Serialize nodes (skip boundary nodes)
    for (const node of graph._nodes) {
      if (node._is_boundary) continue;
      if (node.type === 'rtl/module') {
        const pos = node.pos || [0, 0];
        const size = node.size || [160, 40];
        data.nodes!.push({
          id: node.title,
          ref: node._module_ref || '',
          description: node._module_data ? node._module_data.description : '',
          test_method: node._module_data ? node._module_data.test_method : '',
          pos_x: pos[0],
          pos_y: pos[1],
          size_w: size[0],
          size_h: size[1],
          collapsed: !!(node.flags && node.flags.collapsed),
          properties: node.properties || {}
        });
      }
    }

    // Serialize connections
    const linkMap: Record<string, { node: string; port: string }[]> = {};
    for (const node of graph._nodes) {
      for (const input of (node.inputs || [])) {
        if (input.link !== undefined && input.link !== null) {
          const link = graph.links[String(input.link)];
          if (link) {
            const key = `${link.origin_id}:${link.origin_slot}`;
            if (!linkMap[key]) linkMap[key] = [];
            linkMap[key].push({ node: node.title || String(node.id), port: input.name });
          } else {
            console.warn('Stale link reference on node', node.title, 'input', input.name);
          }
        }
      }
    }
    for (const [fromKey, toList] of Object.entries(linkMap)) {
      const [fromId, fromSlot] = fromKey.split(':');
      const fromNode = graph._nodes.find((n: LGraphNode) => String(n.id) === fromId);
      data.connections!.push({
        from: { node: fromNode ? fromNode.title : fromId, port: fromNode ? fromNode.outputs[parseInt(fromSlot)].name : fromSlot },
        to: toList
      });
    }

    return data;
  }
}

export { GraphManager };
