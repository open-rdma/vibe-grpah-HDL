# RTL Blueprint — Visual Digital Circuit Design Tool

## Overview

A visual hardware design tool using litegraph.js for the frontend and Python/Flask for the backend. Users design multi-level module blueprints on a graph canvas, which are then compiled via LLM into synthesizable RTL (default: Bluespec SystemVerilog, configurable to other target languages).

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend bundler | Vite |
| Graph editor | litegraph.js v0.7.14 (local submodule in `3rd/`) |
| Frontend language | Vanilla JS (ES modules) |
| Backend framework | Flask |
| Data format | YAML per graph |
| Version control | Git (via GitPython) |
| LLM Agent | Claude Code CLI (primary), OpenAI API (configurable fallback) |

## Project Structure

```
hw-visual-design/
├── frontend/                    # Vite SPA
│   ├── index.html
│   ├── vite.config.js
│   ├── package.json
│   ├── src/
│   │   ├── main.js              # Entry point, app bootstrap
│   │   ├── app.js               # Main application controller
│   │   ├── core/
│   │   │   ├── graph-manager.js    # Graph lifecycle (create/open/close/save)
│   │   │   ├── type-system.js      # Data type definition & registry
│   │   │   ├── project.js          # Project load/save, tree management
│   │   │   └── connection-validator.js  # Type-safe connection enforcement
│   │   ├── nodes/
│   │   │   └── rtl-module.js       # Custom LGraphNode for RTL modules
│   │   ├── ui/
│   │   │   ├── toolbar.js          # Top toolbar
│   │   │   ├── project-panel.js    # Left panel: project tree
│   │   │   ├── property-panel.js   # Right panel: node properties
│   │   │   ├── type-editor.js      # Type definition editor dialog
│   │   │   └── dialogs.js          # File open/save dialogs, etc.
│   │   ├── services/
│   │   │   └── api.js              # REST API client
│   │   └── styles/
│   │       └── main.css
│   └── ...
├── backend/                     # Flask server
│   ├── app.py                   # Flask entry point
│   ├── requirements.txt
│   ├── api/
│   │   ├── __init__.py
│   │   ├── project.py            # Project CRUD, tree management
│   │   ├── graph.py              # Graph file read/write
│   │   ├── types.py              # Type definitions CRUD
│   │   ├── build.py              # Build orchestration (LLM calls)
│   │   └── git.py                # Git version control
│   ├── services/
│   │   ├── llm_agent.py          # LLM Agent interface (Claude Code / OpenAI)
│   │   ├── rtl_compiler.py       # Graph → RTL compiler logic
│   │   └── file_manager.py       # YAML file read/write, path resolution
│   └── templates/
│       └── bluespec_verilog/     # Bluespec SystemVerilog templates
├── 3rd/
│   └── litegraph.js/            # Submodule (existing)
└── docs/
```

## UI Layout (Multi-Panel IDE)

```
┌──────────────────────────────────────────────────────┐
│  Toolbar: [New] [Open] [Save] [Add Subgraph] [Build] │
├──────────┬────────────────────────┬──────────────────┤
│          │                       │                  │
│ Project  │                       │   Properties     │
│ Tree     │   LGraphCanvas         │   Panel          │
│          │   (main work area)     │                  │
│          │                       │   - Node name    │
│  top/    │   [add_inst] [fifo]   │   - Description  │
│  ├top    │       │\     /        │   - Test method  │
│  └adder  │       │ \   /         │   - Ports list   │
│          │     [out_node]        │   - Type selector│
│ library/│                       │                  │
│  ├fifo   │                       │                  │
│  └...    │                       │                  │
│          │                       │                  │
├──────────┴────────────────────────┴──────────────────┤
│  Status: Ready   │  Project: my_project  │ git: clean │
└──────────────────────────────────────────────────────┘
```

### Panel Descriptions

**Project Tree Panel (left):**
- Renders the project's directory/graph hierarchy
- Supports multiple trees (e.g., `top/`, `library/`)
- Click a tree name to expand/collapse: loads and lists actual `.yaml` graph files under that directory via `/api/graph/dir?path=treeName`
- Click a `.yaml` file to open it in the editor
- Drag a graph from the tree onto the canvas to instantiate it as a node
- Context menu: New Graph, Delete Graph, New Tree

