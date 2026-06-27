// Type declarations for litegraph.js (loaded globally via <script> tag)

/// <reference path="./graph-types.ts" />

declare class LiteGraph {
  static SPLINE_LINK: number;
  static BOX_SHAPE: number;
  static LGraph: typeof LGraph;
  static LGraphCanvas: typeof LGraphCanvas;
  static createNode(type: string): LGraphNode;
  static registerNodeType(type: string, classObj: { prototype: Partial<LGraphNode> }): void;
  static isValidConnection(typeA: string, typeB: string): boolean;
}

declare class LGraph {
  _nodes: LGraphNode[];
  links: Record<string, LLink>;
  extra: Record<string, any>;
  _subgraph_node?: LGraphNode;
  _is_subgraph?: boolean;
  onAfterChange: (() => void) | null;
  add(node: LGraphNode): void;
  remove(node: LGraphNode): void;
  clear(): void;
  beforeChange(): void;
  connectionChange(node: LGraphNode, linkInfo: unknown): void;
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
  closeSubgraph(): void;
  setDirtyCanvas(fg: boolean, bg: boolean): void;
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
  links?: number[];
  _port_data?: import('./graph-types').PortData;
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
  _subgraph_data?: import('./graph-types').GraphData;
  _subgraph?: LGraph;

  addInput(name: string, type: string): void;
  addOutput(name: string, type: string): void;
  connect(slot: number, targetNode: LGraphNode, targetSlot: number): void;
  disconnectInput(slot: number, opts?: { doProcessChange: boolean }): void;

  // litegraph lifecycle callbacks — exact signatures from src/litegraph.js
  /**
   * Called when an input connection is attempted on this node.
   * @returns false to block the connection.
   * @param targetSlot  - input slot index on this node
   * @param type        - output slot type string
   * @param output      - output slot *object* on the source node
   * @param outputNode  - source node
   * @param outputSlot  - output slot index on the source node
   */
  onConnectInput?(targetSlot: number, type: string, output: LGraphNodePort, outputNode: LGraphNode, outputSlot: number): boolean;

  /**
   * Called when an output connection is attempted from this node.
   * @returns false to block the connection.
   * @param outputSlot  - output slot index on this node
   * @param type        - input slot type string
   * @param input       - input slot *object* on the target node
   * @param inputNode   - target node
   * @param inputSlot   - input slot index on the target node
   */
  onConnectOutput?(outputSlot: number, type: string, input: LGraphNodePort, inputNode: LGraphNode, inputSlot: number): boolean;

  onDblClick?(e: MouseEvent, pos: number[], graphcanvas: LGraphCanvas): boolean;
  getExtraMenuOptions?(canvas: LGraphCanvas, options: any[]): any[];
  getPortColor?(category: string): string;
  setPortsFromData?(moduleData: import('./graph-types').GraphData): void;
  syncWithGraphPorts?(graph: LGraph): void;
}
