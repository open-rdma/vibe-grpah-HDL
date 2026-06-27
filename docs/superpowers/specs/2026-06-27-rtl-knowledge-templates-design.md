# RTL Knowledge Templates — Design

## Overview

Add structured, cascading knowledge snippets to every level of the data model. These snippets are markdown with optional `{{variable}}` interpolation. They cascade from system → project → graph → node → port at build time, composing the system prompt that guides the LLM to generate correct, convention-aware RTL.

## Motivation

Currently the build pipeline sends only ports, properties, and descriptions to the LLM. There is no way to inject coding conventions, project-specific rules, or per-module constraints. The LLM guesses at naming, style, and clock/reset conventions, producing inconsistent output.

Knowledge templates let users encode these rules once and have them propagate down through the hierarchy, with the ability to override at any level.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Knowledge storage | Inline in existing YAML/GraphData types (`knowledge?: string`) |
| System built-ins | Hardcoded `SYSTEM_KNOWLEDGE` record in `constants.ts` |
| Merging + interpolation | New `KnowledgeMerger` class (pure functions, no state) |
| UI editing | Property panel — collapsible "Knowledge" section per view |
| UI preview | Fullscreen floating overlay (`KnowledgePreview` component) |
| Build integration | Merged knowledge sent in `POST /api/build` body |

## Knowledge Hierarchy & Merge Order

```
SYSTEM (language: verilog | vhdl | bluespec)
  ↓ appends
PROJECT (project.yaml properties, from target language)
  ↓ appends
GRAPH / MODULE (graph .yaml meta.knowledge)
  ↓ appends (recursively for subgraphs)
  ↓ ...sub-subgraphs...
  ↓ appends
NODE (node instance in parent graph)
  ↓ appends
PORT (individual port on the node)
```

Each level contributes its `knowledge` text. The final prompt is the concatenation of all levels, separated by `\n\n---\n\n`.

### Template Interpolation

Any level's knowledge may contain `{{variable}}` patterns that resolve from the current entity's data at render time:

- `{{name}}` → entity name (port name, node title, graph meta.name)
- `{{direction}}` → port direction (`input` / `output`)
- `{{category}}` → port category (`clock` / `reset` / `data`)
- `{{type}}` → port type string
- `{{properties.FOO}}` → custom property `FOO` from the entity's `properties` dict
- `{{description}}` → entity description

Unresolved variables are left as-is (`{{unknown}}`) in the output so the user can see what's missing.

### Level Override with `knowledge_template`

A parent level (typically the graph/module level) may define `knowledge_template` to control how child content is inserted. The template uses `{{children}}` as a placeholder. If no template is defined, child content is appended directly.

**Example — graph meta:**
```yaml
meta:
  name: "top"
  knowledge: |
    # Module: {{name}}
    This module operates at {{properties.clock_freq_mhz}} MHz.
  knowledge_template: |
    # Module Knowledge
    {{children}}
```

When the graph has a child node with `knowledge: "Use non-blocking assignments."`, the merged result is:
```
# Module Knowledge
Use non-blocking assignments.
```

Without `knowledge_template`, the result would be:
```
# Module: top
This module operates at 100 MHz.

---

Use non-blocking assignments.
```

## Data Model Changes

All changes are additions to existing interfaces — no breaking changes.

```typescript
// graph-types.ts

interface PortData {
  // ... existing fields ...
  knowledge?: string;
}

interface GraphMeta {
  // ... existing fields ...
  knowledge?: string;
  knowledge_template?: string;
}

interface GraphNodeData {
  // ... existing fields ...
  knowledge?: string;
}

interface Connection {
  // ... existing fields ...
  knowledge?: string;
}

interface GraphData {
  // ... existing fields ...
  knowledge_template?: string;
}
```

## System Built-In Knowledge

Hardcoded in `constants.ts` under `SYSTEM_KNOWLEDGE`. The target language is inferred from project `properties.target` (default `bluespec`).

```typescript
export const SYSTEM_KNOWLEDGE: Record<string, string> = {
  verilog: `# Verilog Coding Conventions
- Use non-blocking assignments (\`<=\`) in \`always_ff\` blocks.
- Prefer \`wire\` for combinational signals, \`reg\` for sequential.
- Module names should match file names.`,

  vhdl: `# VHDL Coding Conventions
- Use \`std_logic\` and \`std_logic_vector\` for synthesizable code.
- Prefer \`rising_edge(clk)\` over \`clk'event and clk='1'\`.
- Entity names should match file names.`,

  bluespec: `# Bluespec SystemVerilog Conventions
- Use \`mkReg\` and \`mkRegU\` for registers.
- Rules are atomic; use \`(* fire_when_enabled *)\` and \`(* no_implicit_conditions *)\` pragmas.
- Interfaces should be defined as BSV interfaces with methods.`
};
```

The per-language entries are intended as starting defaults. Users add more specific rules at the project or module level.

## KnowledgeMerger (New File)

`src/core/knowledge-merger.ts` — a stateless utility class.

```typescript
class KnowledgeMerger {
  /**
   * Merge knowledge levels from outer to inner.
   * `levels` is ordered outermost-first (system, project, graph, node, port).
   * `context.entity` provides the data for {{variable}} interpolation for the
   *   innermost level (typically the port or node being rendered).
   */
  merge(levels: (string | undefined)[], context: KnowledgeContext): string;