**LGraphCanvas (center):**
- Main work area where module graphs are edited
- Custom `rtl/module` node type for RTL module instances
- litegraph.js subgraph navigation: double-click a subgraph node to enter its internal graph
- Connection validation in real-time (type/category/domain checks)

**Properties Panel (right):**
- Context-sensitive to current selection
- Nothing selected: show current graph's top-level properties — name, description, test_method, and **ports list with add/delete**
- Node selected: name, description, test_method, properties key-value editor (add and delete), plus graph-level ports list
- Port selected: name, direction, category, type, clock/reset domain
- Type selector populated from the type system registry

**Toolbar (top):**
- Project: New, Open, Save
- Graph: Add Subgraph, Delete Selected, Zoom In/Out/Reset
- Build: Build Node (scope/mode selector), Build Config
- Type Editor button → opens the type definition dialog

## Data Model

### Project File Organization

```
my_project/
├── project.yaml                 # Project config (trees, types, settings)
├── types.yaml                   # Shared type definitions
├── top/                         # "Top" tree (RTL TOP module)
│   ├── top.yaml                 # Root graph of Top tree
│   └── sub_module_a/
│       └── sub_module_a.yaml    # Child graph (owned by Top tree)
├── library/                     # "Library" tree (reusable modules)
│   ├── adder/
│   │   └── adder.yaml
│   └── fifo/
│       └── fifo.yaml
└── generated/                   # Generated RTL output
    └── ...
```

Each `.yaml` file is one graph. Sub-graphs reside in subdirectories. The `ref:` mechanism enables library-style reuse — the same `adder.yaml` can be referenced by multiple parent graphs. When the original changes, all references see the update.

### Graph YAML Format

```yaml
meta:
  name: "top"
  description: "Top-level module for the design"
  test_method: ""              # Optional test method description
properties:                    # Custom user-defined properties
  clock_freq_mhz: 100
  target: "bluespec_sv"
ports:                         # External ports
  - name: "clk"
    direction: "input"
    category: "clock"           # Special: marks this as a clock source
  - name: "rst_n"
    direction: "input"
    category: "reset"           # Special: marks this as a reset source
    reset_type: "async"         # "async" or "sync"
    active_level: "low"         # "high" or "low"
  - name: "data_in"
    direction: "input"
    category: "data"
    type: "logic[31:0]"
    clock_domain: "clk"         # Which clock drives this signal
    reset_domain: "rst_n"       # Which reset applies
  - name: "data_out"
    direction: "output"
    category: "data"
    type: "logic[31:0]"
    clock_domain: "clk"
nodes:                         # Internal module instances (id must be unique within this graph)
  - id: "adder_inst"
    ref: "library/adder/adder.yaml"  # Reference to another graph
    description: "32-bit adder for accumulation"
    pos_x: 200                    # Canvas X position (litegraph node.pos[0])
    pos_y: 300                    # Canvas Y position (litegraph node.pos[1])
    size_w: 160                   # Node width in pixels (litegraph node.size[0])
    size_h: 40                    # Node height in pixels (litegraph node.size[1])
    collapsed: false              # Whether node is visually collapsed
    properties: {}
  - id: "fifo_inst"
    ref: "library/fifo/fifo.yaml"
    description: "Input buffer FIFO, 8-deep"
    pos_x: 500
    pos_y: 300
    size_w: 160
    size_h: 60
    collapsed: false
    properties:
      DEPTH: 8
canvas:                         # Canvas viewport state (preserved across save/load)
  offset_x: 0                    # Pan offset X
  offset_y: 0                    # Pan offset Y
  scale: 1.0                     # Zoom level
connections:                   # Inter-module wiring
  - from: { node: "graph_input", port: "clk" }
    to: [{ node: "adder_inst", port: "clk" }, { node: "fifo_inst", port: "clk" }]
  - from: { node: "adder_inst", port: "sum" }
    to: [{ node: "graph_output", port: "data_out" }]
  - from: { node: "core_a", port: "result" }
    to: [{ node: "core_b", port: "data_in" }]
    allow_cross_domain: true    # Explicit override for CDC paths
    description: "CDC via handshake, synchronized externally"
```

### Port Signal Categories

