#!/usr/bin/env python3
"""
Iteration 002 Compiler Pipeline
Uses LLM agent (ccb) for code generation from declarative YAML.
Strategy: Two-Phase (types first, then modules) + Bottom-Up.

Key improvements over iter_001:
- LLM agent instead of mechanical translation
- Declarative YAML (L0-L1 target)
- Proper knowledge merging across levels
- Parallel agent invocation for independent modules
"""

import os
import sys
import json
import yaml
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config
BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_RDMA_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
BLUE_RDMA_TEST = "/data/mmh/vibe-grpah-HDL/blue-rdma/test"
CCB = "ccb"
SIM_TIMEOUT = 180
GEN_TIMEOUT = 300

L0_BSV_KNOWLEDGE = """
## Bluespec SystemVerilog (BSV) Language Reference

BSV is a hardware description language based on Guarded Atomic Actions.

### Basic Types and Operations
- `Bit#(n)` - n-bit vector (e.g., `Bit#(32)`, `Bit#(64)`)
- `Bool` - boolean type
- `Int#(n)`, `UInt#(n)` - signed/unsigned integers

### Type Definitions
- Numeric typedefs: `typedef 32 MY_CONST;` or `typedef TAdd#(a, b) MY_CALC;`
- Type aliases: `typedef Bit#(64) ADDR;`
- `typedef enum {A, B, C} MyEnum deriving(Bits, Bounded, Eq, FShow);`
- `typedef struct { Type field; } MyStruct deriving(Bits, Bounded, FShow);`

### Numeric Type Functions
- `TAdd#(a, b)` - addition
- `TSub#(a, b)` - subtraction
- `TMul#(a, b)` - multiplication
- `TDiv#(a, b)` - integer division
- `TLog#(a)` - ceiling of log2
- `TExp#(a)` - 2^a
- `SizeOf#(T)` - bit width of type T
- `valueOf(T)` - numeric value of numeric type

### Hardware Constructs
- `Reg#(T) r <- mkReg(initVal);` or `<- mkRegU;` - register
- `Reg#(T) r[N] <- mkCReg(N, init);` - conflicting register (EHR)
- `FIFOF#(T) f <- mkFIFOF;` - FIFO with notEmpty/notFull
- `Vector#(N, Reg#(T)) vec <- replicateM(mkReg(0));` - register vector
- `Maybe#(T)` - tagged union: `tagged Valid val` or `tagged Invalid`

### Interface and Module
```
interface IfcName;
    method Type methodName(Args);
    method Action actionMethod(Args);
    method ActionValue#(T) avMethod(Args);
endinterface

module mkModName(IfcName);
    // state and rules
    return interface IfcName;
        method Type methodName(Args) = ...;
    endinterface;
endmodule
```

### Rules
- `rule rName; ... endrule`
- Attributes: `(* fire_when_enabled *)`, `(* no_implicit_conditions *)`
- `$display(...)` for debug output
- `$finish(0)` or `$finish(1)` for simulation control
- `immAssert(cond, name, fmt)` for immediate assertions

### Pattern Matching (Maybe#)
```
if (maybeVal matches tagged Valid .v) begin
    // use v
end
```

### Common Imports
- `import FIFOF :: *;` - FIFOF interface
- `import Vector :: *;` - Vector operations
- `import Reserved :: *;` - ReservedZero#(n) type
- `import GetPut :: *;` - Get/Put interfaces
- `import ClientServer :: *;` - Client/Server interfaces
- `import FShow :: *;` - fshow formatting
- `import Assert :: *;` - dynamicAssert
- `import Stmt :: *;` - Stmt type
"""

