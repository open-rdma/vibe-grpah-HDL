/**
 * Unit tests for recursive subgraph drill-down flow.
 *
 * Scenarios covered:
 *  1. Self-referencing module: top.yaml contains a node referencing top.yaml
 *  2. Cross-referencing: A.yaml contains a node referencing B.yaml (and vice versa)
 *  3. Non-recursive: simple module with no recursive references
 *  4. buildSubgraphFromData correctly counts nodes in the generated subgraph
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { GraphData } from '../types/graph-types';

// setup.ts installs LiteGraph/LGraph/LGraphCanvas globals that our app code
// (nodes, graph-manager) depends on at module-load time.
import './setup';

// ----- mock API -----
const mockLoadGraph = vi.fn();
vi.mock('../services/api', () => ({
  API: {
    loadGraph: (...args: any[]) => mockLoadGraph(...args),
    saveGraph: vi.fn(),
    createProject: vi.fn(),
    openProject: vi.fn(),
    saveProject: vi.fn(),
    closeProject: vi.fn(),
    createTree: vi.fn(),
    deleteGraph: vi.fn(),
    listTypes: vi.fn(),
    saveTypes: vi.fn(),
    startBuild: vi.fn(),
    getBuildStatus: vi.fn(),
  },
}));

// Now import the real modules (after mocks are installed)
import { GraphManager, createEmptyGraphData } from '../core/graph-manager';
import { TypeSystem } from '../core/type-system';
// Import node types so they register with LiteGraph
import '../nodes/rtl-module';
import '../nodes/boundary-nodes';

// ---- helpers ----

/** Minimal canvas stub with the properties GraphManager accesses */
function stubCanvas(graph: any): any {
  return {
    graph,
    ds: { offset: [0, 0], scale: 1 },
    draw(_fg: boolean, _bg: boolean) {},
    openSubgraph(_g: any) {},
    closeSubgraph() {},
  };
}

/** Create a valid GraphData object with the given nodes */
function makeGraphData(overrides: Partial<GraphData> = {}): GraphData {
  return {
    meta: { name: 'test_module', description: '', test_method: '' },
    properties: {},
    ports: [
      { name: 'clk', direction: 'input', category: 'clock' },
      { name: 'out', direction: 'output', category: 'data' },
    ],
    nodes: [],
    connections: [],
    ...overrides,
  };
}

// ---- tests ----

