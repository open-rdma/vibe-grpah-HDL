import type { PortData, GraphData } from '../types/graph-types';
import { getPortColor } from '../constants';
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
