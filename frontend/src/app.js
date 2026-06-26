import { TypeSystem } from './core/type-system.js';
import { ConnectionValidator } from './core/connection-validator.js';
import { GraphManager } from './core/graph-manager.js';
import { Project } from './core/project.js';
import { Toolbar } from './ui/toolbar.js';
import { ProjectPanel } from './ui/project-panel.js';
import { PropertyPanel } from './ui/property-panel.js';
import { TypeEditor } from './ui/type-editor.js';
import { showNewProjectDialog, showOpenProjectDialog, showBuildDialog } from './ui/dialogs.js';
import { API } from './services/api.js';

class App {
  constructor() {
    this._typeSystem = new TypeSystem();
    this._connectionValidator = new ConnectionValidator(this._typeSystem);
    window.__connectionValidator = this._connectionValidator;

    this._project = new Project();
    this._graphManager = new GraphManager(this._typeSystem);

    this._initLayout();
    this._initLiteGraph();
    this._initComponents();
  }

  _initLayout() {
    const app = document.getElementById('app');
    app.innerHTML = `
      <div id="toolbar"></div>
      <div id="main-area">
        <div id="project-panel"></div>
        <div id="canvas-container"></div>
        <div id="property-panel"></div>
      </div>
      <div id="statusbar">
        <span id="status-text">Ready</span>
        <span id="status-project">No project</span>
      </div>`;
  }

  _initLiteGraph() {
    const canvasEl = document.createElement('canvas');
    canvasEl.id = 'graph-canvas';
    canvasEl.width = 2000;
    canvasEl.height = 2000;
    document.getElementById('canvas-container').appendChild(canvasEl);

    const graph = new LiteGraph.LGraph();
    this._canvas = new LiteGraph.LGraphCanvas(canvasEl, graph);
    this._canvas.background_image = '';

    this._canvas.render_links_border = true;
    this._canvas.links_render_mode = LiteGraph.SPLINE_LINK;

    this._graphManager.setCanvas(this._canvas);

    this._canvas.onNodeSelected = (node) => {
      this._propertyPanel.showNodeProperties(node);
    };
    this._canvas.onNodeDeselected = () => {
      this._propertyPanel.clear();
    };

    const resizeCanvas = () => {
      const container = document.getElementById('canvas-container');
      canvasEl.width = container.clientWidth;
      canvasEl.height = container.clientHeight;
      if (this._canvas) this._canvas.draw(true, true);
    };
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    this._canvas.draw(true, true);
  }

  _initComponents() {
    this._toolbar = new Toolbar(this);
    this._toolbar.init(document.getElementById('toolbar'));

    this._projectPanel = new ProjectPanel(this);
    this._projectPanel.init(document.getElementById('project-panel'));

    this._propertyPanel = new PropertyPanel(this);
    this._propertyPanel.init(document.getElementById('property-panel'));
    this._propertyPanel.clear();

    this._typeSystem.loadFromServer();
  }

  // === Toolbar actions ===

  async showNewProjectDialog() {
    showNewProjectDialog(async (path, name) => {
      try {
        await this._project.create(path, name);
        this._updateStatus();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project created: ' + name);
      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async showOpenProjectDialog() {
    showOpenProjectDialog(async (path) => {
      try {
        await this._project.open(path);
        this._updateStatus();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project opened');
      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async saveCurrentGraph() {
    if (!this._project.isOpen()) {
      showToast('No project open', 'error');
      return;
    }
    const path = this._graphManager._graph.extra.path;
    if (!path) {
      showToast('No graph loaded', 'error');
      return;
    }
    try {
      await this._graphManager.saveGraph(path);
      this._updateStatus();
      showToast('Graph saved');
    } catch (e) {
      showToast('Save failed: ' + e.message, 'error');
    }
  }

  async openGraph(path) {
    try {
      await this._graphManager.loadGraph(path);
      this._updateStatus();
      this._propertyPanel.clear();
      showToast('Opened: ' + path);
    } catch (e) {
      showToast('Open failed: ' + e.message, 'error');
    }
  }

  addSubgraphNode() {
    const node = LiteGraph.createNode('rtl/module');
    node.title = 'new_module';
    node.pos = [200, 200];
    this._graphManager._graph.add(node);
    if (this._canvas) this._canvas.draw(true, true);
  }

  deleteSelectedNodes() {
    if (!this._canvas) return;
    const selected = this._canvas.selected_nodes || {};
    for (const id of Object.keys(selected)) {
      const node = selected[id];
      node.graph.remove(node);
    }
    this._canvas.deselectAllNodes();
    this._canvas.draw(true, true);
  }

  zoomIn() {
    if (this._canvas) {
      this._canvas.zoom(1.2, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
    }
  }

  zoomOut() {
    if (this._canvas) {
      this._canvas.zoom(0.8, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
    }
  }

  zoomToFit() {
    if (this._canvas) this._canvas.zoomToFit();
  }

  showBuildDialog() {
    const currentPath = this._graphManager._graph.extra.path || 'top/top.yaml';
    showBuildDialog(async (opts) => {
      try {
        const resp = await API.startBuild(currentPath, opts.scope, opts.mode, opts.includeTestbench);
        showToast('Build started: ' + resp.task_id);
        this._pollBuild(resp.task_id);
      } catch (e) {
        showToast('Build failed: ' + e.message, 'error');
      }
    });
  }

  async _pollBuild(taskId) {
    const self = this;
    const interval = setInterval(async () => {
      try {
        const status = await API.getBuildStatus(taskId);
        if (status.status === 'done') {
          clearInterval(interval);
          showToast('Build complete!');
          self._updateStatus();
        } else if (status.status === 'failed') {
          clearInterval(interval);
          showToast('Build failed: ' + status.error, 'error');
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 2000);
  }

  showTypeEditor() {
    const editor = new TypeEditor(this._typeSystem, () => {});
    editor.show();
  }

  redraw() {
    if (this._canvas) this._canvas.draw(true, true);
  }

  getProjectPath() {
    return this._project.getPath();
  }

  _updateStatus() {
    const statusEl = document.getElementById('status-text');
    const projEl = document.getElementById('status-project');
    if (this._project.isOpen()) {
      projEl.textContent = 'Project: ' + this._project.getConfig().name;
    }
    if (this._graphManager._graph.extra.path) {
      statusEl.textContent = 'Graph: ' + this._graphManager._graph.extra.path;
    }
  }
}

export { App };