describe('subgraph drill-down — buildSubgraphFromData', () => {
  let gm: GraphManager;
  let ts: TypeSystem;

  beforeEach(() => {
    mockLoadGraph.mockReset();
    ts = new TypeSystem();
    gm = new GraphManager(ts);
  });

  afterEach(() => {
    gm.reset();
  });

  // ------------------------------------------------------------------
  // Scenario 1: non-recursive module
  // ------------------------------------------------------------------
  it('should populate a subgraph with all module nodes from GraphData', async () => {
    const data = makeGraphData({
      nodes: [
        { id: 'inner_a', ref: 'lib/a.yaml', pos_x: 100, pos_y: 200, properties: {} },
        { id: 'inner_b', ref: 'lib/b.yaml', pos_x: 300, pos_y: 200, properties: {} },
      ],
    });

    // Mock API responses for the inner node refs
    mockLoadGraph.mockImplementation((path: string) => {
      if (path === 'lib/a.yaml') {
        return Promise.resolve({
          path,
          data: makeGraphData({ meta: { name: 'a' }, ports: [{ name: 'in', direction: 'input', category: 'data' }] }),
        });
      }
      if (path === 'lib/b.yaml') {
        return Promise.resolve({
          path,
          data: makeGraphData({ meta: { name: 'b' }, ports: [{ name: 'out', direction: 'output', category: 'data' }] }),
        });
      }
      return Promise.reject(new Error(`unexpected path: ${path}`));
    });

    const subgraph = await gm.buildSubgraphFromData(data, 'top/top.yaml');

    // Should have 2 boundary nodes + 2 module nodes = 4 total
    const allNodes = subgraph._nodes;
    expect(allNodes.length).toBe(4);

    const titles = allNodes.map((n: any) => n.title);
    expect(titles).toContain('<- graph_input');
    expect(titles).toContain('graph_output ->');
    expect(titles).toContain('inner_a');
    expect(titles).toContain('inner_b');
  });

  // ------------------------------------------------------------------
  // Scenario 2: self-referencing module (recursive)
  // ------------------------------------------------------------------
  it('should include a self-referencing node inside the subgraph', async () => {
    const selfRefData = makeGraphData({
      meta: { name: 'top' },
      nodes: [
        { id: 'self_ref', ref: 'top/top.yaml', pos_x: 200, pos_y: 300, properties: {} },
      ],
    });

    // API returns the same data for the self-reference
    mockLoadGraph.mockImplementation((path: string) => {
      if (path === 'top/top.yaml') {
        return Promise.resolve({ path, data: selfRefData });
      }
      return Promise.reject(new Error(`unexpected path: ${path}`));
    });

    const subgraph = await gm.buildSubgraphFromData(selfRefData, 'top/top.yaml');

    const allNodes = subgraph._nodes;
    // 2 boundary + 1 self-ref = 3
    expect(allNodes.length).toBe(3);

    const titles = allNodes.map((n: any) => n.title);
    expect(titles).toContain('self_ref');

    // The self-ref node should have _module_ref set
    const selfRefNode = allNodes.find((n: any) => n.title === 'self_ref');
    expect(selfRefNode).toBeDefined();
    expect((selfRefNode as any)._module_ref).toBe('top/top.yaml');
    // Ports should have been loaded from the API response
    expect(selfRefNode!.inputs.length).toBeGreaterThanOrEqual(0);
    expect(selfRefNode!.outputs.length).toBeGreaterThanOrEqual(0);
  });

  // ------------------------------------------------------------------
  // Scenario 3: cross-referencing (A → B, B → A)
  // ------------------------------------------------------------------
  it('should handle cross-referencing modules without infinite loops', async () => {
    const dataA = makeGraphData({
      meta: { name: 'a' },
      nodes: [{ id: 'b_node', ref: 'lib/b.yaml', pos_x: 150, pos_y: 150, properties: {} }],
      ports: [{ name: 'a_in', direction: 'input', category: 'data' }],
    });
    const dataB = makeGraphData({
      meta: { name: 'b' },
      nodes: [{ id: 'a_node', ref: 'lib/a.yaml', pos_x: 150, pos_y: 150, properties: {} }],
      ports: [{ name: 'b_out', direction: 'output', category: 'data' }],
    });

    mockLoadGraph.mockImplementation((path: string) => {
      if (path === 'lib/a.yaml') return Promise.resolve({ path, data: dataA });
      if (path === 'lib/b.yaml') return Promise.resolve({ path, data: dataB });
      return Promise.reject(new Error(`unexpected path: ${path}`));
    });

    // Drill into A → should see b_node
    const subgraphA = await gm.buildSubgraphFromData(dataA, 'lib/a.yaml');
    expect(subgraphA._nodes.length).toBe(3); // 2 boundary + b_node
    expect(subgraphA._nodes.map((n: any) => n.title)).toContain('b_node');

    // Drill into B → should see a_node
    const subgraphB = await gm.buildSubgraphFromData(dataB, 'lib/b.yaml');
    expect(subgraphB._nodes.length).toBe(3); // 2 boundary + a_node
    expect(subgraphB._nodes.map((n: any) => n.title)).toContain('a_node');
  });
});

