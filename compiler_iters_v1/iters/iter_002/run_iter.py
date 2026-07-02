#!/usr/bin/env python3
"""
Iteration 002 Pipeline Runner - Compact prompt edition.
Uses minimal L0 knowledge and focused prompts for faster ccb generation.
"""

import os, sys, json, yaml, subprocess, time, re
from pathlib import Path
from datetime import datetime

# Config
BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
BLUE_TEST = "/data/mmh/vibe-grpah-HDL/blue-rdma/test"
CCB = "ccb"
SIM_TIMEOUT = 180
GEN_TIMEOUT = 180

MINIMAL_BSV_KNOWLEDGE = """## BSV Quick Reference
- typedef VALUE NAME; — numeric constant (e.g., `typedef 32 X;` or `typedef TAdd#(a,b) Y;`)
- typedef Bit#(W) NAME; — bit vector type alias
- typedef enum {A=3'h0, B=3'h1} T deriving(Bits,Eq,FShow); — enumeration
- typedef struct { T1 f1; T2 f2; } S deriving(Bits,FShow); — struct
- SizeOf#(T) — bit width; TDiv#(a,b) — division; TExp#(n) — 2^n
- valueOf(X) — numeric value of typedef
- ReservedZero#(n) — n-bit reserved field (requires `import Reserved :: *;`)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method RTYPE NAME(ARGS); endinterface
- module mkNAME(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;
- Reg#(T) r[N] <- mkCReg(N, v);
- Bool, Bit#(n), Maybe#(T) with tagged Valid v / tagged Invalid
- case (expr) matches tagged Valid .v: ... endcase
- pack(v) / unpack(b) convert to/from bits
"""

def build_compact_prompt(yaml_data, module_name, module_type):
    """Build a compact prompt optimized for ccb speed."""
    parts = []

    # Core instruction
    parts.append(f"Generate the Bluespec SystemVerilog file for: {module_name}")
    parts.append(f"Module type: {module_type}")
    parts.append("")

    # Minimal BSV knowledge
    parts.append(MINIMAL_BSV_KNOWLEDGE)

    # Module description
    meta = yaml_data.get('meta', {})
    dk = yaml_data.get('design_knowledge', {})
    desc = dk.get('description', meta.get('description', ''))
    if desc:
        parts.append(f"\n## Requirements\n{desc}")

    # Typedefs (compact)
    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        parts.append("\n## Type Definitions (output EXACTLY these)")
        for td in typedefs:
            parts.append(f"typedef {td['value']} {td['name']}; // {td.get('description', td['name'])}")

    # Enums (compact)
    enums = yaml_data.get('enums', [])
    if enums:
        parts.append("\n## Enums")
        for enum in enums:
            parts.append(f"typedef enum {{")
            for v in enum.get('variants', []):
                parts.append(f"    {v},")
            parts.append(f"}} {enum['name']} deriving({enum.get('deriving', 'Bits,Bounded,Eq,FShow')});")

    # Structs (compact)
    structs = yaml_data.get('structs', [])
    if structs:
        parts.append("\n## Structs")
        for struct in structs:
            parts.append(f"typedef struct {{")
            for fld in struct.get('fields', []):
                parts.append(f"    {fld['type']} {fld['name']}; // {fld.get('description', '')}")
            parts.append(f"}} {struct['name']} deriving({struct.get('deriving', 'Bits,Bounded,FShow')});")
            # Add SizeOf/TDiv typedefs
            parts.append(f"typedef SizeOf#({struct['name']}) {struct['name']}_WIDTH;")
            parts.append(f"typedef TDiv#({struct['name']}_WIDTH, 8) {struct['name']}_BYTE_WIDTH;")

    # Functions (compact)
    funcs = yaml_data.get('functions', [])
    if funcs:
        parts.append("\n## Functions")
        for func in funcs:
            fname = func.get('name', 'unknown')
            ret = func.get('return_type', '?')
            args = func.get('args', '')
            desc = func.get('description', '')
            bsv = func.get('bsv_equivalent', '')
            if bsv:
                parts.append(f"\n// Function: {fname}")
                parts.append(bsv)
            else:
                parts.append(f"\nfunction {ret} {fname}({args});")
                if desc:
                    parts.append(f"// {desc}")
                parts.append(f"// Implement using BSV syntax. end with endfunction")

    # Module specific
    md = yaml_data.get('module_def', {})
    if md:
        parts.append(f"\n## Module: {md.get('name', module_name)}")
        if md.get('interface_name'):
            parts.append(f"Interface: {md['interface_name']}")
        for m in md.get('methods', []):
            parts.append(f"  method {m['return_type']} {m['name']}({m['args']});")

    behavior = yaml_data.get('behavior', {})
    if behavior.get('description'):
        parts.append(f"\n## Implementation\n{behavior['description']}")

    state = yaml_data.get('state_elements', [])
    if state:
        parts.append("\nState elements:")
        for s in state:
            parts.append(f"  {s['name']}: {s['type']} = {s.get('init', '?')}")

    rules = yaml_data.get('rules', [])
    if rules:
        parts.append("\nRules:")
        for r in rules:
            parts.append(f"  {r['name']}: {r.get('description', '')}")

    # Final instruction
    parts.append(f"""

Output ONLY the valid BSV code in a ```bsv block. No explanations.
Include all needed import statements.
The code must compile with: bsc -elab -sim {module_name}.bsv

Generate BSV now:""")

    return "\n".join(parts)


