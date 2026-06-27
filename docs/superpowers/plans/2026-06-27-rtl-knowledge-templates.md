# RTL Knowledge Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add hierarchical, cascading knowledge snippets to every level of the RTL data model (system→project→graph→node→port), with markdown + `{{variable}}` interpolation, collapsible UI editing, fullscreen preview overlay, and integration into the build pipeline.

**Architecture:** Inline `knowledge?: string` fields on existing TypeScript interfaces cascade via a stateless `KnowledgeMerger` utility class. A new `KnowledgePreview` component renders merged prompts in a fullscreen overlay. The `PropertyPanel` gains collapsible Knowledge sections per view, and the `App` owns the merger instance. Build requests include merged knowledge in the POST body.

**Tech Stack:** TypeScript (frontend only), litegraph.js (canvas), vanilla DOM manipulation (no framework)

## Global Constraints

- All changes are additive to existing interfaces — no breaking changes to `PortData`, `GraphMeta`, `GraphNodeData`, `Connection`, or `GraphData`
- `knowledge` fields are optional (`knowledge?: string`) — empty/absent means no contribution to merged prompt
- `knowledge_template` uses `{{children}}` placeholder; when absent, child content is appended directly with `\n\n---\n\n` separator
- Variable interpolation: `{{name}}`, `{{direction}}`, `{{category}}`, `{{type}}`, `{{properties.FOO}}`, `{{description}}` — unresolved variables left as-is
- System knowledge hardcoded in `constants.ts` under `SYSTEM_KNOWLEDGE` keyed by language (`verilog` | `vhdl` | `bluespec`)
- `KnowledgeMerger` is stateless — pure functions operating on string arrays and context objects
- `KnowledgePreview` overlay closes on Escape, backdrop click, or [Close] button; [Copy] writes merged text to clipboard
- Verification: `npx tsc --noEmit` (type check) and `npx vite build` (production build) must both pass at each task boundary
- No backend changes needed — backend `file_manager.py` reads/writes YAML transparently
- Connection-level `knowledge?` is added to the type but NOT surfaced in the UI in this plan

---

### Task 1: Data Model Foundation — Types, Constants, and KnowledgeMerger

**Files:**
- Modify: `frontend/src/types/graph-types.ts`
- Modify: `frontend/src/constants.ts`
- Create: `frontend/src/core/knowledge-merger.ts`

**Interfaces:**
- Consumes: Existing `PortData`, `GraphMeta`, `GraphNodeData`, `Connection`, `GraphData` interfaces
- Produces:
  - `PortData.knowledge?: string`
  - `GraphMeta.knowledge?: string`, `GraphMeta.knowledge_template?: string`
  - `GraphNodeData.knowledge?: string`
  - `Connection.knowledge?: string`
  - `GraphData.knowledge_template?: string`
  - `SYSTEM_KNOWLEDGE: Record<string, string>` (exported from constants.ts)
  - `KnowledgeMerger` class with `merge(levels, context, template?)`, `_interpolate(template, entity)`, `_resolve(entity, path)`
  - `KnowledgeContext` interface: `{ entity: Record<string, any> }`

- [ ] **Step 1: Add `knowledge` and `knowledge_template` fields to graph-types.ts**

Add optional `knowledge?: string` to `PortData`, `GraphMeta`, `GraphNodeData`, and `Connection`. Add optional `knowledge_template?: string` to `GraphData` and `GraphMeta`.

In `frontend/src/types/graph-types.ts`, modify each interface:

