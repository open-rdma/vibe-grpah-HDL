#!/usr/bin/env python3
"""
Iteration 003 Compiler - Split-Prompt Strategy

Key improvements:
1. Split complex modules: Phase 1 (types/typedefs) → Phase 2 (functions/modules)
2. Handle ccb output: check BOTH stdout code blocks AND generated files on disk
3. Minimal L0 knowledge for typedef_only modules
4. Parallel generation (4 concurrent ccb calls)
5. Works with all YAML formats (declarative AND auto-generated from iter_001)
"""

import os, sys, json, yaml, subprocess, time, re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
CCB = "ccb"
GEN_TIMEOUT = 120  # per ccb call
COMPILE_TIMEOUT = 60

TINY_BSV_REF = """BSV syntax:
- typedef VALUE NAME; — numeric constant
- typedef Bit#(W) NAME; — bit vector alias
- typedef enum {A=3'h0,B=3'h1} T deriving(Bits,Eq,FShow);
- typedef struct { T1 f; T2 g; } S deriving(Bits,FShow);
- SizeOf#(T); TDiv#(a,b); TExp#(n); TAdd#(a,b); TMul#(a,b)
- import Reserved :: *; for ReservedZero#(n)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method T m(args); endinterface
- module mkM(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;
"""

def build_tiny_typedef_prompt(yaml_data, module_name):
    """Minimal prompt for typedef-only modules."""
    parts = [f"Output the following BSV typedefs as a ```bsv code block. No explanations.\n"]
    for td in yaml_data.get('typedefs', []):
        val = td.get('value', td.get('bsv_equivalent', '?')).replace('typedef ', '').rstrip(';')
        parts.append(f"typedef {val} {td['name']};")
    parts.append("\n```bsv")
    return "\n".join(parts)

def build_split_prompt_types(yaml_data, module_name):
    """Phase 1: Types only - typedefs, enums, structs."""
    parts = [TINY_BSV_REF, f"\nGenerate BSV types for: {module_name}\n"]

    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        parts.append("Typedefs:")
        for td in typedefs:
            val = td.get('value', td.get('bsv_equivalent', '?')).replace('typedef ', '').rstrip(';')
            parts.append(f"  typedef {val} {td['name']};")

    enums = yaml_data.get('enums', [])
    if enums:
        parts.append("\nEnums:")
        for enum in enums:
            parts.append(f"  typedef enum {{")
            for v in enum.get('variants', []):
                parts.append(f"    {v},")
            parts.append(f"  }} {enum['name']} deriving({enum.get('deriving', 'Bits,Eq,FShow')});")

    structs = yaml_data.get('structs', [])
    if structs:
        parts.append("\nStructs:")
        for struct in structs:
            parts.append(f"  typedef struct {{")
            for f in struct.get('fields', []):
                parts.append(f"    {f['type']} {f['name']};")
            parts.append(f"  }} {struct['name']} deriving({struct.get('deriving', 'Bits,FShow')});")
            parts.append(f"  typedef SizeOf#({struct['name']}) {struct['name']}_WIDTH;")
            parts.append(f"  typedef TDiv#({struct['name']}_WIDTH, 8) {struct['name']}_BYTE_WIDTH;")

    parts.append(f"\nOutput in ```bsv block. Include imports. Generate now:")
    return "\n".join(parts)

def build_split_prompt_functions(yaml_data, module_name, types_done):
    """Phase 2: Functions only."""
    funcs = yaml_data.get('functions', [])
    if not funcs:
        return None

    parts = [TINY_BSV_REF, f"\nGenerate BSV functions for: {module_name}"]
    parts.append(f"\nTypes already defined (import them): {', '.join(types_done)}")

    for func in funcs:
        fname = func.get('name', '?')
        ret = func.get('return_type', '?')
        args = func.get('args', '')
        desc = func.get('description', '')
        bsv = func.get('bsv_equivalent', '')
        parts.append(f"\nfunction {ret} {fname}({args});")
        if desc:
            parts.append(f"  // {desc}")
        if bsv:
            parts.append(f"  // Reference implementation:\n  // {bsv[:500]}")

    parts.append(f"\nOutput in ```bsv block. Include imports referencing existing types. Generate now:")
    return "\n".join(parts)

def call_ccb_and_extract(prompt, module_name, cwd, timeout=GEN_TIMEOUT):
    """Call ccb and extract BSV code from output OR generated file."""
    cwd = Path(cwd)

    # Save prompt
    prompt_file = cwd / f"prompt_{module_name}.md"
    with open(prompt_file, 'w') as f:
        f.write(prompt)

    # Record files before ccb runs
    before_files = set(str(p) for p in cwd.glob("*.bsv"))

    try:
        result = subprocess.run(
            [CCB, "-p", prompt, "--permission-mode", "auto", "--print"],
            capture_output=True, text=True, timeout=timeout,
            cwd=str(cwd)
        )
        output = result.stdout

        # Try code block extraction
        code = None
        for m in re.finditer(r'```(?:bsv|bluespec)?\s*\n(.*?)```', output, re.DOTALL):
            content = m.group(1).strip()
            if len(content) > 20:
                code = content
                break

        # If no code block, check for newly created files
        if not code:
            after_files = set(str(p) for p in cwd.glob("*.bsv"))
            new_files = after_files - before_files
            for nf in new_files:
                if module_name.lower() in Path(nf).stem.lower():
                    with open(nf) as f:
                        code = f.read().strip()
                    break

        if code:
            return True, code, ""
        else:
            return False, "", f"No code extracted. stdout: {output[:300]}"

    except subprocess.TimeoutExpired:
        # Check for files even on timeout
        after_files = set(str(p) for p in cwd.glob("*.bsv"))
        new_files = after_files - before_files
        for nf in new_files:
            if module_name.lower() in Path(nf).stem.lower():
                with open(nf) as f:
                    code = f.read().strip()
                if len(code) > 20:
                    return True, code, ""
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)


