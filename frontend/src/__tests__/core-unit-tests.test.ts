/**
 * Comprehensive unit tests for TypeSystem, GraphManager.toYAML round-trip,
 * and ConnectionValidator (I6: test coverage expansion).
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// setup.ts installs LiteGraph/LGraph/LGraphCanvas globals
import './setup';

// ----- mocks -----
vi.mock('../ui/toast', () => ({
  showToast: vi.fn(),
}));

const mockListTypes = vi.fn();
vi.mock('../services/api', () => ({
  API: {
    loadGraph: vi.fn(),
    saveGraph: vi.fn(),
    createProject: vi.fn(),
    openProject: vi.fn(),
    saveProject: vi.fn(),
    closeProject: vi.fn(),
    createTree: vi.fn(),
    deleteGraph: vi.fn(),
    listTypes: (...args: any[]) => mockListTypes(...args),
    saveTypes: vi.fn(),
    startBuild: vi.fn(),
    getBuildStatus: vi.fn(),
  },
}));

import { TypeSystem } from '../core/type-system';
import { GraphManager, createEmptyGraphData } from '../core/graph-manager';
import { ConnectionValidator } from '../core/connection-validator';
import '../nodes/rtl-module';
import '../nodes/boundary-nodes';

// ==========================================================================
// TypeSystem areCompatible tests
// ==========================================================================
describe('TypeSystem.areCompatible', () => {
  let ts: TypeSystem;

  beforeEach(() => {
    ts = new TypeSystem();
  });

  it('returns true for empty or null strings', () => {
    expect(ts.areCompatible('', '')).toBe(true);
    expect(ts.areCompatible('', 'logic')).toBe(true);
    expect(ts.areCompatible('logic', '')).toBe(true);
  });

  it('returns true for exact match', () => {
    expect(ts.areCompatible('logic', 'logic')).toBe(true);
  });

  it('returns false for different base types', () => {
    expect(ts.areCompatible('logic', 'wire')).toBe(false);
  });

  it('returns true for same bus type with same width', () => {
    expect(ts.areCompatible('logic[7:0]', 'logic[7:0]')).toBe(true);
  });

  it('returns false for same base but different bus widths', () => {
    expect(ts.areCompatible('logic[7:0]', 'logic[15:0]')).toBe(false);
    expect(ts.areCompatible('logic[3:0]', 'logic[7:0]')).toBe(false);
  });

  it('handles descending indices correctly (e.g. logic[0:7])', () => {
    // logic[7:0] and logic[0:7] should both have width 8
    expect(ts.areCompatible('logic[7:0]', 'logic[0:7]')).toBe(true);
  });

  it('returns true when one is a bus and the other is a plain base (width not checked)', () => {
    // Plain 'logic' has no width constraint, so it's compatible with any logic bus
    expect(ts.areCompatible('logic', 'logic[7:0]')).toBe(true);
  });

  it('returns false for unparseable type strings with different bases', () => {
    expect(ts.areCompatible('custom_type_A', 'custom_type_B')).toBe(false);
  });

  it('handles non-standard bus-like types', () => {
    expect(ts.areCompatible('mytype[1:0]', 'mytype[1:0]')).toBe(true);
    expect(ts.areCompatible('mytype[3:0]', 'mytype[1:0]')).toBe(false);
  });
});

// ==========================================================================
// GraphManager.toYAML round-trip tests
// ==========================================================================
describe('GraphManager.toYAML', () => {
  let gm: GraphManager;
  let ts: TypeSystem;

  function stubCanvas(graph: any): any {
    return {
      graph,
      ds: { offset: [0, 0], scale: 1 },
      draw(_fg: boolean, _bg: boolean) {},
    };
  }

  beforeEach(() => {
    ts = new TypeSystem();
    gm = new GraphManager(ts);
  });

  afterEach(() => {
    gm.reset();
  });

  it('returns empty graph data when no graph is set', () => {
    const result = gm.toYAML();
    expect(result.meta.name).toBe('');
    expect(result.nodes).toEqual([]);
    expect(result.connections).toEqual([]);
    expect(result.ports).toEqual([]);
    expect(result.properties).toEqual({});
  });

  it('serializes graph metadata', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = {
      meta: { name: 'test_graph', description: 'A test', test_method: '' },
      properties: { clock: '100MHz' },
      ports: [{ name: 'clk', direction: 'input', category: 'clock' }],
      path: 'top/test_graph.yaml',
    };
    gm.setCanvas(stubCanvas(graph));

    const result = gm.toYAML();
    expect(result.meta.name).toBe('test_graph');
    expect(result.meta.description).toBe('A test');
    expect(result.properties.clock).toBe('100MHz');
    expect(result.ports![0].name).toBe('clk');
  });

  it('serializes module nodes and skips boundary nodes', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    // Add a module node manually
    const node = LiteGraph.createNode('rtl/module');
    node.title = 'adder';
    node.pos = [100, 200];
    node.size = [160, 40];
    (node as any)._module_ref = 'lib/adder.yaml';
    graph.add(node);

    const result = gm.toYAML();
    expect(result.nodes!.length).toBe(1);
    expect(result.nodes![0].id).toBe('adder');
    expect(result.nodes![0].ref).toBe('lib/adder.yaml');
    expect(result.nodes![0].pos_x).toBe(100);
    expect(result.nodes![0].pos_y).toBe(200);
  });

  it('excludes boundary nodes from serialization', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = {
      meta: { name: 'test' },
      properties: {},
      ports: [
        { name: 'clk', direction: 'input', category: 'clock' },
        { name: 'out', direction: 'output', category: 'data' },
      ],
    };
    gm.setCanvas(stubCanvas(graph));

    // Trigger boundary node creation
    gm.syncBoundaryNodes();

    const result = gm.toYAML();
    // No non-boundary nodes exist, so nodes should be empty
    expect(result.nodes!.length).toBe(0);
  });

  it('serializes connections between nodes', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = {
      meta: { name: 'test' },
      properties: {},
      ports: [
        { name: 'in', direction: 'input', category: 'data' },
        { name: 'out', direction: 'output', category: 'data' },
      ],
    };
    gm.setCanvas(stubCanvas(graph));

    // Create two module nodes with ports
    const src = LiteGraph.createNode('rtl/module');
    src.title = 'source';
    src.addOutput('data_out', 'logic');
    graph.add(src);

    const dst = LiteGraph.createNode('rtl/module');
    dst.title = 'sink';
    dst.addInput('data_in', 'logic');
    graph.add(dst);

    // Connect them
    src.connect(0, dst, 0);

    const result = gm.toYAML();
    expect(result.connections!.length).toBe(1);
    expect(result.connections![0].from.node).toBe('source');
    expect(result.connections![0].from.port).toBe('data_out');
    expect(result.connections![0].to.length).toBe(1);
    expect(result.connections![0].to[0].node).toBe('sink');
    expect(result.connections![0].to[0].port).toBe('data_in');
  });

  it('round-trips through toYAML without data loss', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = {
      meta: { name: 'roundtrip', description: 'Round-trip test', test_method: 'sim' },
      properties: { freq: '50MHz' },
      ports: [
        { name: 'clk', direction: 'input', category: 'clock' },
        { name: 'rst', direction: 'input', category: 'reset' },
        { name: 'result', direction: 'output', category: 'data', type: 'logic[31:0]' },
      ],
    };
    gm.setCanvas(stubCanvas(graph));

    const nodeA = LiteGraph.createNode('rtl/module');
    nodeA.title = 'mod_a';
    nodeA.pos = [50, 100];
    graph.add(nodeA);

    const nodeB = LiteGraph.createNode('rtl/module');
    nodeB.title = 'mod_b';
    nodeB.pos = [300, 100];
    graph.add(nodeB);

    const yaml = gm.toYAML();

    // Verify structure
    expect(yaml.meta.name).toBe('roundtrip');
    expect(yaml.meta.description).toBe('Round-trip test');
    expect(yaml.properties.freq).toBe('50MHz');
    expect(yaml.ports!.length).toBe(3);
    expect(yaml.nodes!.length).toBe(2);

    const ids = yaml.nodes!.map((n: any) => n.id);
    expect(ids).toContain('mod_a');
    expect(ids).toContain('mod_b');
  });

  it('serializes canvas viewport', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    const canvas = stubCanvas(graph);
    canvas.ds.offset = [50, 100];
    canvas.ds.scale = 1.5;
    gm.setCanvas(canvas);

    const result = gm.toYAML();
    expect(result.canvas!.offset_x).toBe(50);
    expect(result.canvas!.offset_y).toBe(100);
    expect(result.canvas!.scale).toBe(1.5);
  });
});

// ==========================================================================
// ConnectionValidator tests
// ==========================================================================
describe('ConnectionValidator', () => {
  let validator: ConnectionValidator;
  let ts: TypeSystem;

  function makePort(name: string, overrides: Record<string, any> = {}): any {
    return {
      name,
      type: 'data',
      link: null,
      color_on: '#AAA',
      _port_data: {
        name,
        direction: 'input',
        category: 'data',
        type: 'logic',
        clock_domain: '',
        allow_cross_domain: false,
        ...overrides,
      },
      ...overrides,
    };
  }

  function makeNode(title: string, inputs: any[] = [], outputs: any[] = []): any {
    return {
      title,
      id: Math.floor(Math.random() * 10000),
      inputs,
      outputs,
      graph: null,
      _is_boundary: false,
    };
  }

  beforeEach(() => {
    ts = new TypeSystem();
    validator = new ConnectionValidator(ts);
  });

  it('allows data → data connection with compatible types', () => {
    const src = makeNode('src', [], [
      makePort('out', { _port_data: { category: 'data', type: 'logic', direction: 'output' } }),
    ]);
    const dst = makeNode('dst', [
      makePort('in', { _port_data: { category: 'data', type: 'logic', direction: 'input' } }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(true);
  });

  it('blocks data → clock connection', () => {
    const src = makeNode('src', [], [
      makePort('out', { _port_data: { category: 'data', type: 'logic', direction: 'output' } }),
    ]);
    const dst = makeNode('dst', [
      makePort('clk', { _port_data: { category: 'clock', type: 'clock', direction: 'input' } }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Cannot connect data output to clock input');
  });

  it('blocks data → reset connection', () => {
    const src = makeNode('src', [], [
      makePort('out', { _port_data: { category: 'data', type: 'logic', direction: 'output' } }),
    ]);
    const dst = makeNode('dst', [
      makePort('rst', { _port_data: { category: 'reset', type: 'reset', direction: 'input' } }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Cannot connect data output to reset input');
  });

  it('blocks type-mismatched data connection', () => {
    const src = makeNode('src', [], [
      makePort('out', { _port_data: { category: 'data', type: 'logic[7:0]', direction: 'output' } }),
    ]);
    const dst = makeNode('dst', [
      makePort('in', { _port_data: { category: 'data', type: 'logic[15:0]', direction: 'input' } }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Type mismatch');
  });

  it('blocks cross-domain connection without override', () => {
    const src = makeNode('src', [], [
      makePort('out', {
        _port_data: { category: 'data', type: 'logic', direction: 'output', clock_domain: 'clk_a' },
      }),
    ]);
    const dst = makeNode('dst', [
      makePort('in', {
        _port_data: { category: 'data', type: 'logic', direction: 'input', clock_domain: 'clk_b' },
      }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Cross-domain');
  });

  it('allows cross-domain connection when one side has allow_cross_domain', () => {
    const src = makeNode('src', [], [
      makePort('out', {
        _port_data: { category: 'data', type: 'logic', direction: 'output', clock_domain: 'clk_a', allow_cross_domain: true },
      }),
    ]);
    const dst = makeNode('dst', [
      makePort('in', {
        _port_data: { category: 'data', type: 'logic', direction: 'input', clock_domain: 'clk_b' },
      }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(true);
  });

  it('returns error for invalid slots', () => {
    const src = makeNode('src', [], []);
    const dst = makeNode('dst', [], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    expect(result.allowed).toBe(false);
    expect(result.reason).toBe('Invalid slot');
  });

  it('treats ports without explicit category as data', () => {
    const src = makeNode('src', [], [
      makePort('out', { _port_data: { type: 'logic', direction: 'output' } }),
    ]);
    const dst = makeNode('dst', [
      makePort('in', { _port_data: { type: 'logic', direction: 'input' } }),
    ], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    // Both default to 'data', same domain → allowed
    expect(result.allowed).toBe(true);
  });

  it('allows connection when ports have no _port_data', () => {
    const src = makeNode('src', [], [{ name: 'out', type: 'data', link: null, color_on: '#AAA', _port_data: null }]);
    const dst = makeNode('dst', [{ name: 'in', type: 'data', link: null, color_on: '#AAA', _port_data: null }], []);

    const result = validator.validate(src as any, 0, dst as any, 0);
    // Empty _port_data defaults to data/data, same type → allowed
    expect(result.allowed).toBe(true);
  });
});

// ==========================================================================
// GraphManager state management
// ==========================================================================
describe('GraphManager state management', () => {
  let gm: GraphManager;
  let ts: TypeSystem;

  function stubCanvas(graph: any): any {
    return {
      graph,
      ds: { offset: [0, 0], scale: 1 },
      draw(_fg: boolean, _bg: boolean) {},
    };
  }

  beforeEach(() => {
    ts = new TypeSystem();
    gm = new GraphManager(ts);
  });

  afterEach(() => {
    gm.reset();
  });

  it('marks dirty and clean correctly', () => {
    expect(gm.isDirty()).toBe(false);
    gm.markDirty();
    expect(gm.isDirty()).toBe(true);
    gm.markClean();
    expect(gm.isDirty()).toBe(false);
  });

  it('tracks dirty state per path via isGraphDirty', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { path: 'mod/a.yaml', meta: {}, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));
    gm.markDirty();

    expect(gm.isGraphDirty('mod/a.yaml')).toBe(true);
    expect(gm.isGraphDirty('mod/b.yaml')).toBe(false);
  });

  it('getCurrentGraphPath returns null when no graph is set', () => {
    expect(gm.getCurrentGraphPath()).toBeNull();
  });

  it('getCurrentGraphPath returns path when graph is set', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { path: 'top/main.yaml', meta: {}, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    expect(gm.getCurrentGraphPath()).toBe('top/main.yaml');
  });

  it('removeNode rejects boundary nodes', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    const bnode = LiteGraph.createNode('rtl/graph_input');
    bnode.title = '<- graph_input';
    (bnode as any)._is_boundary = true;
    graph.add(bnode);

    expect(gm.removeNode(bnode)).toBe(false);
  });

  it('removeNode succeeds for regular nodes', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    const node = LiteGraph.createNode('rtl/module');
    node.title = 'regular';
    graph.add(node);

    expect(gm.removeNode(node)).toBe(true);
    expect(graph._nodes.find((n: any) => n.title === 'regular')).toBeUndefined();
  });

  it('uniqueNodeName appends suffix when name exists', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    const node = LiteGraph.createNode('rtl/module');
    node.title = 'adder';
    graph.add(node);

    expect(gm.uniqueNodeName('adder')).toBe('adder_2');
    expect(gm.uniqueNodeName('unique')).toBe('unique');
  });

  it('newGraph clears existing content and sets up boundary nodes', () => {
    const graph = new LiteGraph.LGraph();
    graph.extra = { path: 'top/old.yaml', meta: {}, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));

    // Add some content
    const node = LiteGraph.createNode('rtl/module');
    node.title = 'old_node';
    graph.add(node);

    const newGraph = gm.newGraph('fresh');
    expect(newGraph.extra.meta.name).toBe('fresh');
    // Should have boundary nodes
    const boundaryNodes = newGraph._nodes.filter((n: any) => n._is_boundary);
    expect(boundaryNodes.length).toBe(2);
  });
});

// ==========================================================================
// Boundary node context menu — Add Port
// ==========================================================================
describe('Boundary node context menu — Add Port', () => {
  let gm: GraphManager;
  let graph: any;

  function stubCanvas(g: any): any {
    return {
      graph: g,
      ds: { offset: [0, 0], scale: 1 },
      draw(_fg: boolean, _bg: boolean) {},
    };
  }

  beforeEach(() => {
    const ts = new TypeSystem();
    gm = new GraphManager(ts);
    graph = new LiteGraph.LGraph();
    graph.extra = { meta: { name: 'test' }, properties: {}, ports: [] };
    gm.setCanvas(stubCanvas(graph));
    gm._ensureBoundaryNodes(graph);
  });

  afterEach(() => {
    delete (globalThis as any).__app;
    delete (globalThis as any).prompt;
  });

  function triggerAddPortCallback(direction: 'input' | 'output', portName: string): boolean {
    // Find the boundary node of the requested direction
    const boundaryNodes = graph._nodes.filter((n: any) => n._is_boundary);
    const nodeType = direction === 'input' ? 'rtl/graph_input' : 'rtl/graph_output';
    const boundaryNode = boundaryNodes.find((n: any) => n.type === nodeType);
    if (!boundaryNode || !boundaryNode.getExtraMenuOptions) return false;

    // Mock prompt to return the desired port name
    (globalThis as any).prompt = () => portName;

    // Mock __app on globalThis
    const mockApp = {
      _graphManager: gm,
      redraw: vi.fn(),
      _propertyPanel: {
        _showGraphProperties: vi.fn(),
        clear: vi.fn(),
      },
    };
    (globalThis as any).__app = mockApp;

    const options = boundaryNode.getExtraMenuOptions(null, []);
    const addOption = options.find((o: any) => o.content.includes('Add'));
    if (!addOption) return false;
    addOption.callback();
    return true;
  }

  it('adds port to graph.extra.ports via context menu', () => {
    const ok = triggerAddPortCallback('input', 'clk');
    expect(ok).toBe(true);
    expect(graph.extra.ports.length).toBe(1);
    expect(graph.extra.ports[0].name).toBe('clk');
    expect(graph.extra.ports[0].direction).toBe('input');
  });

  it('calls markDirty after adding port via context menu', () => {
    triggerAddPortCallback('input', 'rst_n');
    expect(gm.isDirty()).toBe(true);
  });

  it('calls _showGraphProperties (not clear) after adding port via context menu', () => {
    triggerAddPortCallback('output', 'result');
    const panel = (globalThis as any).__app._propertyPanel;
    expect(panel._showGraphProperties).toHaveBeenCalledWith(graph);
    expect(panel.clear).not.toHaveBeenCalled();
  });

  it('ignores empty port name', () => {
    triggerAddPortCallback('input', '');
    expect(graph.extra.ports.length).toBe(0);
    expect(gm.isDirty()).toBe(false);
  });

  it('adds output port with correct direction', () => {
    triggerAddPortCallback('output', 'data_out');
    expect(graph.extra.ports.length).toBe(1);
    expect(graph.extra.ports[0].direction).toBe('output');
  });
});