```typescript
export interface PortData {
  name: string;
  direction: 'input' | 'output';
  category: 'clock' | 'reset' | 'data';
  type?: string;
  clock_domain?: string;
  reset_domain?: string;
  reset_type?: 'async' | 'sync';
  allow_cross_domain?: boolean;
  knowledge?: string;
}

export interface GraphMeta {
  name: string;
  description?: string;
  test_method?: string;
  knowledge?: string;
  knowledge_template?: string;
}

export interface GraphNodeData {
  id: string;
  ref: string;
  description?: string;
  test_method?: string;
  pos_x: number;
  pos_y: number;
  size_w?: number;
  size_h?: number;
  collapsed?: boolean;
  properties: Record<string, string>;
  knowledge?: string;
}

export interface Connection {
  from: ConnectionTarget;
  to: ConnectionTarget[];
  allow_cross_domain?: boolean;
  description?: string;
  knowledge?: string;
}

export interface GraphData {
  meta: GraphMeta;
  properties: Record<string, any>;
  ports: PortData[];
  nodes: GraphNodeData[];
  connections: Connection[];
  canvas?: CanvasViewport;
  knowledge_template?: string;
}
```

- [ ] **Step 2: Add `SYSTEM_KNOWLEDGE` record to constants.ts**

In `frontend/src/constants.ts`, append after the existing exports:

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

- [ ] **Step 3: Create `KnowledgeMerger` class**

Create `frontend/src/core/knowledge-merger.ts`:

```typescript
export interface KnowledgeContext {
  entity: Record<string, any>;
}

export class KnowledgeMerger {
  /**
   * Merge knowledge levels from outer to inner.
   * `levels` is ordered outermost-first (system, project, graph, node, port).
   * Empty/undefined levels are skipped.
   * `context.entity` provides data for {{variable}} interpolation on the
   * innermost level (typically the port or node being rendered).
   */
  merge(levels: (string | undefined)[], context: KnowledgeContext, template?: string): string {
    const parts: string[] = [];
    for (let i = 0; i < levels.length; i++) {
      const raw = levels[i];
      if (!raw || raw.trim() === '') continue;
      parts.push(this._interpolate(raw, context.entity));
    }
    const body = parts.join('\n\n---\n\n');
    if (template && body) {
      return template.replace(/\{\{children\}\}/g, body);
    }
    return body;
  }

  /**
   * Render a template string with {{variable}} interpolation.
   * Unresolved variables are left as-is.
   */
  _interpolate(template: string, entity: Record<string, any>): string {
    return template.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (_match, path: string) => {
      return this._resolve(entity, path);
    });
  }

  /**
   * Resolve a dotted path like "properties.clock_freq_mhz" from the entity.
   * Returns the string value, or the original {{pattern}} if unresolvable.
   */
  _resolve(entity: Record<string, any>, path: string): string {
    const parts = path.split('.');
    let current: any = entity;
    for (const part of parts) {
      if (current == null || typeof current !== 'object') {
        return `{{${path}}}`;
      }
      if (part in current) {
        current = current[part];
      } else {
        return `{{${path}}}`;
      }
    }
    if (current == null) return `{{${path}}}`;
    return String(current);
  }
}
```

- [ ] **Step 4: Verify type check passes**

Run: `cd D:/study/hw-visual-design/frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 5: Verify build passes**

Run: `cd D:/study/hw-visual-design/frontend && npx vite build`

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
cd D:/study/hw-visual-design/frontend
git add src/types/graph-types.ts src/constants.ts src/core/knowledge-merger.ts
git commit -m "feat: add knowledge data model, SYSTEM_KNOWLEDGE, and KnowledgeMerger class

Co-Authored-By: deepseek-v4-pro <deepseek-ai@claude-code-best.win>"
```

---

### Task 2: Knowledge Preview Overlay

**Files:**
- Create: `frontend/src/ui/knowledge-preview.ts`

**Interfaces:**
- Consumes: (none — standalone component)
- Produces:
  - `KnowledgePreview` class with static `show(title: string, content: string): void`
  - Internal `_close(overlay: HTMLDivElement): void`

- [ ] **Step 1: Create `KnowledgePreview` fullscreen overlay**

Create `frontend/src/ui/knowledge-preview.ts`:

