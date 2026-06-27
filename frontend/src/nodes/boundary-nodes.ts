import type { PortData } from '../types/graph-types';
import { getPortColor, createDefaultPort } from '../constants';

const BOUNDARY_COLORS = {
  graph_input: '#2a6',
  graph_output: '#48c'
};

type SlotKey = 'inputs' | 'outputs';
type AddPortMethod = 'addInput' | 'addOutput';

// Maps from graph-level port direction to boundary node slot type
const DIR_TO_SLOT: Record<'input' | 'output', SlotKey> = { input: 'outputs', output: 'inputs' };
const DIR_TO_ADD: Record<'input' | 'output', AddPortMethod> = { input: 'addOutput', output: 'addInput' };
const DIR_TO_BG: Record<'input' | 'output', string> = { input: '#1a3a2a', output: '#1a2a3a' };
const DIR_TO_TITLE: Record<'input' | 'output', string> = { input: '<- graph_input', output: 'graph_output ->' };

function syncBoundaryPorts(this: LGraphNode, graph: LGraph, direction: 'input' | 'output'): void {
  const ports: PortData[] = (graph.extra && graph.extra.ports) || [];
  const slotsKey = DIR_TO_SLOT[direction];
  const addMethod = DIR_TO_ADD[direction];

  this[slotsKey].length = 0;
  for (let i = 0; i < ports.length; i++) {
    const p = ports[i];
    if (p.direction === direction) {
      (this as any)[addMethod](p.name, p.type || p.category || 'data');
      const idx = this[slotsKey].length - 1;
      this[slotsKey][idx].color_on = this.getPortColor(p.category);
      this[slotsKey][idx]._port_data = p;
    }
  }
  const numPorts = Math.max(this[slotsKey].length, 1);
  this.size[1] = Math.max(30, numPorts * 24 + 8);
}

function addPortMenuOptions(this: LGraphNode, _canvas: LGraphCanvas, _options: any[], direction: 'input' | 'output'): any[] {
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
      const app = (window as any).__app;
      if (app) {
        app._graphManager.syncBoundaryNodes();
        app.redraw();
        app._propertyPanel.clear();
      }
    }
  }];
}

function createBoundaryNode(this: LGraphNode, direction: 'input' | 'output'): void {
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

/**
 * GraphInputNode — has OUTPUT slots for each input-direction graph port,
 * because internal wiring connects FROM graph_input TO internal module inputs.
 */
function GraphInputNode(this: LGraphNode) { createBoundaryNode.call(this, 'input'); }
GraphInputNode.title = DIR_TO_TITLE.input;
GraphInputNode.desc = 'Graph input boundary node (auto-managed)';
(GraphInputNode as any).prototype.syncWithGraphPorts = function(graph: LGraph): void { syncBoundaryPorts.call(this, graph, 'input'); };
(GraphInputNode as any).prototype.getPortColor = getPortColor;
(GraphInputNode as any).prototype.getExtraMenuOptions = function(canvas: LGraphCanvas, options: any[]): any[] { return addPortMenuOptions.call(this, canvas, options, 'input'); };

/**
 * GraphOutputNode — has INPUT slots for each output-direction graph port,
 * because internal wiring connects FROM internal module outputs TO graph_output.
 */
function GraphOutputNode(this: LGraphNode) { createBoundaryNode.call(this, 'output'); }
GraphOutputNode.title = DIR_TO_TITLE.output;
GraphOutputNode.desc = 'Graph output boundary node (auto-managed)';
(GraphOutputNode as any).prototype.syncWithGraphPorts = function(graph: LGraph): void { syncBoundaryPorts.call(this, graph, 'output'); };
(GraphOutputNode as any).prototype.getPortColor = getPortColor;
(GraphOutputNode as any).prototype.getExtraMenuOptions = function(canvas: LGraphCanvas, options: any[]): any[] { return addPortMenuOptions.call(this, canvas, options, 'output'); };

LiteGraph.registerNodeType('rtl/graph_input', GraphInputNode);
LiteGraph.registerNodeType('rtl/graph_output', GraphOutputNode);
