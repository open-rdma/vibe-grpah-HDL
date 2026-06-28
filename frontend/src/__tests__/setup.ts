// Test setup: provide a functional LiteGraph stub for the Node.js test environment.
// The real litegraph.js uses (function(global){...})(this) which fails in ESM
// because top-level `this` is undefined.  This stub replicates the APIs our
// application code actually uses, which is enough for unit-testing data-layer
// operations like buildSubgraphFromData, _populateGraph, _loadRefPorts, etc.

// ---------------------------------------------------------------------------
// Minimal DOM stubs that litegraph constructors need
// ---------------------------------------------------------------------------
(globalThis as any).HTMLCanvasElement = class {};
(globalThis as any).CanvasRenderingContext2D = class {};

// ---------------------------------------------------------------------------
// LLink — lightweight link pair
// ---------------------------------------------------------------------------
class LLink {
  origin_id: number;
  origin_slot: number;
  target_id: number;
  target_slot: number;
  constructor(origin_id: number, origin_slot: number, target_id: number, target_slot: number) {
    this.origin_id = origin_id;
    this.origin_slot = origin_slot;
    this.target_id = target_id;
    this.target_slot = target_slot;
  }
}

// ---------------------------------------------------------------------------
// LGraphNodePort — minimal port/slot
// ---------------------------------------------------------------------------
interface LGraphNodePort {
  name: string;
  type: string;
  link: number | null;
  color_on: string;
  _port_data: any;
}

function makePort(name: string, type: string): LGraphNodePort {
  return { name, type, link: null, color_on: '#AAA', _port_data: null };
}

// ---------------------------------------------------------------------------
// LGraphNode — base node class
// ---------------------------------------------------------------------------
class LGraphNode {
  id: number;
  type: string | null;
  title: string;
  desc: string;
  pos: [number, number];
  size: [number, number];
  flags: { collapsed: boolean };
  color: string;
  bgcolor: string;
  boxcolor: string;
  shape: string | number;
  properties: Record<string, any>;
  inputs: LGraphNodePort[];
  outputs: LGraphNodePort[];
  graph: LGraph | null;

  // Application-defined extensions
  _is_boundary: boolean;
  _module_ref: string | undefined;
  _module_data: any;
  _subgraph_data: any;
  _subgraph: LGraph | undefined;

  // Callback slots (set by node registration or app code)
  onConnectInput?: Function;
  onConnectOutput?: Function;
  onDblClick?: Function;
  getExtraMenuOptions?: Function;
  setPortsFromData?: Function;
  syncWithGraphPorts?: Function;
  getPortColor?: Function;

  constructor() {
    this.id = ++LGraphNode._nextId;
    this.type = null;
    this.title = '';
    this.desc = '';
    this.pos = [0, 0];
    this.size = [160, 40];
    this.flags = { collapsed: false };
    this.color = '#333';
    this.bgcolor = '#353535';
    this.boxcolor = '#666';
    this.shape = 'box';
    this.properties = {};
    this.inputs = [];
    this.outputs = [];
    this.graph = null;
    this._is_boundary = false;
    this._module_ref = undefined;
    this._module_data = undefined;
    this._subgraph_data = undefined;
    this._subgraph = undefined;
  }

  addInput(name: string, type: string): void {
    this.inputs.push(makePort(name, type));
  }

  addOutput(name: string, type: string): void {
    this.outputs.push(makePort(name, type));
  }

  connect(slot: number, targetNode: LGraphNode, targetSlot: number): void {
    const link = new LLink(this.id, slot, targetNode.id, targetSlot);
    this.outputs[slot].link = link as any;
    (targetNode.inputs[targetSlot] as any).link = link as any;
    if (this.graph) {
      this.graph._links.push(link);
    }
  }

  static _nextId = 1;
}

// ---------------------------------------------------------------------------
// LGraph
// ---------------------------------------------------------------------------
class LGraph {
  _nodes: LGraphNode[];
  _links: LLink[];
  links: Record<string, LLink>;
  extra: any;
  _subgraph_node: LGraphNode | null;
  _is_subgraph: boolean;
  onAfterChange: (() => void) | null;
  _onAfterChange: (() => void) | null;