```typescript
export class KnowledgePreview {
  /**
   * Show a fullscreen floating overlay with merged knowledge text.
   * @param title  Entity path label (e.g., "Port clk · top/top.yaml")
   * @param content  The full merged knowledge text to display
   */
  static show(title: string, content: string): void {
    const overlay = document.createElement('div');
    overlay.style.cssText =
      'position:fixed; top:0; left:0; right:0; bottom:0;' +
      'background:rgba(0,0,0,0.7); z-index:10000;' +
      'display:flex; align-items:center; justify-content:center;';

    const box = document.createElement('div');
    box.style.cssText =
      'background:#1e1e1e; border:1px solid #444; border-radius:8px;' +
      'max-width:800px; width:90vw; max-height:80vh;' +
      'display:flex; flex-direction:column; overflow:hidden;';

    // Header bar
    const header = document.createElement('div');
    header.style.cssText =
      'display:flex; align-items:center; gap:12px;' +
      'padding:10px 16px; border-bottom:1px solid #333; flex-shrink:0;';
    const titleEl = document.createElement('span');
    titleEl.style.cssText = 'flex:1; font-size:14px; font-weight:600; color:#ddd;';
    titleEl.textContent = '\u270E Knowledge Preview \u2014 ' + title;

    const copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy';
    copyBtn.style.cssText =
      'padding:4px 12px; font-size:12px; background:#3a3a3a; color:#ccc;' +
      'border:1px solid #555; border-radius:4px; cursor:pointer;';
    copyBtn.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
      } catch {
        copyBtn.textContent = 'Failed';
        setTimeout(() => { copyBtn.textContent = 'Copy'; }, 2000);
      }
    });

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '\u2715 Close';
    closeBtn.style.cssText =
      'padding:4px 12px; font-size:12px; background:#3a3a3a; color:#ccc;' +
      'border:1px solid #555; border-radius:4px; cursor:pointer;';
    closeBtn.addEventListener('click', () => KnowledgePreview._close(overlay));

    header.appendChild(titleEl);
    header.appendChild(copyBtn);
    header.appendChild(closeBtn);

    // Content area
    const contentEl = document.createElement('pre');
    contentEl.style.cssText =
      'flex:1; overflow:auto; padding:16px; margin:0;' +
      'font-family:Consolas,monospace; font-size:12px; line-height:1.6;' +
      'color:#ccc; white-space:pre-wrap; word-break:break-word;';
    contentEl.textContent = content;

    box.appendChild(header);
    box.appendChild(contentEl);
    overlay.appendChild(box);

    // Close on backdrop click
    overlay.addEventListener('click', (e: MouseEvent) => {
      if (e.target === overlay) KnowledgePreview._close(overlay);
    });

    // Close on Escape
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        KnowledgePreview._close(overlay);
        document.removeEventListener('keydown', onKey);
      }
    };
    document.addEventListener('keydown', onKey);

    document.body.appendChild(overlay);
  }

  private static _close(overlay: HTMLDivElement): void {
    overlay.remove();
  }
}
```

- [ ] **Step 2: Verify type check passes**

Run: `cd D:/study/hw-visual-design/frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 3: Verify build passes**

Run: `cd D:/study/hw-visual-design/frontend && npx vite build`

Expected: Build succeeds.

- [ ] **Step 4: Commit**

```bash
cd D:/study/hw-visual-design/frontend
git add src/ui/knowledge-preview.ts
git commit -m "feat: add KnowledgePreview fullscreen overlay with copy/close

