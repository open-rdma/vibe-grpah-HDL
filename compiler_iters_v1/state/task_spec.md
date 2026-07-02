# Compiler Research Task Spec

## Goal
Design a YAML file format and compiler that can convert "nested multi-level graph structure + natural language description" YAML files into correct RTL (BSV) code.

## Success Criteria
- ZFPR (Zero-Fix Pass Rate) = 1.0 across all 20 test modules
- AL (Abstraction Level) >= 0.7
- The YAML format is language-agnostic (LIS = 0)

## Milestones
1. iter_001-003: Establish baseline compiler, test with T01-T03 (simple types/functions)
2. iter_004-006: Scale to T04-T09 (simple modules, FSMs)
3. iter_007-009: Scale to T10-T14 (multi-submodule collaboration)
4. iter_010-012: Scale to T15-T18 (complex data paths, nested graphs)
5. iter_013+: Full integration (T19-T20)

## Key Constraints
- Cannot directly modify generated BSV code
- BSC compiler: /data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc
- Simulation timeout: 3 minutes max
- Each iteration is independent, creates new directory
- Clean up BSC build artifacts after testing
