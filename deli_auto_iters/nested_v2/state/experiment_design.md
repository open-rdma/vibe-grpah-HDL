# nested_v2 Experiment Design

## Overview

nested_v2 tests 7 key improvements to the multi-level knowledge merge approach, motivated by 13 problems discovered in nested_v1.

## Test Hierarchy (4 levels)

```
Level 3: mkPipelinedArbiter       (top/pipelined_arbiter.yaml)
         ├── instantiates mkArbiterTree
         ├── adds pipeline register + valid flag
         └── NEW module, tests deep proviso propagation

Level 2: mkArbiterTree            (library/arbiter_tree/arbiter_tree.yaml)
         ├── instantiates 3× mkRoundRobinArbiter
         ├── two parameterizations: TDiv#(reqNum,2) and 2
         └── tests multi-param child grouping

Level 1: mkRoundRobinArbiter      (library/round_robin_arbiter/round_robin_arbiter.yaml)
         ├── instantiates mkPriorityEncoder
         ├── sequential (has state: Reg#(Bit#(reqNum)))
         └── tests child interface filtering

Level 0: mkPriorityEncoder        (library/priority_encoder/priority_encoder.yaml)
         ├── leaf module, no children
         ├── pure combinational
         └── tests import guidance (should need ZERO imports)
```

## What We're Testing

### Fix 1: Language Template Separation (P4)
Added `templates/bluespec_sv/template.md` with BSV-generic syntax. system_knowledge.md now contains ONLY project-specific info. Tests whether agents can use shared language knowledge.

### Fix 2: Child Knowledge Filtering (P3)
Parents receive ONLY child's:
- External ports (category: data, not internal)
- Method signatures
- Provisos (with parameter substitution)
- Instantiation template

Parents do NOT receive child's behavioral knowledge or internal signals.

### Fix 3: Proviso Closure Computation (P8)
Merge script computes complete transitive proviso closure:
- Module's own provisos
- Each child's provisos with type parameters substituted
- Deduplicated combined list

### Fix 4: Signal Declarations (P2)
Internal signals are explicitly declared in `signals` section with types.
No more `self.signalName` ambiguity in connections.

### Fix 5: Connection Computation Descriptions (P11)
Connections now include `transform` fields describing HOW data flows between signals.
E.g., `transform: "truncate(reqVec)"` → `Bit#(TDiv#(reqNum, 2))`

### Fix 6: Parameter Grouping (P1)
Children with same ref but different parameterizations are shown separately.
E.g., ArbiterTree shows RoundRobinArbiter#(TDiv#(reqNum, 2)) and RoundRobinArbiter#(2) as separate groups.

### Fix 7: Import Guidance (P9)
LAYER 7 provides decision table + analysis of what imports THIS module needs.
Agents are told "Import ONLY what you use" instead of "always import everything".

## Success Criteria

1. All 4 modules compile in dependency order (leaf → mid → mid-upper → top)
2. PriorityEncoder imports ZERO unnecessary packages
3. RoundRobinArbiter has correct priority rotation direction (i → i+1)
4. ArbiterTree has complete provisos (no missing proviso errors like nested_v1)
5. PipelinedArbiter correctly propagates provisos through 3 levels

## Comparison with nested_v1

| Metric | nested_v1 | nested_v2 |
|--------|-----------|-----------|
| Levels | 3 | 4 |
| Language template | Embedded in system_knowledge.md | Shared templates/bluespec_sv/ |
| Child knowledge | FULL (implementation + interface) | Interface contract only |
| Provisos | Not propagated | Complete transitive closure |
| Signals | Inferred from connections (self.X) | Explicitly declared |
| Connections | Flat from→to | With transform descriptions |
| Import guidance | "Always available" list | Decision table + per-module analysis |
| Port types | Generic (Bit_N) | Parameterized (Bit#(reqNum)) |
