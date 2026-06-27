// Minimal type declarations for litegraph.js (loaded globally via <script> tag)

/// <reference path="./graph-types.ts" />

declare class LiteGraph {
  static SPLINE_LINK: number;
  static BOX_SHAPE: number;
  static LGraph: typeof LGraph;
  static LGraphCanvas: typeof LGraphCanvas;
  static createNode(type: string): LGraphNode;
  static registerNodeType(type: string, classObj: any): void;
}

declare class LGraph {
  _nodes: LGraphNode[];
  links: Record<string, LLink>;
  extra: Record<string, any>;
  onAfterChange: (() => void) | null;
  add(node: LGraphNode): void;
  remove(node: LGraphNode): void;
  clear(): void;
}

declare class LGraphCanvas {
  constructor(canvas: HTMLCanvasElement, graph: LGraph);
  graph: LGraph;
  canvas: HTMLCanvasElement;
  background_image: string;
  render_links_border: boolean;
  links_render_mode: number;
  selected_nodes: Record<string, LGraphNode>;
  ds: { offset: [number, number]; scale: number };
  onNodeSelected: ((node: LGraphNode) => void) | null;
  onNodeDeselected: (() => void) | null;
  draw(foreground: boolean, background: boolean): void;
  deselectAllNodes(): void;
  zoom(factor: number, center: [number, number]): void;
  zoomToFit(): void;
  selectNode(node: LGraphNode): void;
  openSubgraph(graph: LGraph): void;
}

interface LLink {
  origin_id: number;
  origin_slot: number;
}

interface LGraphNodePort {
  name: string;
  type?: string;
  color_on?: string;
  link?: number;
  _port_data?: PortData;
}

declare class LGraphNode {
  id: number;
  type: string;
  title: string;
  pos: [number, number];
  size: [number, number];
  flags: Record<string, any>;
  properties: Record<string, string>;
  inputs: LGraphNodePort[];
  outputs: LGraphNodePort[];
  graph: LGraph | null;
  color?: string;
  bgcolor?: string;
  boxcolor?: string;
  shape?: number;

  _is_boundary?: boolean;
  _module_ref?: string;
  _module_data?: Record<string, any>;
  _subgraph_data?: GraphData;
  _subgraph?: LGraph;

  addInput(name: string, type: string): void;
  addOutput(name: string, type: string): void;
  connect(slot: number, targetNode: LGraphNode, targetSlot: number): void;
  getPortColor(category: string): string;
  setPortsFromData(moduleData: GraphData): void;
}
