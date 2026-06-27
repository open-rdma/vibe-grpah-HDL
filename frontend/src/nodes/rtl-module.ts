import type { PortData, GraphData } from '../types/graph-types';
import { getPortColor, SUBGRAPH_MAX_DEPTH } from '../constants';
import { showToast } from '../ui/toast';

// ---------- typed prototype boundary ----------
// litegraph.js registerNodeType copies from classObj.prototype, so the
// prototype is the single source of truth for method assignments.  We cast
// it ONCE to LGraphNode; every method assignment after that point is fully
// type-checked (parameter names, types, and return values) against the
// declared signatures in litegraph.d.ts.

function RTLModuleNode(this: LGraphNode) {
  this.inputs = [];
  this.outputs = [];
  this.properties = {};
  this._is_boundary = false;
  this._module_ref = undefined;
  this._module_data = undefined;
}

RTLModuleNode.title = 'RTL Module';
RTLModuleNode.desc = 'An RTL module instance';

const proto = RTLModuleNode.prototype as LGraphNode;

proto.getPortColor = getPortColor;

function validateConnection(
  sourceNode: LGraphNode, sourceSlot: number,
  targetNode: LGraphNode, targetSlot: number
): boolean {
  const validator = window.__connectionValidator;
  if (!validator) return true;
  const result = validator.validate(sourceNode, sourceSlot, targetNode, targetSlot);
  if (!result.allowed) {
    showToast('Connection blocked: ' + result.reason, 'error');
    return false;
  }
  return true;
}

proto.onConnectInput = function(
  target_slot: number, _type: string, _output_slot: object, output_node: LGraphNode, output_slot: number
): boolean {
  return validateConnection(output_node, output_slot, this, target_slot);
};

proto.onConnectOutput = function(
  output_slot: number, _type: string, _input_slot: object, input_node: LGraphNode, input_slot: number
): boolean {
  return validateConnection(this, output_slot, input_node, input_slot);
};

proto.onDblClick = function(
  _e: MouseEvent, _pos: number[], graphcanvas: LGraphCanvas
): boolean {
  // Already built and cached — open immediately
  if (this._subgraph) {
    graphcanvas.openSubgraph(this._subgraph);
    return true;
  }

  const refPath: string = this._module_ref || '';

  // Can't open only if there's no ref to load from AND no preloaded data
  if (!refPath && !this._subgraph_data) {
    showToast('Cannot open: module data not loaded', 'error');
    return false;
  }

  // Recursion depth guard
  if (graphcanvas._graph_stack && graphcanvas._graph_stack.length >= SUBGRAPH_MAX_DEPTH) {
    showToast(`Cannot drill deeper: max depth ${SUBGRAPH_MAX_DEPTH} reached`, 'error');
    return false;
  }

  const app = window.__app;
  if (!app || !app._graphManager) {
    showToast('Cannot open: app not available', 'error');
    return false;
  }

  // Always refresh _subgraph_data from cache/API (or load for the first time),
  // then build subgraph.  This handles the race where _instantiateFromRef
  // hasn't finished loading yet, and the stale-cache case where the
  // referenced graph was edited in another subgraph session.
  console.log('[onDblClick] refPath=' + refPath + ' hasData=' + !!this._subgraph_data);
  app._graphManager._loadRefPorts(this, refPath)
    .then(() => {
      if (!this._subgraph_data) {
        throw new Error('module data not loaded');
      }
      console.log('[onDblClick] _subgraph_data loaded, nodes=' +
        (this._subgraph_data.nodes || []).length);
      return app._graphManager.buildSubgraphFromData(this._subgraph_data, refPath);
    })
    .then((subgraph: LGraph) => {
      subgraph._subgraph_node = this;
      this._subgraph = subgraph;
      graphcanvas.openSubgraph(subgraph);
    })
    .catch((e: Error) => {
      console.error('[onDblClick] failed:', e.message);
      showToast('Failed to build subgraph: ' + e.message, 'error');
    });

  return true;
};

proto.getExtraMenuOptions = function(canvas: LGraphCanvas, _options: any[]): any[] {
  const self = this;
  const menuOptions: any[] = [
    {
      content: 'Edit Properties',
      callback: () => {
        const app = window.__app;
        if (app) {
          canvas.selectNode(self);
          app._propertyPanel.showNodeProperties(self);
        }
      }
    },
    {
      content: 'Delete',
      callback: () => {
        if (self.graph) {
          self.graph.remove(self);
          canvas.draw(true, true);
        }
      }
    }
  ];
  if (self._module_ref || self._subgraph_data || self._subgraph) {
    menuOptions.push({
      content: 'Open Subgraph',
      callback: () => {
        if (self._subgraph) {
          canvas.openSubgraph(self._subgraph);
          return;
        }
        const refPath: string = self._module_ref || '';
        // Can't open only if there's no ref to load from AND no preloaded data
        if (!refPath && !self._subgraph_data) {
          showToast('Cannot open: module data not loaded', 'error');
          return;
        }
        // Recursion depth guard
        if (canvas._graph_stack && canvas._graph_stack.length >= SUBGRAPH_MAX_DEPTH) {
          showToast(`Cannot drill deeper: max depth ${SUBGRAPH_MAX_DEPTH} reached`, 'error');
          return;
        }
        const app = window.__app;
        if (!app || !app._graphManager) {
          showToast('Cannot open: app not available', 'error');
          return;
        }
        console.log('[ctx OpenSubgraph] refPath=' + refPath + ' hasData=' + !!self._subgraph_data);
        app._graphManager._loadRefPorts(self, refPath)
          .then(() => {
            if (!self._subgraph_data) {
              throw new Error('module data not loaded');
            }
            console.log('[ctx OpenSubgraph] _subgraph_data loaded, nodes=' +
              (self._subgraph_data.nodes || []).length);
            return app._graphManager.buildSubgraphFromData(self._subgraph_data, refPath);
          })
          .then((subgraph: LGraph) => {
            subgraph._subgraph_node = self;
            self._subgraph = subgraph;
            canvas.openSubgraph(subgraph);
          })
          .catch((e: Error) => {
            console.error('[ctx OpenSubgraph] failed:', e.message);
            showToast('Failed to build subgraph: ' + e.message, 'error');
          });
      }
    });
  }
  return menuOptions;
};

proto.setPortsFromData = function(moduleData: GraphData): void {
  this.inputs.length = 0;
  this.outputs.length = 0;

  const ports = moduleData.ports || [];
  for (let i = 0; i < ports.length; i++) {
    const p: PortData = ports[i];
    const color = this.getPortColor!(p.category);
    if (p.direction === 'input') {
      this.addInput(p.name, p.type || p.category || 'data');
      const idx = this.inputs.length - 1;
      this.inputs[idx].color_on = color;
      this.inputs[idx]._port_data = p;
    } else {
      this.addOutput(p.name, p.type || p.category || 'data');
      const idx = this.outputs.length - 1;
      this.outputs[idx].color_on = color;
      this.outputs[idx]._port_data = p;
    }
  }
};

LiteGraph.registerNodeType('rtl/module', RTLModuleNode);
