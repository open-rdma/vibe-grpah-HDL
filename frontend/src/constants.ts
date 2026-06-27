import type { PortData } from './types/graph-types';

export const PORT_COLORS: Record<string, string> = {
  clock: '#0af',
  reset: '#f80',
  data: '#aaa'
};

export function getPortColor(category: string): string {
  return PORT_COLORS[category] || PORT_COLORS.data;
}

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
