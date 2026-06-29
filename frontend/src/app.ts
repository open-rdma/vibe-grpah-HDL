import { TypeSystem } from './core/type-system';
import { ConnectionValidator } from './core/connection-validator';
import { GraphManager } from './core/graph-manager';
import { Project } from './core/project';
import { Toolbar } from './ui/toolbar';
import { ProjectPanel } from './ui/project-panel';
import { PropertyPanel } from './ui/property-panel';
import { TypeEditor } from './ui/type-editor';
import { showNewProjectDialog, showOpenProjectDialog, showBuildDialog } from './ui/dialogs';
import type { BuildDialogOptions } from './ui/dialogs';
import { showToast } from './ui/toast';
import { API } from './services/api';
import { RecentProjects } from './services/recent-projects';
import { KnowledgeMerger } from './core/knowledge-merger';
import { SYSTEM_KNOWLEDGE } from './constants';
import './nodes/boundary-nodes';

class App {
  _typeSystem: TypeSystem;
  _connectionValidator: ConnectionValidator;
  _project: Project;
  _graphManager: GraphManager;
  _canvas!: LGraphCanvas;
  _toolbar!: Toolbar;
  _projectPanel!: ProjectPanel;
  _propertyPanel!: PropertyPanel;
  _knowledgeMerger: KnowledgeMerger;
  _breadcrumbPath: { path: string; label: string }[];
  _origCloseSubgraph: (() => void) | null;

  get _targetLanguage(): string {
    const config = this._project.getConfig();
    const target = config?.properties?.target || 'bluespec';
    return target;
  }

  getSystemKnowledge(): string {
    return SYSTEM_KNOWLEDGE[this._targetLanguage] || SYSTEM_KNOWLEDGE.bluespec;
  }

  getProjectKnowledge(): string {
    // Project-level knowledge storage (project.yaml) not yet implemented.
    // Returns empty string for now.
    return '';
  }

  constructor() {
    this._typeSystem = new TypeSystem();
    this._connectionValidator = new ConnectionValidator(this._typeSystem);
    window.__connectionValidator = this._connectionValidator;
    window.__app = this;

    this._project = new Project();
    this._graphManager = new GraphManager(this._typeSystem);
    this._knowledgeMerger = new KnowledgeMerger();
    this._breadcrumbPath = [];
    this._origCloseSubgraph = null;

    this._initLayout();
    // Canvas is lazy-created on first project open
    this._showCanvasPlaceholder();
    this._initComponents();
  }

  _initLayout(): void {
    const app = document.getElementById('app')!;
    app.innerHTML = `
      <div id="toolbar"></div>
      <div id="breadcrumb-bar"></div>
      <div id="main-area">
        <div id="project-panel"></div>
        <div id="canvas-container"></div>
        <div id="property-panel"></div>
      </div>
      <div id="statusbar">
        <span id="status-text">Ready</span>
        <span id="status-center"></span>
        <span id="status-project">No project</span>
      </div>`;
  }

