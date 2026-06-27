# Subgraph Drill-Down Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable double-clicking an RTL module node to drill into its subgraph using litegraph's native subgraph navigation stack, with breadcrumbs and back-navigation.

**Architecture:** Extract graph population from `loadGraph` into a reusable `_populateGraph`, then add `buildSubgraphFromData` to create `LGraph` from in-memory `_subgraph_data`. Wire `onDblClick` to lazy-build via the new method and call `openSubgraph`. Wrap `openSubgraph`/`closeSubgraph` in app.ts to keep `GraphManager._graph` synced.

**Tech Stack:** litegraph.js subgraph API, TypeScript, existing GraphManager/App infrastructure

## Global Constraints

- Use litegraph native `openSubgraph`/`closeSubgraph` for navigation stack and breadcrumbs
- Subgraph `LGraph` must be lazy-built on first access, not eagerly on node creation
- Dirty state tracked per graph path via existing `_stateCache` mechanism
- Self-reference cycles must be detected and blocked
- Context menu "Open Subgraph" must use the same subgraph navigation (consistency)
- `onNodeSelected`/`onNodeDeselected` must work inside subgraphs (property panel)
- No test framework exists in project — verify via `npx tsc --noEmit` and manual browser testing

---

### Task 1: Extract `_populateGraph(graph, data)` from `loadGraph`

**Files:**
- Modify: `frontend/src/core/graph-manager.ts:98-165`

**Interfaces:**
- Produces: `_populateGraph(graph: LGraph, data: GraphData): Promise<void>` — async, sets `graph.extra`, creates boundary nodes, creates module nodes (with port loading), wires connections. Returns void, operates on passed graph.

- [ ] **Step 1: Extract the `_populateGraph` method**

Add this method to the `GraphManager` class, right before `loadGraph` (after `newGraph` at line 96):

```typescript
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
```

- [ ] **Step 2: Extract `_createNodeFromDataForGraph` from `_createNodeFromData`**

`_createNodeFromData` currently calls `this._requireGraph()` to get the graph. Since `_populateGraph` operates on a passed-in graph (not necessarily `this._graph`), we need a version that takes the graph as a parameter.

Add this private method after `_createNodeFromData` (after line 188):

```typescript
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
```

- [ ] **Step 3: Refactor `_createNodeFromData` to delegate**

Change `_createNodeFromData` (line 167) to delegate to the new method:

```typescript
async _createNodeFromData(nodeData: any): Promise<LGraphNode> {
  return this._createNodeFromDataForGraph(nodeData, this._requireGraph());
}
```

- [ ] **Step 4: Refactor `loadGraph` to use `_populateGraph`**

Replace the middle section of `loadGraph` (lines 114-148, from `const graph = this._requireGraph()` through the connections loop) with a call to `_populateGraph`:

```typescript
async loadGraph(path: string): Promise<LGraph> {
  // Cache current unsaved state before switching
  this._cacheCurrentState();

  // Restore from cache if available, otherwise load from disk
  let data: GraphData;
  const cached = this._stateCache.get(path);
  if (cached) {
    data = cached;
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

  this._dirty = !!cached;
  return graph;
}
```

- [ ] **Step 5: Verify with TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors. The refactored `loadGraph` must compile clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/core/graph-manager.ts
git commit -m "refactor: extract _populateGraph and _createNodeFromDataForGraph from loadGraph"
```

---

### Task 2: Add `buildSubgraphFromData` to GraphManager

**Files:**
- Modify: `frontend/src/core/graph-manager.ts` (add after `_populateGraph`)

**Interfaces:**
- Consumes: `_populateGraph(graph, data)` from Task 1
- Produces: `buildSubgraphFromData(data: GraphData, refPath: string): Promise<LGraph>` — creates a new LGraph, populates it from in-memory data, configures dirty tracking, returns it. Caller sets `_subgraph_node` on the returned graph.

- [ ] **Step 1: Add `buildSubgraphFromData` method**

Add after `_populateGraph`:

```typescript
/**
 * Build a subgraph LGraph from in-memory GraphData (already fetched via _loadRefPorts).
 * The returned graph has onAfterChange wired for dirty tracking.
 * Caller must set graph._subgraph_node = node before calling openSubgraph.
 */
async buildSubgraphFromData(data: GraphData, refPath: string): Promise<LGraph> {
  const graph = new LiteGraph.LGraph();

  // Set path first so _populateGraph can extend graph.extra
  graph.extra = { path: refPath };

  await this._populateGraph(graph, data);

  // Wire dirty tracking for edits inside the subgraph
  graph.onAfterChange = () => {
    this.markDirty();
  };

  return graph;
}
```

- [ ] **Step 2: Add `_syncFromCanvas` method**

After `setCanvas`, add a method to re-sync `_graph` from the canvas (needed after `openSubgraph`/`closeSubgraph` changes `canvas.graph`):

```typescript
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
```

Rename the current `_installDeleteGuard` from `private` to public (or keep private and have `_syncFromCanvas` call it — it's in the same class so private is fine).

- [ ] **Step 3: Verify with TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/core/graph-manager.ts
git commit -m "feat: add buildSubgraphFromData and _syncFromCanvas to GraphManager"
```

---

### Task 3: Wrap subgraph navigation in app.ts

**Files:**
- Modify: `frontend/src/app.ts:74-141` (`_initLiteGraph`)

