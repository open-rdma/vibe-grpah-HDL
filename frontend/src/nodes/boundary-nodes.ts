import type { PortData } from '../types/graph-types';
import { getPortColor, createDefaultPort } from '../constants';

const BOUNDARY_COLORS = {
  graph_input: '#2a6',
  graph_output: '#48c'
};

type SlotKey = 'inputs' | 'outputs';
type BoundaryDirection = 'input' | 'output';

// Maps from graph-level port direction to boundary node slot type
const DIR_TO_SLOT: Record<BoundaryDirection, SlotKey> = { input: 'outputs', output: 'inputs' };
const DIR_TO_BG: Record<BoundaryDirection, string> = { input: '#1a3a2a', output: '#1a2a3a' };
const DIR_TO_TITLE: Record<BoundaryDirection, string> = { input: '<- graph_input', output: 'graph_output ->' };

function syncBoundaryPorts(this: LGraphNode, graph: LGraph, direction: BoundaryDirection): void {
  const ports: PortData[] = (graph.extra && graph.extra.ports) || [];
  const slotsKey = DIR_TO_SLOT[direction];

  this[slotsKey].length = 0;
  for (let i = 0; i < ports.length; i++) {
    const p = ports[i];
    if (p.direction === direction) {
      if (direction === 'input') {
        this.addOutput(p.name, p.type || p.category || 'data');
      } else {
        this.addInput(p.name, p.type || p.category || 'data');
      }
      const idx = this[slotsKey].length - 1;
      this[slotsKey][idx].color_on = this.getPortColor!(p.category);
      this[slotsKey][idx]._port_data = p;
    }
  }
  const numPorts = Math.max(this[slotsKey].length, 1);
  this.size[1] = Math.max(30, numPorts * 24 + 8);
}

function addPortMenuOptions(this: LGraphNode, _canvas: LGraphCanvas, _options: any[], direction: BoundaryDirection): any[] {
  const label = direction === 'input' ? 'Input' : 'Output';
  const self = this;
  return [{
    content: `Add ${label} Port`,
    callback: () => {
      const name = prompt('Port name:');
      if (!name || !name.trim()) return;
      const graph = self.graph;
      if (!graph || !graph.extra) return;
      if (!graph.extra.ports) graph.extra.ports = [];
      const port = createDefaultPort(direction);
      port.name = name.trim();
      graph.extra.ports.push(port);
      const app = window.__app;
      if (app) {
        app._graphManager.syncBoundaryNodes();
        app.redraw();
        app._propertyPanel.clear();
      }
    }
  }];
}

function createBoundaryNode(this: LGraphNode, direction: BoundaryDirection): void {
  this._is_boundary = true;
  this.inputs = [];
  this.outputs = [];
  this.color = BOUNDARY_COLORS[direction === 'input' ? 'graph_input' : 'graph_output'];
  this.bgcolor = DIR_TO_BG[direction];
  this.boxcolor = this.color;
  this.shape = LiteGraph.BOX_SHAPE;
  this.size = [120, 30];
  this.properties = {};
}

// ---------- typed prototype boundary ----------
// Same pattern as rtl-module.ts: cast once to LGraphNode, then all method
// assignments are type-checked against the declarations in litegraph.d.ts.

/**
 * GraphInputNode — has OUTPUT slots for each input-direction graph port,
 * because internal wiring connects FROM graph_input TO internal module inputs.
 */
function GraphInputNode(this: LGraphNode) { createBoundaryNode.call(this, 'input'); }
GraphInputNode.title = DIR_TO_TITLE.input;
GraphInputNode.desc = 'Graph input boundary node (auto-managed)';
const giProto = GraphInputNode.prototype as LGraphNode;
giProto.syncWithGraphPorts = function(graph: LGraph): void { syncBoundaryPorts.call(this, graph, 'input'); };
giProto.getPortColor = getPortColor;
giProto.getExtraMenuOptions = function(canvas: LGraphCanvas, options: any[]): any[] { return addPortMenuOptions.call(this, canvas, options, 'input'); };

/**
 * GraphOutputNode — has INPUT slots for each output-direction graph port,
 * because internal wiring connects FROM internal module outputs TO graph_output.
 */
function GraphOutputNode(this: LGraphNode) { createBoundaryNode.call(this, 'output'); }
GraphOutputNode.title = DIR_TO_TITLE.output;
GraphOutputNode.desc = 'Graph output boundary node (auto-managed)';
const goProto = GraphOutputNode.prototype as LGraphNode;
goProto.syncWithGraphPorts = function(graph: LGraph): void { syncBoundaryPorts.call(this, graph, 'output'); };
goProto.getPortColor = getPortColor;
goProto.getExtraMenuOptions = function(canvas: LGraphCanvas, options: any[]): any[] { return addPortMenuOptions.call(this, canvas, options, 'output'); };

LiteGraph.registerNodeType('rtl/graph_input', GraphInputNode);
LiteGraph.registerNodeType('rtl/graph_output', GraphOutputNode);
