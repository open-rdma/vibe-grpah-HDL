# Knowledge Merge Problems & Redesign Proposals

## Experiment: nested_v1 (PriorityArbiter 3-level system)

Date: 2026-07-01
Status: COMPLETE — all 3 modules generated, 2/3 compile cleanly, 1/3 has proviso errors

---

## Generation Results Summary

### Leaf: mkPriorityEncoder
- **Path:** `generated/PriorityEncoder.bsv` (36 lines)
- **Compilation:** PASSES
- **Correctness:** Algorithm matches spec exactly (combinational priority encoder with for-loop scanning from bit 0)
- **Issue:** Imports 5 unnecessary packages (FIFOF, GetPut, Vector, PAClib, PrimUtils) — module needs NONE of them

### Mid: mkRoundRobinArbiter
- **Path:** `generated/RoundRobinArbiter.bsv` (67 lines)
- **Compilation:** PASSES
- **Correctness:** Likely has rotation direction bug — `rotatePriority` rotates to `i-1` (previous index) instead of `i+1` (next index). When granting bit 0, priority moves to bit (reqNum-1) instead of bit 1. This is a subtle logic error that would only be caught by simulation.
- **Import chain:** Correctly imports `PriorityEncoder::*`

### Top: mkArbiterTree
- **Path:** `generated/ArbiterTree.bsv` (58 lines)
- **Compilation:** FAILS — missing provisos
  - `Add#(TDiv#(reqNum, 2), TDiv#(reqNum, 2), reqNum)` — needed by bit concatenation `{rightGrant, zeroes}` and `truncate(reqVec)`
  - `Add#(1, _, TDiv#(reqNum, 2))` — needed because child `mkRoundRobinArbiter#(TDiv#(reqNum, 2))` requires `Add#(1, _, reqNum)` in its provisos
- **Import chain:** Correctly imports `RoundRobinArbiter::*`

---

## Problems Found During Design

### P1: Port Type Mismatch Between Parent and Child Connections (CRITICAL)

**Description:** When a parent module references a child module's port in `connections`, there is no explicit mapping of the child's generic type parameter to the parent's type. For example, the `arbiter_tree` instantiates `RoundRobinArbiter#(TDiv#(reqNum, 2))`, but the generic parameter mapping is stored as `properties: { reqNum: "TDiv#(reqNum, 2)" }` — a string, not a structured type binding.

**Impact:** The generation agent for the parent module has to INFER the parameter instantiation from context rather than receiving explicit type bindings. This leads to type errors.

**Evidence from nested_v1:** The ArbiterTree agent DID correctly use `RoundRobinArbiter#(TDiv#(reqNum, 2))` for the child instances, but only because the `meta.knowledge` section redundantly specified this. The `properties` field in `nodes[]` was not used by the merge script at all.

**Proposed Fix:** Add a `parameters` section to `nodes` entries:
```yaml
nodes:
  - id: "left_arb_inst"
    ref: "library/round_robin_arbiter/round_robin_arbiter.yaml"
    parameters:
      reqNum: "TDiv#(reqNum, 2)"    # explicit numeric type binding
    properties: {}
```

### P2: `self` Port Semantics Are Ambiguous (CRITICAL)

**Description:** The `connections` section uses `self.portName` to refer to internal signals/wiring that are NOT actual interface ports. For example, `self.priorityLogic`, `self.encoderGrant`, `self.reqSplitter`. The merge script treats these the same as real ports, but they represent internal logic that the parent module needs to IMPLEMENT (not expose).

**Impact:** The generation agent receives a list of "connections to self" but cannot distinguish between:
- Actual interface ports (reqVec, grantVec)
- Internal wiring signals (priorityLogic, reqSplitter)
- Child-to-self connections (encoderGrant)

**Evidence from nested_v1:** The RoundRobinArbiter's merged prompt included `priorityState | internal | Bit_N` from the child's ports, which is an internal state register — the agent generated it correctly anyway (as `Reg#(Bit#(reqNum))`), but was lucky. The ArbiterTree's merged prompt showed connections like `graph_input.reqVec → self.reqSplitter` and `self.leftReq → left_arb_inst.reqVec` — the agent had to GUESS what signals to create for `reqSplitter`, `leftReq`, `rightReq`, etc. It ended up using local variables inside the `actionvalue` block.

