// === Core data structures for RTL Blueprint ===

export interface PortData {
  name: string;
  direction: 'input' | 'output';
  category: 'clock' | 'reset' | 'data';
  type?: string;
  clock_domain?: string;
  reset_domain?: string;
  reset_type?: 'async' | 'sync';
  allow_cross_domain?: boolean;
}

export interface GraphMeta {
  name: string;
  description?: string;
  test_method?: string;
}

export interface CanvasViewport {
  offset_x: number;
  offset_y: number;
  scale: number;
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
}

export interface ConnectionTarget {
  node: string;
  port: string;
}

export interface Connection {
  from: ConnectionTarget;
  to: ConnectionTarget[];
  allow_cross_domain?: boolean;
  description?: string;
}

export interface GraphData {
  meta: GraphMeta;
  properties: Record<string, any>;
  ports: PortData[];
  nodes: GraphNodeData[];
  connections: Connection[];
  canvas?: CanvasViewport;
}

export interface BuildOptions {
  scope: string;
  mode: string;
  includeTestbench: boolean;
}

export interface TypeDefinition {
  description: string;
  category: 'builtin' | 'user';
  params?: { name: string; type: string }[];
  fields?: { name: string; type: string }[];
}

export interface ValidationResult {
  allowed: boolean;
  reason: string;
}

export interface APIResponse<T = any> {
  ok?: boolean;
  error?: string;
  data?: T;
  [key: string]: any;
}
