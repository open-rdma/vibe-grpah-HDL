# Knowledge Merge Problems & Redesign Proposals

## Experiment: nested_v1 (PriorityArbiter 3-level system)

Date: 2026-07-01

---

## Problems Found During Design

### P1: Port Type Mismatch Between Parent and Child Connections (CRITICAL)

**Description:** When a parent module references a child module's port in `connections`, there is no explicit mapping of the child's generic type parameter to the parent's type. For example, the `arbiter_tree` instantiates `RoundRobinArbiter#(TDiv#(reqNum, 2))`, but the generic parameter mapping is stored as `properties: { reqNum: "TDiv#(reqNum, 2)" }` — a string, not a structured type binding.

**Impact:** The generation agent for the parent module has to INFER the parameter instantiation from context rather than receiving explicit type bindings. This leads to type errors.

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

For example, `mkPriorityEncoder` knowledge appears in both the PriorityEncoder generation prompt AND the RoundRobinArbiter generation prompt.

**Impact:** 
- Larger prompts (wasteful)
- Risk of stale knowledge: if parent was generated first and child's knowledge later changes, parent is out of sync
- The parent should only need the child's INTERFACE CONTRACT (methods + ports), not its internal implementation details

**Proposed Fix:** In the parent's merged prompt, include only the child's INTERFACE (ports + method signatures), not its behavioral knowledge. The child's behavioral knowledge is the child's own responsibility:
```python
# In merge_knowledge.py, for child nodes:
# Include: child's ports (interface contract)
# Include: child's meta.name and meta.description
# EXCLUDE: child's meta.knowledge (implementation detail)
```

### P4: No BSV-Specific Language Template (HIGH)

**Description:** The `system_knowledge.md` is copied into each project individually. BSV coding conventions (module syntax, proviso patterns, standard library usage) should be a SHARED TEMPLATE at the language level, not duplicated per-project.

**Impact:** Every project's `system_knowledge.md` re-describes the same BSV conventions. This is fragile — if conventions change, every project must be updated.

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
2. Project knowledge: `project.yaml` + `system_knowledge.md`
3. Module knowledge: `<module>.yaml`
4. Child interfaces (one level down): `<child>.yaml` ports only

### P5: Type Definitions Are Overly Generic (MEDIUM)

**Description:** The `types.yaml` uses generic names like `Bit_N`, `PipeOut_T` which don't convey the actual type parameterization. When a generation agent sees `type: "Bit_N"` on a port, it has to guess the actual bit width from context.

**Impact:** The agent can't mechanically verify that connections are type-safe. A port described as `type: "Bit_N"` connected to another `type: "Bit_N"` might have mismatched widths at compile time.

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

**Impact:** If agents run in parallel, the mid-level agent generates code importing PriorityEncoder, but PriorityEncoder.bsv might not exist yet. Compilation order is not handled.

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

## Proposed Merge Algorithm Redesign

### Current Algorithm (nested_v1)
```
merge(module):
  1. Include project system_knowledge.md
  2. Include types.yaml
  3. Include module's own meta.knowledge + ports
  4. For each child node:
     a. Include child's meta.knowledge (FULL)    ← PROBLEM: includes implementation
     b. Include child's ports
  5. Include wiring connections
```

### Proposed Algorithm (nested_v2)
```
merge(module, mode="generate"):
  1. Include LANGUAGE TEMPLATE (shared BSV conventions)
  2. Include project-level types and shared knowledge
  3. Include module's own meta.knowledge + ports
  
  4. For each child node:
     a. Include child's meta.name + meta.description
     b. Include child's PORTS ONLY (interface contract)
     c. Include child's instantiation PARAMETERS (explicit type bindings)
     d. EXCLUDE child's meta.knowledge (implementation detail)
  
  5. Include module's internal SIGNALS (explicitly declared)
  6. Include wiring CONNECTIONS (validated for direction)
  7. Include module's TEST METHOD

merge(module, mode="review"):
  # Same as generate, but also includes:
  4e. Include child's meta.knowledge (for cross-checking behavior)
```

### Knowledge Cascade Diagram
```
Language Level (templates/bluespec_sv/)
  ├── template.md          # BSV syntax, proviso patterns, standard lib
  └── types.yaml           # BSV built-in types
  
Project Level (project.yaml + system_knowledge.md)
  ├── project description
  ├── target language
  └── project-specific conventions
  
Module Level (top/arbiter_tree.yaml)
  ├── module's own knowledge (behavioral description)
  ├── ports (interface)
  ├── signals (internal wiring targets)
  ├── nodes (submodule instances with parameters)
  └── connections (validated wiring)
  
Child Level (library/round_robin_arbiter.yaml)
  └── Only included as interface contract in parent's merge
      (ports + method signatures, NOT behavioral knowledge)
```

---

## Issues to Test After Agent Completion

- [ ] Does the mid-level RoundRobinArbiter correctly import PriorityEncoder?
- [ ] Does the top-level ArbiterTree correctly instantiate RoundRobinArbiter with the right generic parameters?
- [ ] Does compilation work in dependency order? (leaf → mid → top)
- [ ] Is there any type mismatch between levels (e.g., Bit#(reqNum) vs Bit#(TDiv#(reqNum, 2)))?
- [ ] Does each module correctly handle the case where its children haven't been generated yet?
