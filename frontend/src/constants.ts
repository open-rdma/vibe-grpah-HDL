import type { PortData } from './types/graph-types';

export const PORT_COLORS: Record<string, string> = {
  clock: '#0af',
  reset: '#f80',
  data: '#aaa'
};

export function getPortColor(category: string): string {
  return PORT_COLORS[category] || PORT_COLORS.data;
}

/** Maximum subgraph drill-down depth, configurable via VITE_SUBGRAPH_MAX_DEPTH env var. Default: 64 */
export const SUBGRAPH_MAX_DEPTH: number =
  (typeof import.meta !== 'undefined' && (import.meta as any).env?.VITE_SUBGRAPH_MAX_DEPTH)
    ? parseInt(String((import.meta as any).env.VITE_SUBGRAPH_MAX_DEPTH), 10)
    : 64;

export function createDefaultPort(direction: 'input' | 'output' = 'input'): PortData {
  return {
    name: 'new_port',
    direction,
    category: 'data',
    type: '',
    clock_domain: '',
    reset_domain: '',
    reset_type: 'async'
  };
}