  _showCanvasPlaceholder(): void {
    const container = document.getElementById('canvas-container');
    if (container) {
      container.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-dim);text-align:center;">
        <div>
          <div style="font-size:16px;margin-bottom:6px;">Open or create a project to begin.</div>
        </div>
      </div>`;
    }
  }

  _ensureCanvas(): void {
    // Idempotent — only creates the litegraph canvas once
    if (this._canvas) return;
    this._initLiteGraph();
  }

  _initLiteGraph(): void {
    const container = document.getElementById('canvas-container')!;
    container.innerHTML = '';
    const canvasEl = document.createElement('canvas');
    canvasEl.id = 'graph-canvas';
    canvasEl.width = 2000;
    canvasEl.height = 2000;
    container.appendChild(canvasEl);

    const graph = new LiteGraph.LGraph();
    this._canvas = new LiteGraph.LGraphCanvas(canvasEl, graph);
    this._canvas.background_image = '';

    this._canvas.render_links_border = true;
    this._canvas.links_render_mode = LiteGraph.SPLINE_LINK;

    this._graphManager.setCanvas(this._canvas);

    // Track all litegraph-internal mutations (connections, node moves, etc.)
    graph.onAfterChange = () => {
      this._graphManager.markDirty();
    };

    this._canvas.onNodeSelected = (node: LGraphNode) => {
      if (node._is_boundary) {
        this._propertyPanel.clear();
      } else {
        this._propertyPanel.showNodeProperties(node);
      }
      this._updateStatus();
      this._toolbar.refresh();
    };
    this._canvas.onNodeDeselected = () => {
      this._propertyPanel.clear();
      this._updateStatus();
      this._toolbar.refresh();
    };

    let resizeTimer: ReturnType<typeof setTimeout> | null = null;
    const resizeCanvas = () => {
      if (resizeTimer) clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        const container = document.getElementById('canvas-container')!;
        const w = container.clientWidth;
        const h = container.clientHeight;
        canvasEl.width = w;
        canvasEl.height = h;
        canvasEl.style.width = w + 'px';
        canvasEl.style.height = h + 'px';
        if (this._canvas) this._canvas.draw(true, true);
      }, 150);
    };
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    // Track zoom from mouse wheel
    canvasEl.addEventListener('wheel', () => {
      setTimeout(() => this._updateStatus(), 50);
    });

    this._canvas.draw(true, true);

    // Handle drag-and-drop from project tree onto canvas
    const canvasContainer = document.getElementById('canvas-container')!;
    canvasContainer.addEventListener('dragover', (e: DragEvent) => {
      e.preventDefault();
      if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
    });
    canvasContainer.addEventListener('drop', async (e: DragEvent) => {
      e.preventDefault();
      const refPath = e.dataTransfer!.getData('text/plain');
      if (refPath) {
        try {
          await this._instantiateFromRef(refPath, e.clientX, e.clientY);
        } catch (err: any) {
          console.error('[drop] _instantiateFromRef failed:', err.message || err);
        }
      }
    });

    // Wrap openSubgraph/closeSubgraph to keep GraphManager state synced
    const canvas = this._canvas;
    const origOpenSubgraph = canvas.openSubgraph.bind(canvas);
    const origCloseSubgraph = canvas.closeSubgraph.bind(canvas);
    this._origCloseSubgraph = origCloseSubgraph;

    canvas.openSubgraph = (graph: LGraph) => {
      origOpenSubgraph(graph);
      this._canvas.draw(true, true);
      this._graphManager._syncFromCanvas();

      // Push breadcrumb entry for the subgraph
      const subNode = (graph as any)._subgraph_node;
      const subPath = graph.extra?.path || (subNode ? subNode._module_ref : '');
      const subLabel = subNode ? subNode.title : (subPath || 'subgraph');
      this._breadcrumbPath.push({ path: subPath || '', label: subLabel });
      this._renderBreadcrumb();
    };

    canvas.closeSubgraph = () => {
      this._graphManager._cacheCurrentState();

      // Invalidate subgraph cache on the owning node so the next
      // double-click rebuilds from fresh data (including any edits
      // just cached to _stateCache).
      const closingGraph = canvas.graph;
      const owningNode: LGraphNode | null =
        (closingGraph && (closingGraph as any)._subgraph_node) || null;
      const editedRefPath: string =
        (closingGraph && closingGraph.extra && closingGraph.extra.path) || '';

      if (owningNode) {
        owningNode._subgraph = undefined;
      }

      origCloseSubgraph();
      this._graphManager._syncFromCanvas();

      // Pop breadcrumb back to parent
      if (this._breadcrumbPath.length > 0) {
        this._breadcrumbPath.pop();
      }
      this._renderBreadcrumb();

      // Refresh all nodes in the parent graph that reference the
      // just-edited module so their port displays pick up any
      // additions/removals made inside the subgraph.
      if (editedRefPath) {
        this._refreshNodesForRef(editedRefPath);
      }
    };
  }

  async _instantiateFromRef(refPath: string, clientX: number, clientY: number): Promise<void> {
    if (!this._graphManager._graph) return;
    const parts = refPath.replace(/\\/g, '/').split('/');
    const fileName = parts[parts.length - 1].replace(/\.yaml$/, '');
    const baseName = fileName || 'module';

    const node = LiteGraph.createNode('rtl/module');
    node.title = this._graphManager.uniqueNodeName(baseName);
    node._module_ref = refPath;

    const canvasEl = document.getElementById('graph-canvas')!;
    const rect = canvasEl.getBoundingClientRect();
    const cx = clientX - rect.left;
    const cy = clientY - rect.top;
    const ds = this._canvas.ds;
    const canvasX = cx / ds.scale - ds.offset[0];
    const canvasY = cy / ds.scale - ds.offset[1];
    node.pos = [canvasX, canvasY];

    this._graphManager._graph!.add(node);
    this._graphManager.markDirty();
    await this._graphManager._loadRefPorts(node, refPath);
    if (this._canvas) this._canvas.draw(true, true);
  }

  _initComponents(): void {
    this._toolbar = new Toolbar(this);
    this._toolbar.init(document.getElementById('toolbar')!);

    this._projectPanel = new ProjectPanel(this);
    this._projectPanel.init(document.getElementById('project-panel')!);

    this._propertyPanel = new PropertyPanel(this);
    this._propertyPanel.init(document.getElementById('property-panel')!);
    this._propertyPanel.clear();

    this._typeSystem.loadFromServer();

    window.addEventListener('beforeunload', (e: BeforeUnloadEvent) => {
      if (this._graphManager.hasAnyUnsavedChanges()) {
        e.preventDefault();
        e.returnValue = '';
      }
    });
  }

  // === Toolbar actions ===

  async showNewProjectDialog(): Promise<void> {
    showNewProjectDialog(async (path: string, name: string) => {
      try {
        await this._project.create(path, name);
        RecentProjects.addRecentProject(path);
        this._ensureCanvas();
        this._updateStatus();
        this._toolbar.refresh();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project created: ' + name);
      } catch (e: any) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async showOpenProjectDialog(): Promise<void> {
    showOpenProjectDialog(async (path: string) => {
      try {
        await this._project.open(path);
        RecentProjects.addRecentProject(path);
        this._ensureCanvas();
        this._updateStatus();
        this._toolbar.refresh();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project opened');
      } catch (e: any) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async closeProject(): Promise<void> {
    if (!this._project.isOpen()) {
      showToast('No project open', 'error');
      return;
    }
    try {
      await this._project.close();
      this._destroyCanvas();
      this._graphManager.reset();
      this._showCanvasPlaceholder();
      this._updateStatus();
      this._toolbar.refresh();
      this._projectPanel.refresh([]);
      this._propertyPanel.clear();
      showToast('Project closed');
    } catch (e: any) {
      showToast('Close failed: ' + e.message, 'error');
    }
  }

  _destroyCanvas(): void {
    if (!this._canvas) return;
    const graph = this._graphManager._graph;
    if (graph) graph.onAfterChange = null;
    if (this._canvas) {
      this._canvas.onNodeSelected = null;
      this._canvas.onNodeDeselected = null;
    }
    this._canvas = undefined as any;
    this._graphManager.setCanvas(null);
    this._breadcrumbPath = [];
    this._renderBreadcrumb();
    const container = document.getElementById('canvas-container');
    if (container) container.innerHTML = '';
  }

  async saveCurrentGraph(): Promise<void> {
    if (!this._project.isOpen()) {
      showToast('No project open', 'error');
      return;
    }
    const graph = this._graphManager._graph;
    if (!graph) {
      showToast('No graph loaded', 'error');
      return;
    }
    const path = this._graphManager.getCurrentGraphPath();
    if (!path) {
      showToast('No graph loaded', 'error');
      return;
    }
    try {
      await this._graphManager.saveGraph(path);
      this._updateStatus();
      this._toolbar.refresh();
      showToast('Graph saved');
    } catch (e: any) {
      showToast('Save failed: ' + e.message, 'error');
    }
  }

  async openGraph(path: string): Promise<void> {
    try {
      await this._graphManager.loadGraph(path);
      // Reset breadcrumb to just this graph
      this._breadcrumbPath = [{ path, label: path }];
      this._renderBreadcrumb();
      this._updateStatus();
      this._toolbar.refresh();
      this._propertyPanel.clear();
      showToast('Opened: ' + path);
    } catch (e: any) {
      showToast('Open failed: ' + e.message, 'error');
    }
  }

  addSubgraphNode(): void {
    const graph = this._graphManager._graph;
    if (!graph) return;
    const node = LiteGraph.createNode('rtl/module');
    node.title = this._graphManager.uniqueNodeName('new_module');
    node.pos = [200, 200];
    graph.add(node);
    this._graphManager.markDirty();
    if (this._canvas) this._canvas.draw(true, true);
    this._toolbar.refresh();
  }

  deleteSelectedNodes(): void {
    if (!this._canvas) return;
    const selected = this._canvas.selected_nodes || {};
    for (const id of Object.keys(selected)) {
      const node = selected[id];
      this._graphManager.removeNode(node);
    }
    this._canvas.deselectAllNodes();
    this._graphManager.markDirty();
    this._canvas.draw(true, true);
    this._toolbar.refresh();
  }

  zoomIn(): void {
    if (this._canvas) {
      this._canvas.zoom(1.2, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
      this._updateStatus();
    }
  }

  zoomOut(): void {
    if (this._canvas) {
      this._canvas.zoom(0.8, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
      this._updateStatus();
    }
  }

  zoomToFit(): void {
    if (this._canvas) {
      this._canvas.zoomToFit();
      this._canvas.draw(true, true);
      this._updateStatus();
    }
  }

  showBuildDialog(): void {
    const graph = this._graphManager._graph;
    const currentPath = this._graphManager.getCurrentGraphPath() || 'top/top.yaml';

    // Compute graph-level knowledge
    const graphMeta = (graph && graph.extra && (graph.extra as any).meta) || {};
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

  async _pollBuild(taskId: string): Promise<void> {
    const interval = setInterval(async () => {
      try {
        const status = await API.getBuildStatus(taskId);
        if (status.status === 'done') {
          clearInterval(interval);
          showToast('Build complete!');
          this._updateStatus();
        } else if (status.status === 'failed') {
          clearInterval(interval);
          showToast('Build failed: ' + status.error, 'error');
        }
      } catch (e: any) {
        clearInterval(interval);
        showToast('Build status check failed: ' + (e.message || 'unknown error'), 'error');
      }
    }, 2000);
  }

  showTypeEditor(): void {
    const editor = new TypeEditor(this._typeSystem, () => {});
    editor.show();
  }

  redraw(): void {
    if (this._canvas) this._canvas.draw(true, true);
  }

  async _refreshNodesForRef(refPath: string): Promise<void> {
    const graph = this._graphManager._graph;
    if (!graph || !refPath) return;
    for (const node of graph._nodes || []) {
      if (node._module_ref === refPath) {
        await this._graphManager._loadRefPorts(node, refPath);
      }
    }
    if (this._canvas) {
      this._canvas.draw(true, true);
    }
  }

  _renderBreadcrumb(): void {
    const bar = document.getElementById('breadcrumb-bar');
    if (!bar) return;
    bar.innerHTML = '';

    const path = this._breadcrumbPath;
    if (path.length === 0) return;

    for (let i = 0; i < path.length; i++) {
      if (i > 0) {
        const sep = document.createElement('span');
        sep.className = 'crumb-sep';
        sep.textContent = '\u203A'; // ›
        bar.appendChild(sep);
      }
      const crumb = document.createElement('span');
      const isLast = i === path.length - 1;
      crumb.className = 'crumb' + (isLast ? ' current' : '');
      crumb.textContent = path[i].label;
      if (!isLast) {
        crumb.addEventListener('click', () => this._navigateBreadcrumb(i));
      }
      bar.appendChild(crumb);
    }
  }

  _navigateBreadcrumb(index: number): void {
    // Close subgraphs until we reach the target depth.
    // Use the unwrapped origCloseSubgraph to avoid double-popping breadcrumb state.
    while (this._breadcrumbPath.length - 1 > index) {
      this._graphManager._cacheCurrentState();

      // Invalidate subgraph cache on the owning node (same as closeSubgraph wrapper)
      const closingGraph = this._canvas?.graph;
      const owningNode: LGraphNode | null =
        (closingGraph && (closingGraph as any)._subgraph_node) || null;
      const editedRefPath: string =
        (closingGraph && closingGraph.extra && closingGraph.extra.path) || '';

      if (owningNode) {
        owningNode._subgraph = undefined;
      }

      if (this._origCloseSubgraph) this._origCloseSubgraph();
      this._graphManager._syncFromCanvas();
      this._breadcrumbPath.pop();

      // Refresh ports on parent nodes that reference the just-edited module
      if (editedRefPath) {
        this._refreshNodesForRef(editedRefPath);
      }
    }
    this._renderBreadcrumb();
  }

  _updateStatus(): void {
    const statusEl = document.getElementById('status-text')!;
    const projEl = document.getElementById('status-project')!;
    const centerEl = document.getElementById('status-center')!;
    if (this._project.isOpen()) {
      projEl.textContent = 'Project: ' + this._project.getConfig()!.name;
    }
    const graph = this._graphManager._graph;
    if (graph && graph.extra.path) {
      let indicator = '';
      let color = '';
      if (this._graphManager.isDirty()) {
        indicator = ' \u25CF';
        color = 'var(--warning, #e0a000)';
      } else if (this._graphManager._stateCache.size > 0) {
        indicator = ' \u25CF';
        color = '#888';
      }
      statusEl.textContent = 'Graph: ' + graph.extra.path + indicator;
      statusEl.style.color = color;
    }

    const parts: string[] = [];
    if (this._canvas) {
      const zoomPct = Math.round(this._canvas.ds.scale * 100);
      parts.push('Zoom: ' + zoomPct + '%');
    }
    const selCount = this._canvas ? Object.keys(this._canvas.selected_nodes || {}).length : 0;
    if (selCount > 0) {
      parts.push(selCount + ' selected');
    }
    centerEl.textContent = parts.join('  ');
  }
}

export { App };