| Category | Semantics |
|----------|-----------|
| `clock` | Clock source — drives sequential elements, defines a clock domain |
| `reset` | Reset signal — async or sync, defines a reset domain |
| `data` | All other signals (logic buses, control, etc.) |

### Connection Rules

1. `clock` → any input: allowed (clock can drive anything)
2. `reset` → any input: allowed
3. `data` → `clock` or `reset` input: **blocked** (a data signal shouldn't connect to clock/reset ports)
4. `data` → `data` with different `clock_domain`: **blocked** — unless `allow_cross_domain: true`
5. `data` → `data` with same `clock_domain`: allowed

### Type Definition Format

```yaml
types:
  logic:
    description: "Single-bit logic signal"
    category: "builtin"
  "logic[N:M]":
    description: "Multi-bit bus"
    category: "builtin"
    params:
      - name: "N"
        type: "int"
      - name: "M"
        type: "int"
  custom_struct_name:
    description: "User-defined struct"
    category: "user"
    fields:
      - name: "field_a"
        type: "logic[7:0]"
```

## Frontend Architecture

### Custom Node Type: `rtl/module`

Each canvas node represents an RTL module instance. Extends `LGraphNode`:
- Node title = instance name
- Input ports = module input signals
- Output ports = module output signals
- Color-coded by port category: clock=cyan, reset=orange, data=default
- Double-click on a subgraph node → `openSubgraph()` navigates into its internal graph
- Right-click context menu: Edit Properties, Delete, Open Subgraph

### Canvas Boundary Nodes: `graph_input` / `graph_output`

Each graph canvas displays two special boundary nodes that represent the graph's external ports as visible wiring anchors. They are non-deletable and auto-managed — when ports are added, edited, or removed (via the Properties panel), the boundary nodes update automatically.

**`graph_input` node** — positioned on the left side of the canvas. Has one **output** slot for each `input`-direction graph port. Internal wiring connects from `graph_input.<port>` to internal module inputs. For example, if the graph has an input port `clk`, the `graph_input` node has an output named `clk` that can be wired to `adder_inst.clk`.

**`graph_output` node** — positioned on the right side of the canvas. Has one **input** slot for each `output`-direction graph port. Internal wiring connects from internal module outputs to `graph_output.<port>`. For example, an internal node output `adder_inst.sum` can be wired to `graph_output.data_out`.

Visually, boundary nodes use a distinct style: different background color, thinner/smaller, with the direction arrow baked into the title (`←` for graph_input, `→` for graph_output).

**Boundary node interactions:**
- **Left-click** a boundary node: the Properties Panel switches to the Graph Properties View, showing the full port list with add/delete controls. This is the primary way users discover port management — the boundary nodes serve as visible "handles" for the graph's external interface.
- **Right-click** a boundary node: context menu with "Add Input Port" (graph_input) or "Add Output Port" (graph_output) — opens a quick inline prompt to name the new port, then immediately shows the port in the boundary node and in the properties panel.
- **Delete key** with a boundary node selected: blocked with toast "Boundary nodes are auto-managed and cannot be deleted". Boundary nodes are also excluded from the canvas-level delete-selected action.

### Graph Hierarchy

The design is a **directed graph**, not a tree. A parent graph instantiates child modules (tree-like hierarchy), but those instances can wire to each other peer-to-peer at the same level (making it a graph). The hierarchy is:
- Parent graph: contains module instances and their interconnections
- Child graphs: the internal implementation of a module instance (entered via subgraph navigation)
- Peer wiring: connections between sibling instances within the same parent

### Node Naming Rules

**Unique names at the same level:** Within a single graph, every node instance must have a unique `id`. Duplicate names at the same hierarchy level are prohibited. This is enforced:
- **On instantiation** (drag from tree / context menu): auto-generate a unique suffix if the name already exists (e.g., `adder_inst` → `adder_inst_2`)
- **On rename** (Properties panel): validate the new name against all sibling nodes in the current graph, reject if duplicate
- **On save**: server-side validation rejects graphs with duplicate node IDs, returning a 400 error with the list of duplicates

Different graphs can have nodes with the same name — uniqueness is scoped to the current graph only.

### Cross-Graph Connections

A signal can travel across graph boundaries. For example, a node in the parent graph drives a signal into a subgraph's internal node. This works by composing connections at each level:

```
Parent graph:  source_node.output → sub_instance.input_port
Subgraph:      graph_input.input_port → internal_node.input
```

The parent graph wires `source_node` to `sub_instance`'s port. Inside the subgraph, the `graph_input` node exposes that port, and internal wiring carries it to `internal_node`. From the user's perspective: inside the subgraph, you see the `graph_input` node; in the parent, you see the subgraph instance node showing the same ports.

**No skipping levels:** A signal crossing graph boundaries must pass through explicit ports at **every** level of hierarchy. Given `top → sub_a → sub_b → target`:

```
top:     source → sub_a.port_x       # port_x enters sub_a
sub_a:   graph_input.port_x → sub_b.port_x   # passes through sub_a to sub_b
sub_b:   graph_input.port_x → target.input   # arrives at target
```

It is NOT valid for `top` to wire directly into `sub_b`'s internal node — `sub_a` must declare `port_x` and route it through. This enforces modularity: each graph's ports are its explicit contract with the outside world.

### Connection Validation (Real-Time)

Before a link is created, `onConnectInput`/`onConnectOutput` callbacks check:
1. Port types are compatible (via the type system registry)
2. Category rules (clock/reset/data) are respected
3. Cross-domain flag is present if clock domains differ
Invalid connections are rejected with a notification explaining why.

### Project Panel

- Renders the project's directory/graph tree
- Drag a graph from the tree onto the canvas to instantiate it as a node
- Double-click a graph to open it in the editor
- Context menu: New Graph, Delete Graph, New Tree

### Properties Panel

Three main views, context-sensitive to the current selection:

**1. Graph Properties View** (nothing selected, or clicking a boundary node):
- Shows graph name, description, test_method
- **Ports section** — the most prominent section, always visible:
  - Lists all graph ports with category/direction/type summary
  - Each port row is clickable → inline port editor (name, direction, category, type, clock/reset domain)
  - Each port row has a ✕ delete button
  - If no ports exist: shows a prominent call-to-action — "No ports defined" with a clear [+ Add Port] button at the top of the section
  - [+ Add Port] button at the bottom of the port list, styled to stand out (full width, accent color)

**2. Node Properties View** (node selected):
- Name (validated for uniqueness at current graph level), description, test_method
- Ref path (which subgraph this instance points to)
- Custom properties key-value editor (add/delete rows)
- Ports list (read-only summary — click to drill into individual port properties)

**3. Port Properties View** (port selected from node):
- Name, direction, category, type, clock/reset domain
- Reset type selector (when category is "reset")
- Type selector dropdown populated from the type system registry

### Graph State Cache (Dirty Tracking & Safe Graph Switching)

The canvas holds a single `LGraph` instance. Users freely switch between graphs in the project tree without losing unsaved work. Unsaved changes are held in memory until the user explicitly saves or closes the browser.

**Core mechanism — state cache in GraphManager:**

- `_dirty: boolean` — tracks whether the currently displayed graph has unsaved mutations.
- `_stateCache: Map<string, GraphData>` — stores serialized graph state keyed by path. When the user switches away from a dirty graph, its current state is snapshotted (via `toYAML()`) and stored in the cache before loading the target graph.

**Switching graphs (`openGraph`):**

1. If the current graph is dirty, serialize it to the state cache: `_stateCache.set(currentPath, toYAML())`.
2. Check the state cache for the target path. If found (i.e., the user previously had unsaved work on that graph), load from cache instead of from disk.
3. If not cached, load from disk as normal.
4. Clear the dirty flag after restoring a cached state or loading from disk.

**Saving (`saveGraph`):**

1. Write current state to disk.
2. Remove the path from the state cache.
3. Clear the dirty flag.

**No confirmation dialog on graph switch** — switching graphs is lossless. The user's unsaved state persists in the cache until saved or until the browser tab closes.

**Browser close guard (`beforeunload`):**

- If any entry exists in the state cache, OR the current graph is dirty: block the browser close with the standard `beforeunload` dialog.
- The message is browser-default (e.g., "Changes you made may not be saved.").

**Status bar indicator:**

- A yellow `●` appears next to the graph path when the current graph is dirty.
- A gray `●` appears when the current graph is clean but other cached graphs have unsaved changes.

**Mutations that mark dirty:**

- Any property panel field change (name, description, test_method, properties, port edits)
- Adding/deleting ports
- Adding/deleting nodes
- Creating/removing connections
- Moving nodes on canvas (captured via `LGraph.onAfterChange`)

### Project-Gated Features

When no project is open, all editing and navigation features are disabled. Only project creation/opening remains active. This prevents confusion and errors from interacting with an uninitialized workspace.

**Toolbar — button tracking:**
All state-gated buttons must be stored as class fields so `_updateButtonStates()` can toggle their `disabled` property. Currently only Save/Add/Delete/Build are tracked — Zoom In, Zoom Out, Fit, and Types must also become fields.

**Toolbar state (no project):**
- **Enabled:** New, Open
- **Disabled:** Save, Add Subgraph, Delete, Zoom In, Zoom Out, Fit, Build, Types
- `_updateButtonStates()` gates Zoom In/Out/Fit/Types on `hasProject` (not `hasGraph`) — navigation controls should be available any time a project is open even if no graph is loaded yet.
- Save and Add Subgraph gate on `hasGraph` (project must be open AND a graph loaded).
- Delete gates on `hasSelection`.
- Build gates on `hasGraph`.

**Canvas state (no project):**
- No `LGraphCanvas` instance exists. The canvas container shows a centered placeholder message: "Open or create a project to begin."
- `App._ensureCanvas()` (new method) lazily creates the litegraph canvas on first project open. Called from both `showNewProjectDialog` and `showOpenProjectDialog` success paths.
- `App._ensureCanvas()` is idempotent — if canvas already exists, it's a no-op.
- Drag-and-drop from the project tree is ignored when no project is open (the drop handler already depends on `_graphManager._graph` which is null until canvas is created).

**Property panel state (no project):**
- Shows a placeholder: "No project open." with subtext "Use New or Open to get started."
- `PropertyPanel.clear()` checks `_app._project.isOpen()` first, shows placeholder if false.

**Project panel state (no project):**
- Shows a placeholder: "No project open." with subtext "Use New or Open to get started."
- `ProjectPanel.refresh()` checks project state, shows placeholder if no project open.

**Transitions:**
- **Startup → no project:** All panels show their no-project placeholders. Toolbar buttons are gated per the table above. `_initLiteGraph()` is NOT called during construction — only layout placeholders are rendered.
- **Project opened (New or Open):** `_ensureCanvas()` creates the litegraph graph+canvas. `_initComponents()` registers the `onAfterChange` hook. All panels refresh with real content. Toolbar calls `refresh()` → `_updateButtonStates()` to re-evaluate.
- **No "close project" action exists**, so the no-project state only occurs at startup before the first project is opened. Once a project is open, the workspace stays initialized.

### Recent Projects

When opening a project, a list of recently opened projects is displayed for quick access. This eliminates the need to re-type or re-navigate to frequently used project paths.

**Storage:**
- Uses `localStorage` under key `recent-projects`
- Stores an array of project path strings, most recent first
- Maximum 10 entries; duplicates are moved to the top on re-open
- Read/written by a new service module `src/services/recent-projects.ts`

**Service API (`RecentProjects`):**
- `getRecentProjects(): string[]` — returns the current list from localStorage
- `addRecentProject(path: string): void` — adds a path, deduplicates, trims to 10, persists

**Dialog integration (`showOpenProjectDialog`):**
- Below the path input, a "Recent Projects" list is shown
- Each item is a clickable row showing the project path
- Clicking a recent project fills the path input with that path
- Double-clicking a recent project opens it directly (calls `onOpen(path)` immediately)
- If the recent list is empty, the section is not shown

**Recording:**
- `App.showOpenProjectDialog()` success callback calls `RecentProjects.addRecentProject(path)`
- `App.showNewProjectDialog()` success callback calls `RecentProjects.addRecentProject(path)`
- Recording happens after successful open/create, not before

---

## Backend Architecture

### API Endpoints

```
PROJECT MANAGEMENT
  POST   /api/project/create          Create new project scaffold
  POST   /api/project/open            Open existing project (returns config)
  POST   /api/project/save            Save project config
  GET    /api/project/trees           List all trees in project
  POST   /api/project/tree/create     Create a new tree

GRAPH OPERATIONS
  GET    /api/graph/load?path=...     Load a graph YAML file
  POST   /api/graph/save              Save a graph YAML file
  POST   /api/graph/validate          Validate graph integrity (refs, types, connections)
  DELETE /api/graph/delete?path=...   Delete a graph
  GET    /api/graph/dir?path=...      List graph files under a directory

TYPE SYSTEM
  GET    /api/types/list              List all type definitions
  POST   /api/types/save              Save type definitions
  GET    /api/types/check?from=...&to=...  Check if two types are compatible

BUILD (LLM)
  POST   /api/build                   Start a build task
  GET    /api/build/status/<task_id>  Poll build task status/progress
  GET    /api/build/output/<task_id>  Get generated RTL output

GIT
  POST   /api/git/commit              Commit with message
  GET    /api/git/log                 View commit history
  POST   /api/git/checkout            Checkout a revision

LLM CONFIG
  GET    /api/llm/config              Get current LLM configuration
  POST   /api/llm/config              Update LLM configuration
```

### Build Pipeline

#### Build Scope (vertical axis — which nodes)

| Scope | Description |
|-------|-------------|
| `this` | Build only the selected module |
| `this + descendants` | Build the module and everything below it in the hierarchy |
| `this + ancestors` | Build the module and everything from it up to the root |
| `entire graph` | All modules reachable from the current graph's root |

#### Build Mode (horizontal axis — how to generate)

| Mode | Description |
|------|-------------|
| `fresh` | Send only the module spec (ports, description, properties) to the LLM — no prior code |
| `incremental` | Send the module spec + previously generated RTL code — LLM refines/updates |

#### Build Request

```json
POST /api/build
{
  "target_node": "top/top.yaml",
  "scope": "descendants",
  "mode": "fresh",
  "include_testbench": true
}
→ { "task_id": "uuid" }
```

#### Connection Node References

The special node IDs `graph_input` and `graph_output` in the connections section refer to the module's own external ports (as defined in the `ports` list). These are the graph-level input/output boundary nodes that map internal sub-module ports to the module's external interface.

#### Build Order Strategy

- For `descendants` or `all`: bottom-up (leaves first → parent last), so sub-module RTL exists when generating the parent
- For `ancestors`: bottom-up from root to the target's level
- Dependencies resolved via the module instantiation DAG

#### Prompt Composition

For each node during build:
1. System prompt: "You are an RTL design expert. Output only synthesizable Bluespec SystemVerilog."
2. Module context: target language, coding conventions
3. Module spec: name, description, port list, properties
4. Sub-module interfaces: ports of all referenced sub-graphs (for wiring context)
5. Connection map: how sub-modules are wired together
6. [Incremental mode]: previously generated RTL code

#### Testbench Generation

When `include_testbench: true`:
1. Module's `test_method` description (stimulus strategy, checker logic)
2. Module port list with types and clock/reset domains
3. Interfaces of directly connected neighbor modules (so AI generates realistic stimulus)
4. Clock generation rules, reset sequencing
5. The LLM is instructed: "Module X connects to module Y via port Z. Study Y's interface to generate realistic traffic on Z."

### LLM Agent Abstraction

```python
class LLMAgent(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        """Call the LLM and return generated text."""
```

- `ClaudeCodeAgent` — shells out to `claude --print --prompt "..."`
- `OpenAIAgent` — uses `openai` Python SDK
- Configurable via `LLM_CONFIG` in project settings
- Designed for future extension to other providers

## Key Design Decisions

1. **Graph, not tree**: Module hierarchy is a directed graph — parent instantiates children, siblings can wire peer-to-peer. The parent's generated code includes the `wire`/`assign` statements between its children.

2. **File-based persistence**: One YAML file per graph, directory hierarchy mirrors module hierarchy. Git provides versioning. No database — simple, transparent, diffable.

3. **Reference-based reuse**: Library modules are referenced by path (`ref:`), not copied. Changes propagate to all referrers.

4. **Type-safe connections**: The type system + port categories (clock/reset/data) + clock domain checking prevent invalid wiring at edit time.

5. **Configurable target languages**: Template-based code generation with Bluespec SystemVerilog as the default. Target language is a project-level setting.

6. **LLM as compiler backend**: The LLM translates module specs into RTL. It receives structured context (ports, connections, sub-module interfaces) to produce correct, synthesizable code.