def build_prompt_from_yaml(yaml_data, module_name, module_type, dependencies=None):
    """Build a comprehensive prompt for ccb from YAML data.

    Uses the 6-level knowledge hierarchy:
    L0: Language knowledge (BSV reference)
    L1: Project-level knowledge
    L2: Interface contract (ports, methods)
    L3: Behavior knowledge (implementation details)
    L4: Connection knowledge
    L5: Port-level knowledge
    """
    parts = []

    # Header
    parts.append(f"Generate a Bluespec SystemVerilog (BSV) source file for module: **{module_name}**")
    parts.append(f"Module type: {module_type}")
    parts.append("")

    # L0: Language knowledge
    parts.append(L0_BSV_KNOWLEDGE)

    # Module description
    meta = yaml_data.get('meta', {})
    desc = yaml_data.get('design_knowledge', {}).get('description', meta.get('description', ''))
    if desc:
        parts.append(f"## Module Requirements\n{desc}")

    # L1: Project context
    proj_ctx = yaml_data.get('project_context', '')
    if proj_ctx:
        parts.append(f"\n## Project Context\n{proj_ctx}")

    # L2: Interface contract
    parts.append("\n## Interface Contract (L2)")
    if yaml_data.get('ports'):
        parts.append("### Ports")
        for p in yaml_data['ports']:
            parts.append(f"- `{p['name']}`: {p.get('direction', '')} {p.get('type', '')}" +
                        (f" // {p['description']}" if p.get('description') else ""))

    if yaml_data.get('methods'):
        parts.append("\n### Methods")
        for m in yaml_data['methods']:
            parts.append(f"- `{m['name']}`: {m.get('return_type', '')} ({m.get('args', '')})" +
                        (f" // {m['description']}" if m.get('description') else ""))

    # L3: Behavior
    behavior = yaml_data.get('behavior', {})
    if behavior:
        parts.append("\n## Implementation Guidance (L3)")
        if behavior.get('description'):
            parts.append(behavior['description'])

    if yaml_data.get('state_elements'):
        parts.append("\n### Required State Elements")
        for s in yaml_data['state_elements']:
            parts.append(f"- `{s['name']}`: {s.get('type', '')}" +
                        (f" initialized to {s['init']}" if s.get('init') else ""))

    if yaml_data.get('rules'):
        parts.append("\n### Required Rules")
        for r in yaml_data['rules']:
            parts.append(f"- `{r['name']}`: {r.get('description', '')}")

    # Type definitions (for typedef_only modules)
    if yaml_data.get('typedefs'):
        parts.append("\n## Type Definitions")
        for td in yaml_data['typedefs']:
            parts.append(f"- `{td['name']}`: {td.get('description', '')}")
            if td.get('value'):
                parts.append(f"  Value: `{td['value']}`")

    if yaml_data.get('enums'):
        parts.append("\n## Enum Types")
        for enum in yaml_data['enums']:
            parts.append(f"- `{enum['name']}`: {enum.get('description', '')}")
            parts.append(f"  Variants: {enum.get('variants', [])}")
            parts.append(f"  Deriving: {enum.get('deriving', 'Bits, Bounded, Eq, FShow')}")

    if yaml_data.get('structs'):
        parts.append("\n## Struct Types")
        for struct in yaml_data['structs']:
            parts.append(f"- `{struct['name']}`: {struct.get('description', '')}")
            parts.append(f"  Deriving: {struct.get('deriving', 'Bits, Bounded, FShow')}")
            for fld in struct.get('fields', []):
                parts.append(f"  - {fld['name']}: {fld.get('type', '?')}" +
                            (f" // {fld['description']}" if fld.get('description') else ""))

    if yaml_data.get('functions'):
        parts.append("\n## Functions")
        for func in yaml_data['functions']:
            parts.append(f"- `{func['name']}({func.get('args', '')})` → {func.get('return_type', '')}: {func.get('description', '')}")

    # Dependencies
    if dependencies:
        parts.append("\n## Dependencies (already available)")
        for dep in dependencies:
            parts.append(f"- `{dep}.bsv` - can be imported with `import {dep} :: *;`")

    # Generation instructions
    parts.append(f"""
## Output Requirements

1. Generate ONLY valid BSV source code inside a ```bsv code block.
2. Include all necessary `import` statements at the top.
3. If this is a typedef_only module: output only typedefs, enums, structs, and functions.
4. If this is a module: implement the complete interface with all methods.
5. For modules: include module body with `(* synthesize *)` if needed.
6. The generated code must compile with `bsc -elab -sim`.
7. Do NOT include any explanation outside the code block.
8. Use exact type names and module names as specified.

Generate the complete BSV source code now:""")

    return "\n".join(parts)


def call_ccb(prompt, module_name, log_dir, timeout=GEN_TIMEOUT):
    """Call ccb (Claude Code) to generate BSV code."""
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Write prompt to file
    prompt_file = log_dir / f"prompt_{module_name}.md"
    with open(prompt_file, 'w') as f:
        f.write(prompt)

    cmd = [
        CCB, "-p", prompt,
        "--permission-mode", "auto",
        "--print"
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(log_dir)
        )

        output = result.stdout

        # Save raw output
        with open(log_dir / f"raw_output_{module_name}.txt", 'w') as f:
            f.write(output)

        # Extract BSV code
        import re
        bsv_code = None

        # Try ```bsv block
        match = re.search(r'```bsv\s*\n(.*?)```', output, re.DOTALL)
        if match:
            bsv_code = match.group(1).strip()
        else:
            # Try ```bluespec block
            match = re.search(r'```bluespec\s*\n(.*?)```', output, re.DOTALL)
            if match:
                bsv_code = match.group(1).strip()
            else:
                # Try generic ``` block with BSV content
                for match in re.finditer(r'```\s*\n(.*?)```', output, re.DOTALL):
                    content = match.group(1).strip()
                    if any(kw in content for kw in ['typedef', 'module ', 'interface ', 'endmodule', 'import ']):
                        bsv_code = content
                        break

        if bsv_code:
            return True, bsv_code, ""
        else:
            return False, "", f"No BSV code block found. Output preview: {output[:500]}"

    except subprocess.TimeoutExpired:
        return False, "", "CCB generation timed out"
    except Exception as e:
        return False, "", str(e)