  constructor() {
    this._nodes = [];
    this._links = [];
    this.links = {}; // indexed by link id string
    this.extra = {};
    this._subgraph_node = null;
    this._is_subgraph = false;
    this.onAfterChange = null;
    this._onAfterChange = null;
  }

  add(node: LGraphNode): void {
    node.graph = this;
    this._nodes.push(node);
  }

  remove(node: LGraphNode): void {
    const idx = this._nodes.indexOf(node);
    if (idx >= 0) {
      this._nodes.splice(idx, 1);
      node.graph = null;
    }
  }

  clear(): void {
    for (const node of this._nodes) {
      node.graph = null;
    }
    this._nodes.length = 0;
    this._links.length = 0;
    this.links = {};
  }
}

// ---------------------------------------------------------------------------
// LGraphCanvas — minimal stub
// ---------------------------------------------------------------------------
class LGraphCanvas {
  graph: LGraph | null;
  canvas: any;
  ds: { offset: [number, number]; scale: number };
  background_image: string;
  render_links_border: boolean;
  links_render_mode: number;
  selected_nodes: Record<string, LGraphNode>;
  onNodeSelected: Function | null;
  onNodeDeselected: Function | null;
  _graph_stack: LGraph[];

  constructor(_el: any, graph?: LGraph) {
    this.graph = graph || null;
    this.canvas = { width: 800, height: 600 };
    this.ds = { offset: [0, 0], scale: 1 };
    this.background_image = '';
    this.render_links_border = false;
    this.links_render_mode = 0;
    this.selected_nodes = {};
    this.onNodeSelected = null;
    this.onNodeDeselected = null;
    this._graph_stack = [];
  }

  draw(_fg?: boolean, _bg?: boolean): void {}
  selectNode(_node: LGraphNode): void {}
  deselectAllNodes(): void {}
  zoom(_factor: number, _center?: [number, number]): void {}
  zoomToFit(): void {}

  openSubgraph(graph: LGraph): void {
    if (this.graph) {
      this._graph_stack.push(this.graph);
    }
    this.graph = graph;
  }

  closeSubgraph(): void {
    if (this._graph_stack.length > 0) {
      this.graph = this._graph_stack.pop()!;
    }
  }
}

// ---------------------------------------------------------------------------
// LiteGraph — global namespace (the part our app code uses)
// ---------------------------------------------------------------------------
const _nodeTypes: Record<string, { new (): LGraphNode }> = {};

const LiteGraphStub = {
  VERSION: 0.4,

  // Shape constants
  SPLINE_LINK: 0,
  BOX_SHAPE: 'box',

  // Class refs (our code does `new LiteGraph.LGraph()` etc.)
  LGraph,
  LGraphCanvas,
  LLink,
  LGraphNode,

  // Node registry (used at module load time by node definition files)
  registerNodeType(type: string, base_class: { new (): LGraphNode } & { title?: string; desc?: string }): void {
    // Copy LGraphNode.prototype methods onto the registered class's prototype,
    // matching the real litegraph.js behaviour (lines 177-181).  Our node
    // constructors are plain functions, not subclasses, so addInput/addOutput/
    // connect would otherwise be missing.
    for (const key of Object.getOwnPropertyNames(LGraphNode.prototype)) {
      if (key === 'constructor') continue;
      if (!(key in base_class.prototype)) {
        (base_class.prototype as any)[key] = (LGraphNode.prototype as any)[key];
      }
    }
    _nodeTypes[type] = base_class;
  },

  createNode(type: string): LGraphNode {
    const Ctor = _nodeTypes[type];
    if (!Ctor) {
      throw new Error(`LiteGraph.createNode: unknown node type "${type}"`);
    }
    const node = new Ctor();
    node.type = type;
    // Copy static title/desc from constructor
    if ((Ctor as any).title) node.title = (Ctor as any).title;
    if ((Ctor as any).desc) node.desc = (Ctor as any).desc;
    return node;
  },
};

// Install on globalThis so module-level LiteGraph.* calls work
(globalThis as any).LiteGraph = LiteGraphStub;
(globalThis as any).LGraph = LGraph;
(globalThis as any).LGraphCanvas = LGraphCanvas;
(globalThis as any).LLink = LLink;
(globalThis as any).LGraphNode = LGraphNode;