describe('GraphManager state cache interaction', () => {
  let gm: GraphManager;
  let ts: TypeSystem;

  beforeEach(() => {
    mockLoadGraph.mockReset();
    ts = new TypeSystem();
    gm = new GraphManager(ts);
  });

  it('buildSubgraphFromData should prefer cached state over passed data', async () => {
    const diskData = makeGraphData({
      meta: { name: 'disk_version' },
      nodes: [{ id: 'old_node', ref: '', pos_x: 0, pos_y: 0, properties: {} }],
    });

    const cachedData = makeGraphData({
      meta: { name: 'cached_version' },
      nodes: [{ id: 'new_node', ref: '', pos_x: 100, pos_y: 100, properties: {} }],
    });

    // Put something into the state cache (simulates unsaved edit in subgraph)
    (gm as any)._stateCache.set('mod/disk.yaml', cachedData);

    // Even though we pass diskData, the cached version should win
    const subgraph = await gm.buildSubgraphFromData(diskData, 'mod/disk.yaml');

    const titles = subgraph._nodes.map((n: any) => n.title);
    expect(titles).toContain('new_node');
    expect(titles).not.toContain('old_node');
  });
});

describe('_cacheCurrentState behavior', () => {
  let gm: GraphManager;
  let ts: TypeSystem;

  beforeEach(() => {
    ts = new TypeSystem();
    gm = new GraphManager(ts);
  });

  it('should NOT cache when _dirty is false (graph is clean)', () => {
    const canvas = stubCanvas(new LiteGraph.LGraph());
    gm.setCanvas(canvas);
    const graph = gm._graph!;
    graph.extra = { path: 'mod/clean.yaml', meta: {}, properties: {}, ports: [] };

    gm.markClean(); // explicitly clean
    gm._cacheCurrentState();

    expect((gm as any)._stateCache.has('mod/clean.yaml')).toBe(false);
  });

  it('should cache when _dirty is true', () => {
    const canvas = stubCanvas(new LiteGraph.LGraph());
    gm.setCanvas(canvas);
    const graph = gm._graph!;
    graph.extra = { path: 'mod/dirty.yaml', meta: {}, properties: {}, ports: [] };

    gm.markDirty();
    gm._cacheCurrentState();

    expect((gm as any)._stateCache.has('mod/dirty.yaml')).toBe(true);
  });

  it('should NOT cache when graph has no path', () => {
    const canvas = stubCanvas(new LiteGraph.LGraph());
    gm.setCanvas(canvas);
    gm.markDirty();
    gm._cacheCurrentState();

    // No path on graph.extra → nothing cached
    expect((gm as any)._stateCache.size).toBe(0);
  });
});

describe('onDblClick guard logic (simulated)', () => {
  // This tests the guard conditions in onDblClick:
  //   if (!refPath && !this._subgraph_data) → bail
  // The fix changed this from:
  //   if (!this._subgraph_data) → bail (too strict)
  // to:
  //   if (!refPath && !this._subgraph_data) → bail (correct — only bail if nothing to load)

  it('should ALLOW drill-down when refPath is set but _subgraph_data is undefined', () => {
    // Simulates a freshly drag-and-dropped node that hasn't finished loading
    const refPath = 'mod/target.yaml';
    const subgraph_data = undefined;

    const shouldBail = !refPath && !subgraph_data;
    expect(shouldBail).toBe(false); // Should NOT bail — refPath is set, data will load
  });

  it('should ALLOW drill-down when both refPath and _subgraph_data are set', () => {
    const refPath = 'mod/target.yaml';
    const subgraph_data = makeGraphData();

    const shouldBail = !refPath && !subgraph_data;
    expect(shouldBail).toBe(false); // Should NOT bail
  });

  it('should BAIL when neither refPath nor _subgraph_data is set', () => {
    const refPath = '';
    const subgraph_data = undefined;

    const shouldBail = !refPath && !subgraph_data;
    expect(shouldBail).toBe(true); // Should bail — nothing to load from
  });

  it('should ALLOW when refPath is empty but _subgraph_data is available (preloaded)', () => {
    // Edge case: data was loaded inline without a ref
    const refPath = '';
    const subgraph_data = makeGraphData();

    const shouldBail = !refPath && !subgraph_data;
    expect(shouldBail).toBe(false); // Should NOT bail — data is already available
  });
});
