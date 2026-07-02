# Compiler Research Task Specification

## Goal
Design and iterate on a YAML-based knowledge representation format and a compiler that converts YAML→BSV, validated against the blue-rdma test suite.

## Milestones
1. **M1**: Achieve ZFPR > 0 for at least T01-T04 (basic type/function modules) — YAML format can express BSV types correctly
2. **M2**: Achieve ZFPR > 0 for T01-T11 (through medium complexity) — compiler handles submodules and state machines
3. **M3**: Achieve ZFPR > 0 for T01-T20 (full test suite) — end-to-end validation
4. **M4**: Achieve ZFPR >= 0.5 across all 20 modules — mature compiler
5. **M5**: Achieve ZFPR >= 0.8 with AL >= 0.7 — optimized format

## Success Criteria
- Core metric: ZFPR (Zero-Fix Pass Rate) — modules passing all testbenches without manual BSV edits
- Secondary: AL (Abstraction Level) — ratio of L0+L1 descriptions to total
- Tertiary: ID (Information Density) — YAML bytes / BSV bytes, lower is better

## Constraints
- BSC compiler: /data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04
- Simulation timeout: 180 seconds max
- Cannot modify generated BSV directly — only modify YAML and regenerate
- Each iteration in its own directory
- All 20 test cases attempted per iteration (batch parallel)
- Claude Code CLI: `ccb -p --permission-mode auto`
- Zero user interaction