def compile_bsv(bsv_path, build_dir):
    """Compile a BSV file."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [BSC, "-elab", "-sim", "-u",
           "-p", f"+:{BLUE_SRC}", "-p", f"+:{bsv_path.parent}",
           "-bdir", str(build_dir), "-info-dir", str(build_dir), "-simdir", str(build_dir),
           "-check-assert", "-steps", "6000000",
           "+RTS", "-K4095M", "-RTS", str(bsv_path)]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ok = result.returncode == 0 and "Error:" not in result.stdout
        return ok, result.stdout if not ok else ""
    except:
        return False, "Exception"


def process_module(name, yaml_path, gen_dir, log_dir, build_dir):
    """Process one module through the full pipeline."""
    log_dir = Path(log_dir)
    gen_dir = Path(gen_dir)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    mtype = data.get('module_type', 'module')
    result = {'name': name, 'mtype': mtype}

    # Step 1: Generate types
    t0 = time.time()

    if mtype == 'typedef_only':
        prompt = build_tiny_typedef_prompt(data, name)
        ok, code, msg = call_ccb_and_extract(prompt, name, log_dir)
        result['gen_time'] = time.time() - t0
        if not ok:
            result['gen_ok'] = False
            result['error'] = msg[:200]
            return result
        combined_code = code
    else:
        # Phase 1: Types
        prompt1 = build_split_prompt_types(data, name)
        ok1, code1, msg1 = call_ccb_and_extract(prompt1, f"{name}_types", log_dir)
        if not ok1:
            result['gen_time'] = time.time() - t0
            result['gen_ok'] = False
            result['error'] = f"Phase1 types: {msg1[:200]}"
            return result

        # Phase 2: Functions (if any)
        prompt2 = build_split_prompt_functions(data, name, [name])
        if prompt2:
            ok2, code2, msg2 = call_ccb_and_extract(prompt2, f"{name}_funcs", log_dir)
            combined_code = code1 + "\n\n" + (code2 if ok2 else "")
        else:
            combined_code = code1

        result['gen_time'] = time.time() - t0

    # Write combined code
    bsv_path = gen_dir / f"{name}.bsv"
    with open(bsv_path, 'w') as f:
        f.write(combined_code)
    result['gen_ok'] = True
    result['bsv_bytes'] = len(combined_code)

    # Step 2: Compile
    comp_ok, comp_msg = compile_bsv(bsv_path, build_dir / name)
    result['compile_ok'] = comp_ok
    if not comp_ok:
        err_lines = [l for l in comp_msg.split('\n') if 'Error' in l]
        result['compile_error'] = err_lines[0][:200] if err_lines else 'Unknown'

    return result


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_003")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy YAML from iter_002
    src_yaml = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_002/yaml")
    for yf in src_yaml.glob("*.yaml"):
        if yf.name == 'project.yaml':
            continue
        dst = yaml_dir / yf.name
        if not dst.exists():
            import shutil
            shutil.copy(yf, dst)

    yaml_files = sorted(yaml_dir.glob("*.yaml"))

    results = {}
    print(f"Processing {len(yaml_files)} modules...")

    # Process modules with up to 4 parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for yf in yaml_files:
            name = yf.stem
            future = executor.submit(process_module, name, str(yf), gen_dir, log_dir, build_dir)
            futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                r = future.result()
                results[name] = r
                status = []
                if r.get('gen_ok'):
                    status.append("GEN")
                    if r.get('compile_ok'):
                        status.append("COMPILE")
                    else:
                        status.append("COMPILE_FAIL")
                else:
                    status.append("GEN_FAIL")
                print(f"  {name}: {' '.join(status)} ({r.get('gen_time', 0):.1f}s)")
            except Exception as e:
                print(f"  {name}: ERROR {e}")
                results[name] = {'gen_ok': False, 'error': str(e)}

    # Summary
    total = len(results)
    gen_ok = sum(1 for r in results.values() if r.get('gen_ok'))
    comp_ok = sum(1 for r in results.values() if r.get('compile_ok'))

    summary = {
        'iteration': 'iter_003',
        'strategy': 'split_prompt_phased',
        'timestamp': datetime.now().isoformat(),
        'total_modules': total,
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'fpc': comp_ok / max(total, 1),
        'results': {k: {kk: vv for kk, vv in v.items() if kk != 'compile_error'}
                    for k, v in results.items()}
    }

    with open(log_dir / "summary_iter_003.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nIter 003: Gen={gen_ok}/{total}, Compile={comp_ok}/{total}, FPC={comp_ok/max(total,1):.3f}")

if __name__ == "__main__":
    main()