Co-Authored-By: deepseek-v4-pro <deepseek-ai@claude-code-best.win>"
```

---

### Task 3: Property Panel Knowledge Sections

**Files:**
- Modify: `frontend/src/ui/property-panel.ts`

**Interfaces:**
- Consumes:
  - `KnowledgePreview.show(title, content)` from Task 2
  - `App._knowledgeMerger` (will be added in Task 4 — use a guard: `if (!this._app._knowledgeMerger) return;`)
  - `App.getSystemKnowledge()` (guard similarly)
  - `App.getProjectKnowledge()` (guard similarly)
- Produces:
  - Collapsible "Knowledge" section in `_showGraphProperties()`, `showNodeProperties()`, `showPortProperties()`
  - Each section has a `<textarea>` bound to the entity's `knowledge` field and a [Preview] button

- [ ] **Step 1: Add import for KnowledgePreview**

In `frontend/src/ui/property-panel.ts`, add the import at the top:

```typescript
import { KnowledgePreview } from './knowledge-preview';
```

Insert this line after the existing `import { showToast } from './toast';` line.

- [ ] **Step 2: Add Knowledge section to `_showGraphProperties`**

In the `_showGraphProperties` method, append after the existing sections (after the Test Method textarea), before the closing `}`:

```typescript
    // Knowledge section
    this._addHeading('Knowledge');
    const metaKnowledge = meta.knowledge || '';
    const knowledgeHeading = this._el!.lastElementChild as HTMLElement;
    if (knowledgeHeading) {
      knowledgeHeading.textContent = 'Knowledge' + (metaKnowledge.trim() ? ' [\u270E]' : '');
      knowledgeHeading.style.cursor = 'pointer';
      const knowledgeContainer = document.createElement('div');
      let knowledgeCollapsed = false;
      knowledgeHeading.addEventListener('click', () => {
        knowledgeCollapsed = !knowledgeCollapsed;
        knowledgeContainer.style.display = knowledgeCollapsed ? 'none' : '';
      });
      this._el!.appendChild(knowledgeContainer);

      const ta = document.createElement('textarea');
      ta.value = metaKnowledge;
      ta.placeholder = 'Markdown knowledge for this module. Use {{name}}, {{direction}}, {{category}}, {{type}}, {{properties.FOO}}, {{description}} for interpolation.';
      ta.addEventListener('input', () => {
        meta.knowledge = ta.value;
        this._app._graphManager.markDirty();
      });
      knowledgeContainer.appendChild(ta);

      const previewBtn = document.createElement('button');
      previewBtn.textContent = 'Preview';
      previewBtn.style.cssText = 'margin-top:4px; width:100%;';
      previewBtn.addEventListener('click', () => {
        const merger = this._app._knowledgeMerger;
        if (!merger) {
          showToast('Knowledge system not available', 'error');
          return;
        }
        const graph = this._app._graphManager._graph;
        const levels: (string | undefined)[] = [
          this._app.getSystemKnowledge(),
          this._app.getProjectKnowledge(),
          meta.knowledge
        ];
        const merged = merger.merge(levels, { entity: { ...meta, properties: graph.extra.properties || {} } });
        KnowledgePreview.show('Graph \u00b7 ' + (meta.name || 'unnamed'), merged);
      });
      knowledgeContainer.appendChild(previewBtn);

      // Knowledge Template
      const tmplLabel = document.createElement('label');
      tmplLabel.textContent = 'Knowledge Template';
      tmplLabel.style.cssText = 'display:block; margin-top:8px; font-size:10px; color:var(--text-dim); text-transform:uppercase;';
      knowledgeContainer.appendChild(tmplLabel);
      const tmplTa = document.createElement('textarea');
      tmplTa.value = graph.extra.knowledge_template || '';
      tmplTa.placeholder = 'Use {{children}} as placeholder for sub-level content.';
      tmplTa.addEventListener('input', () => {
        graph.extra.knowledge_template = tmplTa.value;
        this._app._graphManager.markDirty();
      });
      knowledgeContainer.appendChild(tmplTa);
    }