**Proposed Fix:** Introduce a `signals` section for internal signals:
```yaml
signals:
  - name: "priorityLogic"
    type: "Bit_N"
    description: "Internal: request vector after priority mask application"
  - name: "encoderGrant"
    type: "Bit_N"
    description: "Internal: grant result from the priority encoder submodule"
```

Then in `connections`, reference these as `signal: priorityLogic` instead of `self.priorityLogic`:
```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    to:
      - { node: "encoder_inst", port: "reqVec" }
      - { signal: "priorityLogic" }
```

### P3: Knowledge Duplication Across Levels (HIGH)

**Description:** The child module's behavioral knowledge appears in BOTH:
- The child's own merged prompt (where it belongs)
- The parent's merged prompt (duplicated, as "submodule knowledge")

For example, `mkPriorityEncoder` knowledge appears in both the PriorityEncoder generation prompt AND the RoundRobinArbiter generation prompt. Similarly, `mkRoundRobinArbiter`'s full behavioral knowledge (including its internal architecture and arbitration algorithm) appears in the ArbiterTree prompt.

**Impact:** 
- Larger prompts (243 lines for ArbiterTree vs ~100 lines if child implementation was filtered)
- Risk of stale knowledge: if parent was generated first and child's knowledge later changes, parent is out of sync
- The parent should only need the child's INTERFACE CONTRACT (methods + ports + provisos), not its internal implementation details
- Confuses the agent: the parent agent sees "Submodule X uses PriorityEncoder internally" and might think it also needs to instantiate PriorityEncoder

**Evidence from nested_v1:** The ArbiterTree merged prompt is 243 lines. The RoundRobinArbiter child knowledge section alone is ~50 lines, detailing the priority mask rotation algorithm, the encoder submodule, and the arbitration steps. None of this is needed by the parent — the parent only needs to know the `grant()` method signature.

**Proposed Fix:** In the parent's merged prompt, include only the child's INTERFACE (ports + method signatures), not its behavioral knowledge. The child's behavioral knowledge is the child's own responsibility:
```python
# In merge_knowledge.py, for child nodes:
# Include: child's ports (interface contract) — EXTERNAL ports only, not internal
# Include: child's meta.name and meta.description
# Include: child's method signatures
# Include: child's PROVISOS (for parameter propagation)
# EXCLUDE: child's meta.knowledge (implementation detail)
```

### P4: No BSV-Specific Language Template (HIGH)

**Description:** The `system_knowledge.md` is copied into each project individually. BSV coding conventions (module syntax, proviso patterns, standard library usage) should be a SHARED TEMPLATE at the language level, not duplicated per-project.

**Impact:** Every project's `system_knowledge.md` re-describes the same BSV conventions. This is fragile — if conventions change, every project must be updated. Also makes it hard to add new language targets (Verilog, Chisel, etc.).

**Evidence from nested_v1:** The system_knowledge.md contains generic BSV syntax (interface/module definition, function syntax, numeric type constraints). These are identical across all BSV projects. Only the list of "available packages" (PAClib, PrimUtils) is project-specific.

**Proposed Fix:** Introduce a language-level knowledge template at `{{language}}/template.md`:
```
deli_auto_iters/
  templates/
    bluespec_sv/
      template.md        # BSV-specific coding conventions
      types.yaml         # BSV built-in types (FIFOF, Reg, PipeOut, etc.)
```

The merge script would layer:
1. Language template: `templates/bluespec_sv/template.md`
2. Project knowledge: `project.yaml` + `system_knowledge.md` (project-specific only)
3. Module knowledge: `<module>.yaml`
4. Child interfaces (one level down): `<child>.yaml` ports + methods + provisos only

### P5: Type Definitions Are Overly Generic (MEDIUM)

**Description:** The `types.yaml` uses generic names like `Bit_N`, `PipeOut_T` which don't convey the actual type parameterization. When a generation agent sees `type: "Bit_N"` on a port, it has to guess the actual bit width from context.

**Impact:** The agent can't mechanically verify that connections are type-safe. A port described as `type: "Bit_N"` connected to another `type: "Bit_N"` might have mismatched widths at compile time.