def compile_bsv(bsv_file, build_dir, extra_src_dirs=None):
    """Compile a BSV file with bsc."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    src_paths = [f"-p", f"+:{BLUE_RDMA_SRC}"]
    if extra_src_dirs:
        for d in extra_src_dirs:
            src_paths.extend(["-p", f"+:{d}"])

    cmd = [
        BSC, "-elab", "-sim", "-u",
        *src_paths,
        "-bdir", str(build_dir),
        "-info-dir", str(build_dir),
        "-simdir", str(build_dir),
        "-check-assert",
        "-steps", "6000000",
        "+RTS", "-K4095M", "-RTS",
        str(bsv_file)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ok = result.returncode == 0
        msg = result.stderr[-1000:] if not ok else ""
        # Also check for "Error:" in stdout
        if ok and "Error:" in result.stdout:
            ok = False
            msg = result.stdout
        return ok, msg
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
    except Exception as e:
        return False, str(e)


def run_testbench(bsv_file, test_module, testbench_file, build_dir, extra_src_dirs=None):
    """Compile and run a testbench for a module."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    src_paths = [
        "-p", f"+:{BLUE_RDMA_SRC}",
        "-p", f"+:{BLUE_RDMA_TEST}",
        "-p", f"+:{bsv_file.parent}",
    ]
    if extra_src_dirs:
        for d in extra_src_dirs:
            src_paths.extend(["-p", f"+:{d}"])

    out_flags = [
        "-bdir", str(build_dir),
        "-info-dir", str(build_dir),
        "-simdir", str(build_dir),
    ]

    common = ["-u", "-check-assert", "-steps", "6000000", "+RTS", "-K4095M", "-RTS"]

    # Compile
    compile_cmd = [BSC, "-elab", "-sim"] + src_paths + out_flags + common + ["-g", test_module, str(testbench_file)]
    result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0 or "Error:" in result.stdout:
        return False

    # Link
    link_cmd = [BSC, "-sim"] + out_flags + ["-e", test_module, "-o", str(build_dir / f"{test_module}.sh")]
    result = subprocess.run(link_cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return False

    # Simulate
    sim_script = build_dir / f"{test_module}.sh"
    try:
        result = subprocess.run([str(sim_script)], capture_output=True, text=True,
                               timeout=SIM_TIMEOUT, cwd=str(build_dir))
        output = result.stdout + result.stderr
        return result.returncode == 0 and ("PASS" in output or "passed" in output.lower())
    except:
        return False


def main():
    """Main compiler pipeline for Iteration 002."""
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_002")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    results = {}

    # Process each YAML file
    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    if not yaml_files:
        print("No YAML files found!")
        return

    for yf in yaml_files:
        if yf.name in ('project.yaml', 'types.yaml'):
            continue

        module_name = yf.stem
        print(f"\n{'='*60}")
        print(f"Processing: {module_name}")

        try:
            with open(yf) as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            print(f"  ERROR loading YAML: {e}")
            results[module_name] = {'gen_ok': False, 'error': str(e)}
            continue

        module_type = yaml_data.get('module_type', 'module')

        # Build prompt
        prompt = build_prompt_from_yaml(yaml_data, module_name, module_type)

        # Call ccb to generate BSV
        t_start = time.time()
        gen_ok, bsv_code, gen_msg = call_ccb(prompt, module_name, log_dir)
        gen_time = time.time() - t_start

        print(f"  Generation: {'OK' if gen_ok else 'FAIL'} ({gen_time:.1f}s)")

        if not gen_ok:
            print(f"  Error: {gen_msg[:200]}")
            results[module_name] = {'gen_ok': False, 'error': gen_msg[:200], 'gen_time': gen_time}
            continue

        # Write generated BSV
        bsv_path = gen_dir / f"{module_name}.bsv"
        with open(bsv_path, 'w') as f:
            f.write(bsv_code)

        # Compile
        mod_build_dir = build_dir / module_name
        compile_ok, compile_msg = compile_bsv(bsv_path, mod_build_dir, [str(gen_dir)])
        print(f"  Compile: {'PASS' if compile_ok else 'FAIL'}")
        if not compile_ok and compile_msg:
            print(f"  Error: {compile_msg[:200]}")

        results[module_name] = {
            'gen_ok': True,
            'compile_ok': compile_ok,
            'compile_msg': compile_msg[:500] if not compile_ok else '',
            'gen_time': gen_time,
            'bsv_lines': bsv_code.count('\n'),
            'bsv_bytes': len(bsv_code),
        }

    # Write results
    with open(log_dir / "results_iter_002.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)

    # Summary
    total = len(results)
    gen_ok = sum(1 for r in results.values() if r.get('gen_ok'))
    compile_ok = sum(1 for r in results.values() if r.get('compile_ok'))

    print(f"\n{'='*60}")
    print(f"Iteration 002 Summary:")
    print(f"  Generated: {gen_ok}/{total}")
    print(f"  Compiled:  {compile_ok}/{total}")
    print(f"  FPC: {compile_ok/total:.3f}" if total > 0 else "  FPC: N/A")

if __name__ == "__main__":
    main()