  /**
   * Render a template string with {{variable}} interpolation.
   * @param template  The string containing {{var}} patterns.
   * @param entity    Object to resolve variables from.
   */
  _interpolate(template: string, entity: Record<string, any>): string;

  /**
   * Resolve a dotted path like "properties.clock_freq_mhz" from the entity.
   * Returns the string value, or the original pattern if unresolvable.
   */
  _resolve(entity: Record<string, any>, path: string): string;
}
```

## Property Panel Changes

Three views gain a collapsible "Knowledge" section:

### Graph Properties View
- Collapsible "Knowledge" textarea (edits `meta.knowledge`).
- If the graph has sub-nodes, a second textarea "Knowledge Template" (edits `graph.extra.knowledge_template`).
- [Preview] button opens the fullscreen overlay showing system → project → graph knowledge.

### Node Properties View
- Collapsible "Knowledge" textarea (edits `node._module_data.knowledge`).
- [Preview] button shows system → project → graph → node.

### Port Properties View
- Collapsible "Knowledge" textarea (edits `slot._port_data.knowledge`).
- [Preview] button shows system → project → graph → node → port.

Each knowledge section shows a small indicator icon [✎] when the level has custom knowledge content (vs. empty/default).

## Knowledge Preview Overlay (New File)

`src/ui/knowledge-preview.ts` — a fullscreen floating overlay.

- **Trigger:** [Preview] button in property panel.
- **Visual:** Dark semi-transparent backdrop covering the entire viewport. Centered scrollable content area (max-width 800px, 80vh tall) with monospace-styled merged prompt text.
- **Header bar:** Title showing the entity path (e.g., "Port clk · top/top.yaml"), [Copy] button (copies the full merged text to clipboard), and [Close] button (or click backdrop, or press Escape).
- **Content:** Read-only, rendered as preformatted markdown. Sections separated by `---` horizontal rules.

```
┌──────────────────────────────────────────────────────┐
│  ✎ Knowledge Preview — Port "clk" · top/top.yaml    │
│                              [Copy]  [✕ Close]      │
├──────────────────────────────────────────────────────┤
│                                                      │
│  # Bluespec SystemVerilog Conventions                │
│  - Use mkReg and mkRegU for registers.               │
│  - Rules are atomic...                               │
│                                                      │
│  ────────────────────────────────────────────         │
│                                                      │
│  # Project: 100MHz clock, active-low reset           │
│  The design targets a Xilinx FPGA...                 │
│                                                      │
│  ────────────────────────────────────────────         │
│                                                      │
│  # Port: clk (input, clock)                          │
│  Primary clock input. Must be connected to           │
│  a PLL or external oscillator.                       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

## App Integration

In `app.ts`, the `App` class gains:

- A `_knowledgeMerger: KnowledgeMerger` instance (constructed once, stateless).
- A `_targetLanguage: string` getter that reads `properties.target` from the current project config (defaults to `'bluespec'`).
- A `getSystemKnowledge(): string` method that returns `SYSTEM_KNOWLEDGE[targetLanguage]`.
- A `getProjectKnowledge(): string` that reads project-level knowledge (from `project.yaml` — to be added to the project data model later; for now, returns empty).

The `PropertyPanel` constructor gains a reference to the `App` (already has `_app`).

## Build Pipeline Integration

When the user triggers a build, the frontend pre-computes merged knowledge for each target node and includes it in the build request:

```typescript
// In dialogs.ts build handler, for each target node:
const knowledge = knowledgeMerger.merge(
  [
    app.getSystemKnowledge(),
    app.getProjectKnowledge(),
    graphKnowledge,       // from current graph meta
    nodeKnowledge,        // from node._module_data
    portKnowledge         // per-port (appended in the per-node loop)
  ],
  { entity: { name: node.title, properties: node.properties, ... } }
);
```

The merged knowledge string is sent alongside `scope`, `mode`, and `include_testbench` in `POST /api/build`. The backend injects it into the system prompt sent to the LLM agent.

## Files Changed

| File | Change |
|------|--------|
| `src/types/graph-types.ts` | Add `knowledge?: string` to `PortData`, `GraphMeta`, `GraphNodeData`, `Connection`; add `knowledge_template?: string` to `GraphData`, `GraphMeta` |
| `src/constants.ts` | Add `SYSTEM_KNOWLEDGE` record |
| `src/core/knowledge-merger.ts` | **NEW** — `KnowledgeMerger` class |
| `src/ui/knowledge-preview.ts` | **NEW** — fullscreen overlay with copy/close |
| `src/ui/property-panel.ts` | Add collapsible "Knowledge" section + [Preview] button to graph/node/port views |
| `src/app.ts` | Instantiate `KnowledgeMerger`, add `getSystemKnowledge()` / `getProjectKnowledge()` methods |
| `src/ui/dialogs.ts` | Include merged knowledge in build request payload |
| `src/services/api.ts` | Add `knowledge` field to `startBuild()` params (if needed by backend) |

## Non-Goals (for this spec)

- **Backend knowledge storage changes** — the backend's `file_manager.py` already reads/writes YAML faithfully; adding `knowledge` fields to the YAML data model is transparent. No backend code changes needed.
- **Connection-level knowledge in UI** — the `Connection` interface gains `knowledge?` for data completeness, but the current UI has no inline connection editor; this is left for a future UI task.
- **Knowledge diff/merge in git history** — standard YAML text diffs cover knowledge fields naturally since they are inline.
- **Knowledge syntax highlighting in edit textareas** — plain `<textarea>` is sufficient for initial implementation.