**Evidence from nested_v1:** All ports use `type: "Bit_N"` with a description like "Width = reqNum". The agent correctly inferred `Bit#(reqNum)` from the description, but only because the descriptions were consistent. If one module's port said `Bit_N` with "Width = reqNum" and another said `Bit_N` with "Width = TDiv#(reqNum, 2)", there's no compile-time check.

**Proposed Fix:** Use parameterized type expressions:
```yaml
ports:
  - name: "reqVec"
    type: "Bit#(reqNum)"      # explicit parameter, not "Bit_N"
  - name: "grantVec"
    type: "Bit#(reqNum)"      # same parameter — connection is safe
```

Or use structured type definitions:
```yaml
types:
  ReqVector:
    base: "Bit"
    width: "reqNum"
    description: "Request vector with reqNum bits"
```

### P6: No Dependency Order Resolution (MEDIUM)

**Description:** The three modules form a dependency chain: ArbiterTree depends on RoundRobinArbiter depends on PriorityEncoder. The current approach launches all three agents in parallel, but they must be compiled in order: leaf first, then mid, then top (because mid imports leaf, top imports mid).

**Impact:** If agents run in parallel, the mid-level agent generates code importing PriorityEncoder, but PriorityEncoder.bsv might not exist yet. Compilation order is not handled. In nested_v1, all three were generated in parallel and written to the same directory — this happened to work because the compilation was done afterward, not during generation.

**Proposed Fix:** 
- Option A: Sequential generation (leaf → mid → top), compiling each before the next
- Option B: Parallel generation + ordered compilation (generate all, then compile in dependency order)
- Option C: Generate ALL modules in a single session with internal dependency tracking