```

- [ ] **Step 3: Add Knowledge section to `showNodeProperties`**

In the `showNodeProperties` method, append after the Ports section (after the port list loop), before the closing `}`:

```typescript
    this._addHeading('Knowledge');
    const nodeKnowledge = data.knowledge || '';
    const nkHeading = this._el!.lastElementChild as HTMLElement;
    if (nkHeading) {
      nkHeading.textContent = 'Knowledge' + (nodeKnowledge.trim() ? ' [\u270E]' : '');
      nkHeading.style.cursor = 'pointer';
      const nkContainer = document.createElement('div');
      let nkCollapsed = false;
      nkHeading.addEventListener('click', () => {
        nkCollapsed = !nkCollapsed;
        nkContainer.style.display = nkCollapsed ? 'none' : '';
      });
      this._el!.appendChild(nkContainer);

      const ta = document.createElement('textarea');
      ta.value = nodeKnowledge;
      ta.placeholder = 'Markdown knowledge for this node instance.';
      ta.addEventListener('input', () => {
        data.knowledge = ta.value;
        node._module_data = data;
        this._app._graphManager.markDirty();
      });
      nkContainer.appendChild(ta);

      const previewBtn = document.createElement('button');
      previewBtn.textContent = 'Preview';
      previewBtn.style.cssText = 'margin-top:4px; width:100%;';
      previewBtn.addEventListener('click', () => {
        const merger = this._app._knowledgeMerger;
        if (!merger) {
          showToast('Knowledge system not available', 'error');
          return;
        }
        const graph = this._app._graphManager._graph;
        const graphMeta = (graph && graph.extra && graph.extra.meta) || {};
        const levels: (string | undefined)[] = [
          this._app.getSystemKnowledge(),
          this._app.getProjectKnowledge(),
          graphMeta.knowledge,
          data.knowledge
        ];
        const template = graph.extra.knowledge_template || graphMeta.knowledge_template || undefined;
        const merged = merger.merge(levels, { entity: { name: node.title, properties: node.properties || {}, description: data.description } }, template);
        KnowledgePreview.show('Node \u00b7 ' + (node.title || 'unnamed'), merged);
      });
      nkContainer.appendChild(previewBtn);
    }
```

- [ ] **Step 4: Add Knowledge section to `showPortProperties`**

In the `showPortProperties` method, after the existing port fields (before the Back button at the end), add:

```typescript
    this._addHeading('Knowledge');
    const portKnowledge = portData.knowledge || '';
    const pkHeading = this._el!.lastElementChild as HTMLElement;
    if (pkHeading) {
      pkHeading.textContent = 'Knowledge' + (portKnowledge.trim() ? ' [\u270E]' : '');
      pkHeading.style.cursor = 'pointer';
      const pkContainer = document.createElement('div');
      let pkCollapsed = false;
      pkHeading.addEventListener('click', () => {
        pkCollapsed = !pkCollapsed;
        pkContainer.style.display = pkCollapsed ? 'none' : '';
      });
      this._el!.appendChild(pkContainer);

      const ta = document.createElement('textarea');
      ta.value = portKnowledge;
      ta.placeholder = 'Markdown knowledge for this port. Use {{name}}, {{direction}}, {{category}}, {{type}} for interpolation.';
      ta.addEventListener('input', () => {
        portData.knowledge = ta.value;
        slot._port_data = portData;
        this._app._graphManager.markDirty();
      });
      pkContainer.appendChild(ta);

      const previewBtn = document.createElement('button');
      previewBtn.textContent = 'Preview';
      previewBtn.style.cssText = 'margin-top:4px; width:100%;';
      previewBtn.addEventListener('click', () => {
        const merger = this._app._knowledgeMerger;
        if (!merger) {
          showToast('Knowledge system not available', 'error');
          return;
        }
        const graph = this._app._graphManager._graph;
        const graphMeta = (graph && graph.extra && graph.extra.meta) || {};
        const nodeData = node._module_data || {};
        const levels: (string | undefined)[] = [
          this._app.getSystemKnowledge(),
          this._app.getProjectKnowledge(),
          graphMeta.knowledge,
          nodeData.knowledge,
          portData.knowledge
        ];
        const entity: Record<string, any> = {
          name: slot.name,
          direction: direction,
          category: portData.category,
          type: portData.type || '',
          properties: node.properties || {}
        };
        const template = graph.extra.knowledge_template || graphMeta.knowledge_template || undefined;
        const merged = merger.merge(levels, { entity }, template);
        KnowledgePreview.show('Port \u00b7 ' + slot.name + ' \u00b7 ' + (node.title || 'unnamed'), merged);
      });
      pkContainer.appendChild(previewBtn);
    }