**Interfaces:**
- Consumes: `GraphManager._syncFromCanvas()`, `GraphManager._cacheCurrentState()` (existing), `GraphManager.buildSubgraphFromData()` from Task 2
- Produces: Wrapped `canvas.openSubgraph` / `canvas.closeSubgraph` that keep `GraphManager._graph` in sync

The `_initLiteGraph` method sets up the litegraph canvas. After the existing setup, we wrap `openSubgraph` and `closeSubgraph` to keep `GraphManager` state consistent.

- [ ] **Step 1: Add subgraph navigation wrappers at end of `_initLiteGraph`**

Add this block at the end of `_initLiteGraph()`, right before the closing `}` of the method (after the drag-and-drop handler setup, before line 142):

```typescript
// Wrap openSubgraph/closeSubgraph to keep GraphManager state synced
const canvas = this._canvas;
const origOpenSubgraph = canvas.openSubgraph.bind(canvas);
const origCloseSubgraph = canvas.closeSubgraph.bind(canvas);

canvas.openSubgraph = (graph: LGraph) => {
  origOpenSubgraph(graph);
  // After attachCanvas, canvas.graph has changed to the subgraph
  this._graphManager._syncFromCanvas();
};

canvas.closeSubgraph = () => {
  // Cache subgraph state before popping the stack
  this._graphManager._cacheCurrentState();
  origCloseSubgraph();
  // After attachCanvas, canvas.graph is back to parent
  this._graphManager._syncFromCanvas();
};
```

- [ ] **Step 2: Verify with TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app.ts
git commit -m "feat: wrap openSubgraph/closeSubgraph to sync GraphManager state"
```

---

### Task 4: Wire `onDblClick` and context menu in rtl-module.ts

**Files:**
- Modify: `frontend/src/nodes/rtl-module.ts:54-103`

**Interfaces:**
- Consumes: `GraphManager.buildSubgraphFromData()` from Task 2, `LGraphCanvas.openSubgraph()` (native), wrapped by Task 3
- Modifies: `onDblClick` (lines 54-61), context menu "Open Subgraph" (lines 87-101)

- [ ] **Step 1: Replace `onDblClick`**

Replace the current `onDblClick` (lines 54-61):

```typescript
proto.onDblClick = function(
  _e: MouseEvent, _pos: number[], graphcanvas: LGraphCanvas
): boolean {
  // Already built and cached — open immediately
  if (this._subgraph) {
    graphcanvas.openSubgraph(this._subgraph);
    return true;
  }

  // No data to build from
  if (!this._subgraph_data) {
    showToast('Cannot open: module data not loaded', 'error');
    return false;
  }

  // Self-reference guard
  const parentPath = graphcanvas.graph?.extra?.path;
  if (this._module_ref && parentPath && this._module_ref === parentPath) {
    showToast('Cannot drill into self-referencing module', 'error');
    return false;
  }

  const app = window.__app;
  if (!app || !app._graphManager) {
    showToast('Cannot open: app not available', 'error');
    return false;
  }

  // Lazy-build subgraph from _subgraph_data
  const refPath = this._module_ref || '';
  app._graphManager.buildSubgraphFromData(this._subgraph_data, refPath)
    .then((subgraph: LGraph) => {
      subgraph._subgraph_node = this;
      this._subgraph = subgraph;
      graphcanvas.openSubgraph(subgraph);
    })
    .catch((e: Error) => {
      showToast('Failed to build subgraph: ' + e.message, 'error');
    });

  return true;
};
```

- [ ] **Step 2: Replace context menu "Open Subgraph" callback**

Replace the current context menu "Open Subgraph" entry (lines 87-101) with one that uses the same drill-down path:

```typescript
if (self._module_ref || self._subgraph_data || self._subgraph) {
  menuOptions.push({
    content: 'Open Subgraph',
    callback: () => {
      if (self._subgraph) {
        canvas.openSubgraph(self._subgraph);
        return;
      }
      if (!self._subgraph_data) {
        showToast('Cannot open: module data not loaded', 'error');
        return;
      }
      const parentPath = canvas.graph?.extra?.path;
      if (self._module_ref && parentPath && self._module_ref === parentPath) {
        showToast('Cannot drill into self-referencing module', 'error');
        return;
      }
      const app = window.__app;
      if (!app || !app._graphManager) {
        showToast('Cannot open: app not available', 'error');
        return;
      }
      const refPath = self._module_ref || '';
      app._graphManager.buildSubgraphFromData(self._subgraph_data, refPath)
        .then((subgraph: LGraph) => {
          subgraph._subgraph_node = self;
          self._subgraph = subgraph;
          canvas.openSubgraph(subgraph);
        })
        .catch((e: Error) => {
          showToast('Failed to build subgraph: ' + e.message, 'error');
        });
    }
  });
}
```

- [ ] **Step 3: Verify with TypeScript compilation**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors. The `LGraph` and `LGraphCanvas` types come from litegraph.js declarations.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/nodes/rtl-module.ts
git commit -m "feat: wire onDblClick and context menu for subgraph drill-down"
```

---

### Task 5: Final build verification

- [ ] **Step 1: Full build check**

Run: `cd frontend && npx tsc --noEmit`

Expected: Zero type errors across all files.

- [ ] **Step 2: Production build**

Run: `cd frontend && npx vite build`

Expected: Build succeeds without errors.

- [ ] **Step 3: Commit (if any fixes needed)**

If the build reveals issues, fix them and commit. Otherwise skip.
