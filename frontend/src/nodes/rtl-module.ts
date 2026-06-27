import type { PortData, GraphData } from '../types/graph-types';
import { getPortColor } from '../constants';
import { showToast } from '../ui/toast';

/**
 * RTL Module Node — represents a module instance on the canvas.
 * Subclassed via litegraph.js prototype copying system.
 */
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

(RTLModuleNode as any).prototype.getPortColor = getPortColor;

function validateConnection(
  sourceNode: LGraphNode, sourceSlot: number,
  targetNode: LGraphNode, targetSlot: number
): boolean {
  const validator = (window as any).__connectionValidator;
  if (!validator) return true;
  const result = validator.validate(sourceNode, sourceSlot, targetNode, targetSlot);
  if (!result.allowed) {
    showToast('Connection blocked: ' + result.reason, 'error');
    return false;
  }
  return true;
}

(RTLModuleNode as any).prototype.onConnectInput = function(
  target_slot: number, _type: string, _output_slot: object, output_node: LGraphNode, output_slot: number
): boolean {
  return validateConnection(output_node, output_slot, this, target_slot);
};

(RTLModuleNode as any).prototype.onConnectOutput = function(
  output_slot: number, _type: string, _input_slot: object, input_node: LGraphNode, input_slot: number
): boolean {
  return validateConnection(this, output_slot, input_node, input_slot);
};

(RTLModuleNode as any).prototype.onDblClick = function(
  e: MouseEvent, pos: number[], graphcanvas: LGraphCanvas
): boolean {
  if (this._subgraph) {
    graphcanvas.openSubgraph(this._subgraph);
    return true;
  }
  return false;
};

(RTLModuleNode as any).prototype.getExtraMenuOptions = function(canvas: LGraphCanvas, options: any[]): any[] {
  const self = this;
  const menuOptions: any[] = [
    {
      content: 'Edit Properties',
      callback: () => {
        const app = (window as any).__app;
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
        } else if (self._module_ref) {
          const app = (window as any).__app;
          if (app) {
            app.openGraph(self._module_ref);
          }
        }
      }
    });
  }
  return menuOptions;
};

(RTLModuleNode as any).prototype.setPortsFromData = function(moduleData: GraphData): void {
  this.inputs.length = 0;
  this.outputs.length = 0;

  const ports = moduleData.ports || [];
  for (let i = 0; i < ports.length; i++) {
    const p: PortData = ports[i];
    const color = this.getPortColor(p.category);
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