```

- [ ] **Step 5: Verify type check passes**

Run: `cd D:/study/hw-visual-design/frontend && npx tsc --noEmit`

Expected: No type errors. If there are errors about `_knowledgeMerger` or `getSystemKnowledge` / `getProjectKnowledge` not existing on `App`, add temporary declarations in `app.ts` in the same step (or add the guard checks that avoid calling them).

Note: The `_knowledgeMerger` and `getSystemKnowledge()` / `getProjectKnowledge()` methods won't exist on `App` until Task 4. Add stub declarations to `app.ts` now to satisfy the compiler:

In `frontend/src/app.ts`, inside the `App` class, add:

```typescript
  _knowledgeMerger: any = null;
  getSystemKnowledge(): string { return ''; }
  getProjectKnowledge(): string { return ''; }
```

- [ ] **Step 6: Verify build passes**

Run: `cd D:/study/hw-visual-design/frontend && npx vite build`

Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
cd D:/study/hw-visual-design/frontend
git add src/ui/property-panel.ts src/app.ts
git commit -m "feat: add Knowledge collapsible sections to graph/node/port property views

Co-Authored-By: deepseek-v4-pro <deepseek-ai@claude-code-best.win>"
```

---

### Task 4: App Integration

**Files:**
- Modify: `frontend/src/app.ts`

**Interfaces:**
- Consumes:
  - `KnowledgeMerger` class from Task 1
  - Stub fields/methods from Task 3 (to be replaced with real implementations)
- Produces:
  - `App._knowledgeMerger: KnowledgeMerger` (real instance)
  - `App._targetLanguage: string` getter
  - `App.getSystemKnowledge(): string` (real implementation)
  - `App.getProjectKnowledge(): string` (real implementation)

- [ ] **Step 1: Add import for KnowledgeMerger**

In `frontend/src/app.ts`, add the import after the existing imports:

```typescript
import { KnowledgeMerger } from './core/knowledge-merger';
import { SYSTEM_KNOWLEDGE } from './constants';
```

- [ ] **Step 2: Initialize KnowledgeMerger in constructor**

In the `App` constructor, add after `this._graphManager = new GraphManager(this._typeSystem);`:

```typescript
    this._knowledgeMerger = new KnowledgeMerger();
```

- [ ] **Step 3: Replace stubs with real methods**

Replace the stub `_knowledgeMerger: any = null;` field declaration (added in Task 3) with:

```typescript
  _knowledgeMerger: KnowledgeMerger;
```

Replace the stub `getSystemKnowledge(): string` with:

```typescript
  get _targetLanguage(): string {
    const config = this._project.getConfig();
    const target = config?.properties?.target || 'bluespec';
    return target;
  }

  getSystemKnowledge(): string {
    return SYSTEM_KNOWLEDGE[this._targetLanguage] || SYSTEM_KNOWLEDGE.bluespec;
  }
```

Replace the stub `getProjectKnowledge(): string` with:

```typescript
  getProjectKnowledge(): string {
    // Project-level knowledge storage (project.yaml) not yet implemented.
    // Returns empty string for now.
    return '';
  }
```

- [ ] **Step 4: Verify type check passes**

Run: `cd D:/study/hw-visual-design/frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 5: Verify build passes**

Run: `cd D:/study/hw-visual-design/frontend && npx vite build`

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
cd D:/study/hw-visual-design/frontend
git add src/app.ts
git commit -m "feat: integrate KnowledgeMerger into App with system/project knowledge methods

Co-Authored-By: deepseek-v4-pro <deepseek-ai@claude-code-best.win>"
```

---

### Task 5: Build Pipeline Integration

**Files:**
- Modify: `frontend/src/ui/dialogs.ts`
- Modify: `frontend/src/services/api.ts`
- Modify: `frontend/src/app.ts` (the `showBuildDialog` method)

