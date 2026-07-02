# Compiler Auto Research Task Spec

## Goal
Find the optimal YAML input format and compiler internal workflow for converting "nested multi-level graph + natural language" YAML files into RTL code (BSV). The system must achieve ZFPR=1.0 across all 20 test modules.

## Success Criteria
1. ZFPR (Zero-Fix Pass Rate) = 1.0: all test modules pass testbench without manual BSV edits
2. AL (Abstraction Level) >= 0.7: YAML descriptions are sufficiently declarative
3. ID (Information Density) < 1.0: YAML is more compact than original BSV
4. DCC (Dependency Chain Coverage) = 1.0: continuous ZFPR chain from leaves to root

## Milestones
- Phase 1: T01-T02 (type system expression)
- Phase 2: T03-T04 (simple logic modules)
- Phase 3: T05-T06 (arbitration/work completion)
- Phase 4: T07-T09 (pipeline/packet processing)
- Phase 5: T10-T11 (send queue management)
- Phase 6: T12-T14 (QP core logic)
- Phase 7: T15-T17 (payload/complex datapath)
- Phase 8: T18 (multi-level nested graph)
- Phase 9: T19-T20 (full system integration)

## Environment
- BSC compiler: /data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc
- Source code: /data/mmh/vibe-grpah-HDL/blue-rdma/src/
- Test code: /data/mmh/vibe-grpah-HDL/blue-rdma/test/
- Output directory: /data/mmh/vibe-grpah-HDL/compiler_iters_v1/

## Key Constraints
- Cannot directly modify generated BSV; only modify YAML and regenerate
- Each iteration in a new directory
- Max simulation timeout: 3 minutes
- Zero interaction during run
- Clean build artifacts after iteration, keep BSV source, git commit
- BSC path must be in PATH for compilation