Option A is safest: generate leaf, compile it, generate mid (knowing leaf's interface is fixed), compile mid against leaf's .bo file, etc.

### P7: Connection Direction Inference Is Implicit (LOW)

**Description:** The `connections` section uses `.to` targets but doesn't explicitly check that the source port's direction matches the target port's direction. An `input` port cannot drive an `input` port. The current system relies on human review.

**Impact:** Invalid connections (output → output, input → input) would only be caught at compile time or manual review.

**Proposed Fix:** The merge script should validate connections:
```python
for conn in connections:
    src_port = find_port(conn.from.node, conn.from.port)
    for target in conn.to:
        tgt_port = find_port(target.node, target.port)
        if src_port.direction == tgt_port.direction:
            warn(f"Direction mismatch: {src_port.direction} → {tgt_port.direction}")
```

---

## NEW Problems Found During nested_v1 Generation

### P8: Proviso Propagation Failure Across Hierarchy (CRITICAL)

**Description:** When a parent instantiates a child with specific type parameters, the child's provisos must be resolved with those parameters and added to the parent. The merge script does NOT compute this transitive proviso closure.

**Concrete Example:**
- `RoundRobinArbiter` has provisos:
  ```
  Add#(1, _, reqNum)
  NumAlias#(TLog#(reqNum), logReqNum)
  Add#(TLog#(reqNum), 1, TLog#(TAdd#(1, reqNum)))
  ```
- `ArbiterTree` instantiates `RoundRobinArbiter#(TDiv#(reqNum, 2))`
- Substituting `reqNum → TDiv#(reqNum, 2)` gives:
  ```
  Add#(1, _, TDiv#(reqNum, 2))         ← NEEDED, but missing
  NumAlias#(TLog#(TDiv#(reqNum, 2)), _) ← NEEDED
  Add#(TLog#(TDiv#(reqNum, 2)), 1, ...) ← NEEDED
  ```
- Additionally, the bit-splitting operations (`truncate`, `truncateLSB`, `{a, b}`) introduce:
  ```
  Add#(TDiv#(reqNum, 2), TDiv#(reqNum, 2), reqNum)  ← NEEDED, but missing
  ```
- **Result:** ArbiterTree.bsv FAILS compilation with missing proviso errors.

**Root Cause:** The merge script treats provisos as opaque text. It doesn't know that `reqNum` in the child's context maps to `TDiv#(reqNum, 2)` in the parent's context, so it can't perform the substitution.

**Proposed Fix:** The merge script must parse provisos from child modules and substitute type parameters:
```python
def compute_derived_provisos(child_provisos, param_bindings):
    """Substitute param bindings into child's provisos to get parent's required provisos."""
    derived = []
    for proviso in child_provisos:
        derived.append(substitute(proviso, param_bindings))
    return derived
```

For example, `parent_param = "reqNum"`, `child_param = "reqNum"`, binding `reqNum → TDiv#(reqNum, 2)`:
- `Add#(1, _, reqNum)` → `Add#(1, _, TDiv#(reqNum, 2))`

Additionally, the merge script should analyze the connections to detect bit-manipulation operations that introduce provisos:
- `truncate(Bit#(N))` → requires `Add#(M, _, N)` where M is the result width
- `{Bit#(A), Bit#(B)}` → requires `Add#(A, B, N)` where N is the result width
- `zeroExtend(Bit#(M))` → requires the target width to be `Add#(M, _, target)`

### P9: Unnecessary Import Pollution (MEDIUM)

**Description:** The `system_knowledge.md` prescribes a fixed set of "standing imports" that ALL generated modules include unconditionally: `FIFOF`, `GetPut`, `Vector`, `PAClib`, `PrimUtils`. The agents follow this prescription blindly.

**Concrete Example:** `PriorityEncoder.bsv` is a pure combinational circuit with no registers, no FIFOs, no vectors. It needs ZERO of the 5 imported packages. Yet the agent dutifully includes all 5.

```bsv
import FIFOF::*;       // UNUSED
import GetPut::*;      // UNUSED
import Vector::*;      // UNUSED
import PAClib::*;      // UNUSED
import PrimUtils::*;   // UNUSED
```

**Root Cause:** The system_knowledge.md says "The following packages are always available" and the generation instructions don't tell the agent to only import what it actually uses.

**Proposed Fix:** Change the template to say "Import ONLY the packages you actually use" and provide a decision table:
```
| Import | When to use |
|--------|------------|
| FIFOF::* | Module contains FIFOF#(T) instances |
| Reg (built-in) | Module contains Reg#(T) instances |
| Vector::* | Module uses Vector#(n, T) or replicateM |
| PAClib::* | Module uses PipeOut or mkFork |
| PrimUtils::* | Module uses CReg or toPipeOut |
```

### P10: Child Ports Include Internal Signals (HIGH)

**Description:** The child YAML's `ports` section mixes external interface ports with internal state registers. When the merge script outputs all of the child's ports to the parent, the parent sees internal signals as though they were connectable ports.

**Concrete Example:** RoundRobinArbiter's merged prompt in the ArbiterTree context includes:
```
priorityState | internal | Bit_N | Internal: one-hot priority mask tracking which requestor has highest priority.
```
This is a `Reg#(Bit#(reqNum))` inside the RoundRobinArbiter module — NOT something the parent can or should connect to. But because all ports are dumped flatly, the parent agent sees it alongside real ports like `reqVec` and `grantVec`.

**Proposed Fix:** 
1. Add a `category` field to ports with values: `data` (external), `internal` (state register), `clock_reset` (clock/reset)
2. The merge script filters child ports to only `category: data` when presenting them to the parent
3. Internal ports are used only for the child's own generation

### P11: Connections Don't Describe Computations (HIGH)

**Description:** The `connections` section describes WHERE data flows but not HOW it is transformed. The parent agent sees flat from→to relationships without understanding the computation needed between them.

**Concrete Example:** The ArbiterTree connections include:
```yaml
- from: { node: "graph_input", port: "reqVec" }
  to: [{ node: "self", port: "reqSplitter" }]

- from: { node: "self", port: "leftReq" }
  to: [{ node: "left_arb_inst", port: "reqVec" }]
```

This tells the agent "input goes to splitter" and "leftReq goes to left arbiter", but NOT that:
- `leftReq` is the LOWER HALF of the input: `truncate(reqVec)` → `Bit#(TDiv#(reqNum, 2))`
- `rightReq` is the UPPER HALF of the input: `truncateLSB(reqVec)` → `Bit#(TDiv#(reqNum, 2))`

The agent had to infer these transformations from the `meta.knowledge` description, not from the structured connections data.

**Proposed Fix:** Augment connections with `transform` descriptions:
```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    to: [{ signal: "leftReq" }]
    transform: "truncate(reqVec)"        # lower half
    result_type: "Bit#(TDiv#(reqNum, 2))"
    
  - from: { node: "graph_input", port: "reqVec" }
    to: [{ signal: "rightReq" }]
    transform: "truncateLSB(reqVec)"     # upper half
    result_type: "Bit#(TDiv#(reqNum, 2))"
```

### P12: Generated Code Has Subtle Logic Bug (HIGH)

**Description:** The RoundRobinArbiter generated code has a priority rotation direction bug that would only be caught by simulation or formal verification.

**Concrete Example:** The `rotatePriority` function rotates priority to `i-1` (previous index) instead of `i+1` (next index):
```bsv
function Bit#(reqNum) rotatePriority(Bit#(reqNum) grant);
    Bit#(reqNum) rotated = 0;
    for (Integer i = 0; i < valueOf(reqNum); i = i + 1) begin
        if (grant[i] == 1) begin
            Integer nextIdx = (i == 0) ? (valueOf(reqNum) - 1) : (i - 1);
            rotated[nextIdx] = 1;
        end
    end
    return rotated;
endfunction
```

With `priorityOneHot = 1` (bit 0 has highest priority), granting bit 0 sets next priority to bit (reqNum-1). But the correct round-robin behavior should set next priority to bit 1.

The correct rotation would be `i + 1`:
```bsv
Integer nextIdx = (i == valueOf(reqNum) - 1) ? 0 : (i + 1);
```

**Root Cause:** The YAML knowledge says "the next bit after the granted one becomes the new highest priority, wrapping around" but the agent's implementation moves the one-hot bit in the WRONG direction. The knowledge description was correct, but the agent misinterpreted "next bit after" as "next bit before" in the implementation.

**Impact:** This type of bug is insidious — the module compiles cleanly, passes type checking, but has incorrect runtime behavior. Standard compile-time checks cannot catch it.

### P13: Interface Method vs Port Name Mismatch (MEDIUM)

**Description:** The `connections` section references `port` names (e.g., `grantVec`) but the BSV interface exposes `method` names (e.g., `grant()`). There's no explicit mapping from port names to method names.

**Concrete Example:** The RoundRobinArbiter YAML defines port `grantVec` (output, Bit_N) and the knowledge says the method is `grant(Bit#(reqNum) reqVec) → ActionValue#(Bit#(reqNum))`. The connections wire `encoder_inst.grantVec → self.encoderGrant`, but the parent code actually calls `encoder.grant(highGroup)` — the port name `grantVec` is never used in the code. The agent has to mentally map "port grantVec = output" → "method grant returns ActionValue#(Bit#(reqNum))".

**Proposed Fix:** Add explicit method declarations to the YAML:
```yaml
methods:
  - name: "grant"
    arguments:
      - name: "reqVec"
        type: "Bit#(reqNum)"
    returns: "ActionValue#(Bit#(reqNum))"
    maps_to_port: "grantVec"   # explicit: method grant() produces output port grantVec
```

---

## Additional Observations

### What Worked Correctly
1. **Correct package naming and import chains**: All three modules use the correct `import X::*` statements for their dependencies.
2. **Interface/Module structure**: All three follow correct BSV syntax for interface and module definitions.
3. **Child instantiation**: All three correctly instantiate their child submodules (e.g., `PriorityEncoder#(reqNum) encoder <- mkPriorityEncoder`).
4. **Numeric type parameterization**: The agents correctly used `reqNum` as a numeric type and parameterized child instances correctly.
5. **Knowledge hierarchy was used**: The agents read the merged knowledge and followed the algorithm descriptions.

### What Partially Worked
1. **Provisos**: The leaf and mid modules have correct provisos that compile. The top module has the right IDEA but misses derived provisos — the provisos it has are `NumAlias#(TLog#(reqNum), ...)` which show understanding, but the transitive closure is incomplete.
2. **Bit manipulation**: truncate, truncateLSB, and zeroExtend were used correctly. The agent knows these BSV primitives.

---

## Proposed Merge Algorithm Redesign

### Current Algorithm (nested_v1)
```
merge(module):
  1. Include project system_knowledge.md (FULL)
  2. Include types.yaml
  3. Include module's own meta.knowledge + ports
  4. For each child node:
     a. Include child's meta.knowledge (FULL)    ← PROBLEM: includes implementation
     b. Include child's ports (ALL, including internal)
  5. Include wiring connections (flat from→to)
  6. Include generation instructions (generic boilerplate)
```

### Proposed Algorithm (nested_v2)
```
merge(module, mode="generate"):
  LAYER 0 — LANGUAGE TEMPLATE (shared, not per-project)
    0a. templates/bluespec_sv/template.md    # BSV syntax, patterns
    0b. templates/bluespec_sv/types.yaml     # Built-in types with decision table
  
  LAYER 1 — PROJECT KNOWLEDGE
    1a. project.yaml → description, target language
    1b. system_knowledge.md (PROJECT-SPECIFIC only, not language-generic)
  
  LAYER 2 — MODULE INTERFACE
    2a. meta.name, meta.description
    2b. ports (external data ports only)
    2c. methods (explicit method signatures with port mapping)
  
  LAYER 3 — MODULE BEHAVIORAL KNOWLEDGE
    3a. meta.knowledge (implementation algorithm)
    3b. Internal signals (declared explicitly, not inferred from connections)
  
  LAYER 4 — CHILD INTERFACES (interface contract only)
    For each child node (DEDUPLICATED by ref path):
      4a. Child's meta.name + meta.description
      4b. Child's external ports only (filter out internal)
      4c. Child's methods (signatures)
      4d. Child's provisos WITH type parameters SUBSTITUTED (derived provisos)
      4e. EXPLICIT instantiation template:
          "mkChild#(param1_val, param2_val) instance_name <- mkChild;"
      4f. EXCLUDE child's meta.knowledge (implementation detail)
  
  LAYER 5 — CONNECTION COMPUTATIONS
    For each connection GROUP (end-to-end data flow):
      5a. Source → transform 1 → signal 1 → transform 2 → ... → destination
      5b. Each transform described as: function(bit_widths)
      5c. Each signal typed explicitly
      5d. Direction validated: output → input only
  
  LAYER 6 — DERIVED PROVISO CLOSURE
    6a. Module's own provisos
    6b. Each child's provisos with param substitutions
    6c. Bit manipulation provisos (from connection computation analysis)
       - truncate → Add#(result_sz, _, source_sz)
       - concatenate → Add#(left_sz, right_sz, result_sz)
       - zeroExtend → Add#(source_sz, _, target_sz)
    6d. Deduplicate and sort for readability
  
  LAYER 7 — IMPORT GUIDANCE
    7a. Decision table: when to import each package
    7b. "Import ONLY packages your module actually uses"
    7c. Standard BSV built-ins don't need imports (Reg, Bit, Bool, Integer)

merge(module, mode="review"):
  # Same as generate, but LAYER 4 also includes:
  4g. Child's meta.knowledge (for cross-checking behavior)
  4h. Child's full generated code (for code review)
```

### Knowledge Cascade Diagram (Updated)
```
Language Level (templates/bluespec_sv/)
  ├── template.md          # BSV syntax, proviso patterns, standard lib decision table
  └── types.yaml           # BSV built-in types (Bit#(n), Bool, Reg, FIFOF)
  
Project Level (project.yaml + system_knowledge.md)
  ├── project description
  ├── target language
  ├── available packages (project-specific, e.g., PAClib, PrimUtils)
  └── project constraints
  
Module Level (top/arbiter_tree.yaml)
  ├── module's own knowledge (behavioral algorithm)
  ├── ports (external interface)
  ├── methods (explicit signatures with port mapping)
  ├── signals (internal wiring targets, explicitly typed)
  ├── nodes (submodule instances with STRUCTURED parameters)
  └── connections (validated wiring with transform descriptions)
  
Child Level (library/round_robin_arbiter.yaml)
  └── Only included as INTERFACE CONTRACT in parent's merge:
      ├── meta.name + meta.description
      ├── EXTERNAL ports only (category: data)
      ├── method signatures
      ├── PROVISOS (with parameter substitution)
      └── (EXCLUDED: meta.knowledge, internal ports, implementation details)
```

### Key Architectural Decisions

1. **Child knowledge filtering**: Parent gets ONLY the child's interface contract. Never the implementation. Eliminates P3.

2. **Proviso closure computation**: The merge script walks child provisos, substitutes type parameters, and adds bit-manipulation provisos. Eliminates P8.

3. **Signal extraction**: Internal signals are explicitly declared in `signals` section, validated against connections. Eliminates P2.

4. **Connection computation descriptions**: Each connection group gets a transform description explaining HOW data is manipulated. Eliminates P11.

5. **Language template separation**: BSV conventions move to a shared template. Project system_knowledge.md shrinks to project-specific info only. Eliminates P4.

6. **Explicit parameter bindings**: `nodes[].parameters` is a structured mapping, parsed by the merge script for type substitution. Eliminates P1.

7. **Port category filtering**: `category: internal` ports are excluded from the parent's view. Eliminates P10.

8. **Method declarations**: Explicit method signatures with port mapping bridge the gap between wiring diagrams and code. Eliminates P13.

9. **Import decision table**: The agent is told WHEN to import each package, not to blindly include all. Eliminates P9.

10. **Direction validation**: The merge script validates output→input before generating the prompt. Eliminates P7.

---

## Issues To Test After Agent Completion

- [x] Does the mid-level RoundRobinArbiter correctly import PriorityEncoder? YES
- [x] Does the top-level ArbiterTree correctly instantiate RoundRobinArbiter with the right generic parameters? YES, but provisos incomplete
- [x] Does compilation work in dependency order? (leaf → mid → top)? Leaf and mid YES, top FAILS (P8)
- [x] Is there any type mismatch between levels? Compile-time proviso errors confirm type constraint gaps
- [ ] Does each module correctly handle the case where its children haven't been generated yet? (Not tested — all generated in parallel)

---

## New Issues To Test In nested_v2 (After Redesign)

- [ ] Can the merge script compute the complete proviso transitive closure?
- [ ] Does filtering child knowledge to interface-only produce correct parent modules?
- [ ] Are import statements minimal (only what's needed)?
- [ ] Can the agent correctly implement connection transforms when given explicit transform descriptions?
- [ ] Does the language template separation work across different BSV projects?
- [ ] Is the RoundRobinArbiter rotation direction bug reproducible, or was it a one-off?
- [ ] Can we detect the rotation direction bug via the merge script (e.g., by adding an "expected behavior" test)?

---

## nested_v2 Validation Results (2026-07-01)

The redesigned merge algorithm was implemented and tested in `deli_auto_iters/nested_v2/` with a 4-level hierarchy. See `../nested_v2/state/findings_and_results.md` for full details.

### Fixes Validated:
- **P1 (Parameter Instantiation)**: ✅ Fixed — structured `parameters` in YAML + proper BSV inst syntax
- **P2 (Signal Declarations)**: ✅ Partially — signals section added to YAMLs, but agent doesn't always use names
- **P3 (Knowledge Duplication)**: ✅ Fixed — child knowledge filtered to interface contract only
- **P4 (Language Template)**: ✅ Fixed — shared `templates/bluespec_sv/template.md`
- **P5 (Type Definitions)**: ✅ Fixed — `Bit#(reqNum)` instead of `Bit_N`
- **P6 (Dependency Order)**: ⚠️ Not tested — all 4 agents ran in parallel
- **P7 (Direction Validation)**: ⚠️ Not implemented — still manual
- **P8 (Proviso Propagation)**: ✅ Fixed — complete transitive closure computed
- **P9 (Import Pollution)**: ✅ Fixed — decision table, 0 unnecessary imports in leaf
- **P10 (Internal Ports)**: ✅ Fixed — `category: internal` ports filtered from parent view
- **P11 (Connection Computations)**: ⚠️ Included in merge but agent used own approach
- **P12 (Logic Bug)**: ✅ Fixed — rotation direction corrected (i → i+1)
- **P13 (Method/Port Mapping)**: ⚠️ Methods added to YAML but not used by agent

### New Problems Found:
- **P14**: NumAlias naming collision — must filter from derived provisos
- **P15**: Constant-valued provisos cause solver interference
- **P16**: Child package import missing from guidance
- **P17**: Module naming snake_case → PascalCase conversion
- **P18**: Import analysis false positives from knowledge text
- **P19**: Verilog syntax leakage (1'b1, 1'b0)
- **P20**: valueOf(reqNum) required for bit select

### Overall Result:
4/4 modules compile (vs 2/3 in nested_v1). The knowledge merge redesign is validated as a significant improvement.