**Interfaces:**
- Consumes:
  - `App._knowledgeMerger`, `App.getSystemKnowledge()`, `App.getProjectKnowledge()` from Task 4
  - `BuildDialogOptions` (currently has `scope`, `mode`, `includeTestbench`)
  - `API.startBuild` (currently takes `targetNode, scope, mode, includeTestbench`)
- Produces:
  - `BuildDialogOptions.knowledge: string`
  - `API.startBuild` accepts `knowledge` parameter, sends it in POST body
  - `App.showBuildDialog` computes merged graph knowledge and passes it

- [ ] **Step 1: Add `knowledge` field to `BuildDialogOptions`**

In `frontend/src/ui/dialogs.ts`, modify the interface:

```typescript
interface BuildDialogOptions {
  scope: string;
  mode: string;
  includeTestbench: boolean;
  knowledge: string;
}
```

- [ ] **Step 2: Add `knowledge` parameter to `API.startBuild`**

In `frontend/src/services/api.ts`, modify the `startBuild` method signature and body:

```typescript
  startBuild(targetNode: string, scope: string, mode: string, includeTestbench: boolean, knowledge: string): Promise<{ task_id: string }> {
    return this._post('/api/build', { target_node: targetNode, scope, mode, include_testbench: includeTestbench, knowledge });
  },
```

- [ ] **Step 3: Compute and pass knowledge in `App.showBuildDialog`**

In `frontend/src/app.ts`, modify the `showBuildDialog` method to compute merged knowledge before calling the dialog:

```typescript
  showBuildDialog(): void {
    const graph = this._graphManager._graph;
    const currentPath = (graph ? graph.extra.path : null) || 'top/top.yaml';

    // Compute graph-level knowledge
    const graphMeta = (graph && graph.extra && graph.extra.meta) || {};
    const graphKnowledge = this._knowledgeMerger.merge(
      [
        this.getSystemKnowledge(),
        this.getProjectKnowledge(),
        graphMeta.knowledge
      ],
      { entity: graphMeta }
    );

    showBuildDialog(async (opts: BuildDialogOptions) => {
      try {
        const resp = await API.startBuild(currentPath, opts.scope, opts.mode, opts.includeTestbench, opts.knowledge);
        showToast('Build started: ' + resp.task_id);
        this._pollBuild(resp.task_id);
      } catch (e: any) {
        showToast('Build failed: ' + e.message, 'error');
      }
    }, graphKnowledge);
  }
```

- [ ] **Step 4: Pass `knowledge` to `showBuildDialog` as a parameter**

Modify `showBuildDialog` function in `frontend/src/ui/dialogs.ts` to accept the knowledge string:

```typescript
function showBuildDialog(onBuild: (opts: BuildDialogOptions) => void, knowledge: string): void {
```

And in the Build button's onClick, include knowledge in the opts:

```typescript
      label: 'Build',
      onClick: (body) => {
        if (onBuild) {
          onBuild({
            scope: (body.querySelector('#build-scope') as HTMLSelectElement).value,
            mode: (body.querySelector('#build-mode') as HTMLSelectElement).value,
            includeTestbench: (body.querySelector('#build-tb') as HTMLInputElement).checked,
            knowledge: knowledge
          });
        }
      }
```

- [ ] **Step 5: Verify type check passes**

Run: `cd D:/study/hw-visual-design/frontend && npx tsc --noEmit`

Expected: No type errors.

- [ ] **Step 6: Verify build passes**

Run: `cd D:/study/hw-visual-design/frontend && npx vite build`

Expected: Build succeeds.

- [ ] **Step 7: Commit**

```bash
cd D:/study/hw-visual-design/frontend
git add src/ui/dialogs.ts src/services/api.ts src/app.ts
git commit -m "feat: include merged knowledge in build pipeline requests

Co-Authored-By: deepseek-v4-pro <deepseek-ai@claude-code-best.win>"
```

---