def gen_module(yaml_path, module_name, module_type, out_dir, log_dir, timeout=GEN_TIMEOUT):
    """Generate BSV for one module."""
    with open(yaml_path) as f:
        yaml_data = yaml.safe_load(f)

    prompt = build_compact_prompt(yaml_data, module_name, module_type)
    prompt_size = len(prompt)

    # Save prompt
    prompt_file = Path(log_dir) / f"prompt_{module_name}.md"
    with open(prompt_file, 'w') as f:
        f.write(prompt)

    # Call ccb
    t0 = time.time()
    try:
        result = subprocess.run(
            [CCB, "-p", prompt, "--permission-mode", "auto", "--print"],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(log_dir))
        )
        output = result.stdout
        elapsed = time.time() - t0

        # Extract code block
        code = None
        for m in re.finditer(r'```(?:bsv|bluespec)?\s*\n(.*?)```', output, re.DOTALL):
            content = m.group(1).strip()
            if any(kw in content for kw in ['typedef', 'module ', 'interface ', 'endmodule', 'import ', 'function ']):
                code = content
                break

        if not code:
            # Last resort: take any code-like block
            for m in re.finditer(r'```\s*\n(.*?)```', output, re.DOTALL):
                code = m.group(1).strip()
                break

        if code:
            bsv_path = Path(out_dir) / f"{module_name}.bsv"
            with open(bsv_path, 'w') as f:
                f.write(code)
            return {'ok': True, 'elapsed': elapsed, 'size': len(code), 'prompt_size': prompt_size}
        else:
            return {'ok': False, 'elapsed': elapsed, 'error': 'No code block', 'raw': output[:500],
                    'prompt_size': prompt_size}

    except subprocess.TimeoutExpired:
        return {'ok': False, 'elapsed': timeout, 'error': 'Timeout', 'prompt_size': prompt_size}
    except Exception as e:
        return {'ok': False, 'elapsed': time.time() - t0, 'error': str(e), 'prompt_size': prompt_size}


def compile_bsv(bsv_file, build_dir):
    """Compile BSV file."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = bsv_file.parent

    cmd = [
        BSC, "-elab", "-sim", "-u",
        "-p", f"+:{BLUE_SRC}",
        "-p", f"+:{gen_dir}",
        "-bdir", str(build_dir), "-info-dir", str(build_dir), "-simdir", str(build_dir),
        "-check-assert", "-steps", "6000000",
        "+RTS", "-K4095M", "-RTS",
        str(bsv_file)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ok = result.returncode == 0 and "Error:" not in result.stdout
        msg = result.stderr[-500:] if not ok else ""
        if "Error:" in result.stdout:
            msg = result.stdout
        return ok, msg
    except:
        return False, "Exception"


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_002")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    results = {}
    yaml_files = sorted(yaml_dir.glob("*.yaml"))

    for yf in yaml_files:
        if yf.name in ('project.yaml', 'types.yaml'):
            continue

        name = yf.stem
        print(f"\n--- {name} ---")

        with open(yf) as f:
            data = yaml.safe_load(f)
        mtype = data.get('module_type', 'module')

        # Generate
        r = gen_module(str(yf), name, mtype, gen_dir, log_dir)
        print(f"  Gen: {'OK' if r['ok'] else 'FAIL'} ({r['elapsed']:.1f}s, prompt={r['prompt_size']}B)")

        if not r['ok']:
            print(f"  Error: {r.get('error', 'unknown')[:200]}")
            results[name] = {'gen_ok': False, 'error': r.get('error', ''), 'gen_time': r['elapsed']}
            continue

        # Compile
        bsv_path = gen_dir / f"{name}.bsv"
        comp_ok, comp_msg = compile_bsv(bsv_path, build_dir / name)
        print(f"  Compile: {'PASS' if comp_ok else 'FAIL'}")
        if not comp_ok and comp_msg:
            # Show first error line
            err_lines = [l for l in comp_msg.split('\n') if 'Error' in l]
            if err_lines:
                print(f"  {err_lines[0][:200]}")

        results[name] = {
            'gen_ok': True, 'compile_ok': comp_ok,
            'gen_time': r['elapsed'], 'bsv_bytes': r['size'],
            'prompt_size': r['prompt_size']
        }

    # Summary
    with open(log_dir / "results_iter_002.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)

    total = len(results)
    gen_count = sum(1 for v in results.values() if v.get('gen_ok'))
    comp_count = sum(1 for v in results.values() if v.get('compile_ok'))
    print(f"\n{'='*60}")
    print(f"Iter 002: Generated {gen_count}/{total}, Compiled {comp_count}/{total}, FPC={comp_count/max(total,1):.3f}")

if __name__ == "__main__":
    main()
