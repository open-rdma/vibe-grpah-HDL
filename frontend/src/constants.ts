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

export const SYSTEM_KNOWLEDGE: Record<string, string> = {
  verilog: `# Verilog Coding Conventions
- Use non-blocking assignments (\`<=\`) in \`always_ff\` blocks.
- Prefer \`wire\` for combinational signals, \`reg\` for sequential.
- Module names should match file names.`,

  vhdl: `# VHDL Coding Conventions
- Use \`std_logic\` and \`std_logic_vector\` for synthesizable code.
- Prefer \`rising_edge(clk)\` over \`clk'event and clk='1'\`.
- Entity names should match file names.`,

  bluespec: `# Bluespec SystemVerilog Conventions
- Use \`mkReg\` and \`mkRegU\` for registers.
- Rules are atomic; use \`(* fire_when_enabled *)\` and \`(* no_implicit_conditions *)\` pragmas.
- Interfaces should be defined as BSV interfaces with methods.`
};
