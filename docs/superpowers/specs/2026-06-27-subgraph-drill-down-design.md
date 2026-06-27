# Subgraph Drill-Down Design

**Goal:** Enable double-clicking an RTL module node to drill into its referenced subgraph using litegraph's native subgraph navigation stack, with breadcrumbs and back-navigation.

**Architecture:** Lazy construction — `LGraph` is built from already-loaded `_subgraph_data` on first double-click, then cached on `node._subgraph`. Navigation uses litegraph's built-in `openSubgraph`/`closeSubgraph` stack. Dirty tracking extends the existing per-path `_stateCache` pattern to work across the subgraph stack.

**Tech Stack:** litegraph.js subgraph API, existing GraphManager/App infrastructure, TypeScript

---

## Global Constraints

- Use litegraph native `openSubgraph`/`closeSubgraph` for navigation stack and breadcrumbs
- Subgraph `LGraph` must be lazy-built on first access, not eagerly on node creation
- Dirty state tracked per graph path via existing `_stateCache` mechanism
- Self-reference cycles must be detected and blocked
- Context menu "Open Subgraph" must use the same subgraph navigation (consistency)
- `onNodeSelected`/`onNodeDeselected` must work inside subgraphs (property panel)

---

## Navigation Flow

```
Double-click RTL module node
  |
  +-> _subgraph exists?
  |     yes -> canvas.openSubgraph(node._subgraph)
  |     no  -> buildSubgraph(node)
  |             -> set graph._subgraph_node = node
  |             -> node._subgraph = graph
  |             -> canvas.openSubgraph(node._subgraph)
  |
  v
User is now inside subgraph
  - Breadcrumb rendered automatically by litegraph (parent >> node title)
  - Escape or click breadcrumb area -> closeSubgraph()
  - closeSubgraph pops stack, re-attaches parent graph, centers on subgraph node
```

## Subgraph Construction

`buildSubgraph(node)` builds an `LGraph` from `node._subgraph_data` (a `GraphData` object already fetched during port loading):

1. Create new `LGraph` instance
2. Set `graph.extra` = { path: node._module_ref, meta, properties, ports } from `_subgraph_data`
3. Add `graph_input` and `graph_output` boundary nodes, synced to `graph.extra.ports`
4. Create RTL module nodes for each entry in `nodes[]`
5. Wire connections using the `from.port` / `to[].port` map
6. Set `graph._subgraph_node = node` (required by litegraph for breadcrumb display)
7. Set `graph.onAfterChange` to `GraphManager.markDirty()` for dirty tracking
8. Cache node._subgraph = graph for subsequent double-clicks

This mirrors `GraphManager.loadGraph()` but operates on in-memory data without an API call.

## Dirty Tracking

GraphManager currently tracks one graph + one dirty flag. With subgraphs, multiple `LGraph` instances are alive simultaneously (parent on stack + subgraph active).

**Rule:** Dirty state is tracked per graph path (`graph.extra.path`). When switching between graphs (subgraph open, close, or top-level navigation), the current graph's state is cached before the switch.

Scenarios:

- **Edit inside subgraph, then close (closeSubgraph):** Before popping the stack, cache the subgraph's `toYAML()` under its path in `_stateCache`. Mark dirty if changed from disk version.
- **Edit inside subgraph, then click project tree:** `_cacheCurrentState()` is already called by `loadGraph()`. The subgraph's state is preserved.
- **Drill back into same subgraph:** Second `openSubgraph` reuses `node._subgraph` (already built, already has edits).
- **Save (Ctrl+S):** Saves the currently visible graph (top of stack). Does not automatically save parent or sibling subgraphs — each graph is saved independently.

## Context Menu Consistency

Current behavior: "Open Subgraph" calls `app.openGraph(self._module_ref)` which does a flat replace.

New behavior: "Open Subgraph" triggers the same drill-down path as double-click — build subgraph lazily, then `openSubgraph()`. This ensures drill-down always means the same navigation model regardless of how it's triggered.

## Edge Cases

- **Missing `_subgraph_data`:** Show toast "Cannot open: module data not loaded" instead of silent no-op.
- **Self-reference:** If `node._module_ref === graph.extra.path` (module references itself), block drill-down with toast "Cannot drill into self-referencing module."
- **Nested subgraphs:** Works naturally — litegraph's `_graph_stack` handles arbitrary depth. Each subgraph is a full `LGraph` whose nodes can have their own `_subgraph`.
- **Subgraph node deletion:** If a node with an open subgraph is deleted from the parent, `closeSubgraph` first returns to parent, then the delete proceeds. The orphaned `LGraph` is garbage collected.
- **Dirty subgraph + project close:** `hasAnyUnsavedChanges()` iterates `_stateCache` entries. Subgraph edits stored there are included automatically.

## Files to Modify

| File | Change |
|------|--------|
| `frontend/src/nodes/rtl-module.ts` | `onDblClick`: lazy-build `LGraph` from `_subgraph_data`, set `_subgraph_node`, call `openSubgraph`. Context menu "Open Subgraph": use same path instead of `app.openGraph()`. |
| `frontend/src/core/graph-manager.ts` | Extract `_populateGraph(graph, data)` from `loadGraph` for reuse. Add `buildSubgraphFromData(data, refPath)` public method. Set `onAfterChange` on created subgraphs. |
| `frontend/src/app.ts` | After `openSubgraph`, re-attach `onNodeSelected`/`onNodeDeselected` so property panel works inside subgraphs. Handle `onAfterChange` propagation. |

## What This Does NOT Change

- `app.addSubgraphNode()` — creating placeholder nodes unchanged
- Drag-and-drop from project tree — still uses `app.openGraph()` for top-level navigation
- Save/Load API — still goes through `GraphManager.saveGraph()` / `loadGraph()`
- Port loading (`_loadRefPorts`) — `_subgraph_data` is already populated, no change needed
