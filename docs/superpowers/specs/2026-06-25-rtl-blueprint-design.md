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
- Drag a graph from the tree onto the canvas to instantiate it as a node
- Double-click a graph to open it in the editor
- Context menu: New Graph, Delete Graph, New Tree

**LGraphCanvas (center):**
- Main work area where module graphs are edited
- Custom `rtl/module` node type for RTL module instances
- litegraph.js subgraph navigation: double-click a subgraph node to enter its internal graph
- Connection validation in real-time (type/category/domain checks)

**Properties Panel (right):**
- Context-sensitive to current selection
- Node selected: name, description, test_method, properties key-value editor
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
nodes:                         # Internal module instances
  - id: "adder_inst"
    ref: "library/adder/adder.yaml"  # Reference to another graph
    description: "32-bit adder for accumulation"
    properties: {}
  - id: "fifo_inst"
    ref: "library/fifo/fifo.yaml"
    description: "Input buffer FIFO, 8-deep"
    properties:
      DEPTH: 8
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

### Graph Hierarchy

The design is a **directed graph**, not a tree. A parent graph instantiates child modules (tree-like hierarchy), but those instances can wire to each other peer-to-peer at the same level (making it a graph). The hierarchy is:
- Parent graph: contains module instances and their interconnections
- Child graphs: the internal implementation of a module instance (entered via subgraph navigation)
- Peer wiring: connections between sibling instances within the same parent

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

- Context-sensitive to the current selection
- Node selected: shows name, description, test_method, properties key-value editor
- Port selected: shows name, direction, category, type, clock/reset domain
- Type selector dropdown populated from the type system registry

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
