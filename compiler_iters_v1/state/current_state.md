# Deli_AutoResearch State - Compiler Research

## Session: 2026-07-02 (prompt_v2 branch)

## Completed Iterations

| Iter | Strategy | FPC | Key Finding |
|------|----------|-----|-------------|
| 001 | Auto-parse BSV→YAML→mechanical BSV | 0.045 | Auto-parser unreliable, loses syntax |
| 002 | LLM agent (ccb) + declarative YAML | 0.333* | LLM works for simple modules, large prompts timeout |
| 003 | Split-prompt (types+funcs) + 4 parallel | 0.182 | 15/22 gen OK, 4/22 compile |
| 004 | Reference BSV + 2-round error fix loop | 0.375** | Fix loop works (2 modules), 3/8 compile |

*iter_002: 1/3 modules tested (Settings only)
**iter_004: 8 foundational modules tested

## Modules with FPC=1.0 (compiled successfully)
- Settings: All iterations (typedef_only, simplest module)
- WorkCompGen: iter_004 (with error-fix loop)
- Arbitration: iter_004 (with error-fix loop)

## Tried Directions (do NOT repeat)
1. Direct mechanical YAML→BSV conversion (iter_001) - FAILED
2. Single large prompt with full L0 knowledge (iter_002) - TIMEOUT
3. Parallel-only generation without fixes (iter_003) - INCOMPLETE CODE
4. Reference BSV injection into YAML (iter_004) - WORKS but slow

## Promising Directions (try next)
1. Template-based generation: Create BSV templates with fill-in slots
2. Two-agent approach: Generator + Blind Reviewer (per prompt_v2_compiler_flow.md)
3. Incremental compilation: Start with stubs, add features one at a time
4. Testbench-first: Generate testbench from test_method, then module
5. Type-inference from original BSV: Extract type signatures, let LLM fill behavior
6. Smaller YAML: Remove reference BSV, use only declarative descriptions
7. L0-L1 abstraction: Pure declarative with minimal hints (per optimization.md)

## Current Bottlenecks
1. Prompt size >8KB causes ccb timeout
2. Generated code is syntactically correct but incomplete (stubs)
3. Complex modules (Headers, DataTypes) need better knowledge representation
4. Error-fix loop is effective but slow (5+ minutes per module with 2 rounds)

## Metrics Trend
- FPC: 0.045 → 0.333 → 0.182 → 0.375 (improving on foundational)
- GEN rate: 1.0 → 0.333 → 0.682 → 0.750 (improving)
- ZFPR: 0.0 (no testbench testing yet - prerequisite is FPC)
