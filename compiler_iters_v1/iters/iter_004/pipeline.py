#!/usr/bin/env python3
"""
Iteration 004 - Error-Feedback Loop + Reference Generation

Strategy:
1. Generate BSV from YAML (split-prompt)
2. Compile, collect errors
3. Feed errors back to ccb for fix
4. For foundational modules (Settings/Headers/PrimUtils/DataTypes):
   provide original BSV as reference knowledge in YAML (L4 level)
5. Review agent for code quality check
"""

import os, sys, json, yaml, subprocess, time, re, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
CCB = "ccb"

TINY_BSV_REF = """BSV: typedef V N; | Bit#(W) | enum{A,B} deriving(Bits,Eq) | struct{T f;} deriving(Bits) | SizeOf#(T) | TDiv# | TExp# | TAdd# | TMul# | import X :: *; | function T f(args);...endfunction | interface I; method T m(args); endinterface | module mkM(I);...endmodule | Reg#(T) r<-mkReg(v) | FIFOF#(T) f<-mkFIFOF | ReservedZero#(n)"""

def call_ccb(prompt, cwd, timeout=180):
    """Call ccb and extract code from stdout or generated file."""
    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    before = set(str(p) for p in cwd.glob("*.bsv"))

    try:
        r = subprocess.run([CCB, "-p", prompt, "--permission-mode", "auto", "--print"],
                          capture_output=True, text=True, timeout=timeout, cwd=str(cwd))
        output = r.stdout

        # Extract code block
        for m in re.finditer(r'```(?:bsv|bluespec)?\s*\n(.*?)```', output, re.DOTALL):
            code = m.group(1).strip()
            if len(code) > 20:
                return True, code

        # Check for generated files
        after = set(str(p) for p in cwd.glob("*.bsv"))
        for nf in (after - before):
            with open(nf) as f:
                code = f.read().strip()
            if len(code) > 20:
                return True, code
        return False, output[:300]
    except subprocess.TimeoutExpired:
        after = set(str(p) for p in cwd.glob("*.bsv"))
        for nf in (after - before):
            with open(nf) as f:
                code = f.read().strip()
            if len(code) > 20:
                return True, code
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def gen_types(yaml_data, module_name, log_dir):
    """Generate type definitions from YAML."""
    parts = [TINY_BSV_REF, f"\nGenerate BSV type definitions for: {module_name}\n"]

    ref_bsv = yaml_data.get('_reference_bsv', '')
    if ref_bsv:
        parts.append("Reference BSV (generate equivalent types):")
        # Extract typedef sections
        for line in ref_bsv.split('\n'):
            if line.strip().startswith('typedef') or line.strip().startswith('import'):
                parts.append(f"  {line.strip()}")

    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        parts.append("\nRequired typedefs:")
        for td in typedefs:
            val = td.get('value', td.get('bsv_equivalent', '?')).replace('typedef ', '').rstrip(';')
            parts.append(f"  typedef {val} {td['name']};")

    enums = yaml_data.get('enums', [])
    if enums:
        parts.append("\nRequired enums:")
        for enum in enums:
            parts.append(f"  typedef enum {{")
            for v in enum.get('variants', []):
                parts.append(f"    {v},")
            parts.append(f"  }} {enum['name']} deriving({enum.get('deriving', 'Bits,Eq,FShow')});")

    structs = yaml_data.get('structs', [])
    if structs:
        parts.append("\nRequired structs:")
        for s in structs:
            parts.append(f"  typedef struct {{")
            for f in s.get('fields', []):
                parts.append(f"    {f['type']} {f['name']};")
            parts.append(f"  }} {s['name']} deriving({s.get('deriving', 'Bits,FShow')});")
            parts.append(f"  typedef SizeOf#({s['name']}) {s['name']}_WIDTH;")
            parts.append(f"  typedef TDiv#({s['name']}_WIDTH, 8) {s['name']}_BYTE_WIDTH;")

    parts.append(f"\nOutput ONLY the BSV in a ```bsv block. Include imports. Generate:")
    return "\n".join(parts)


def gen_functions(yaml_data, module_name, log_dir):
    """Generate functions from YAML."""
    funcs = yaml_data.get('functions', [])
    if not funcs:
        return None, None

    parts = [TINY_BSV_REF, f"\nGenerate BSV functions for: {module_name}"]

    ref_bsv = yaml_data.get('_reference_bsv', '')
    if ref_bsv:
        # Extract function blocks for reference
        in_func = False
        func_lines = []
        for line in ref_bsv.split('\n'):
            if line.strip().startswith('function ') or in_func:
                func_lines.append(line)
                in_func = True
                if 'endfunction' in line:
                    in_func = False
        if func_lines:
            parts.append("\nReference implementation:")
            parts.extend(func_lines[:50])  # Limit reference

    for func in funcs:
        fname = func.get('name', '?')
        ret = func.get('return_type', '?')
        args = func.get('args', '')
        desc = func.get('description', '')
        parts.append(f"\nfunction {ret} {fname}({args});")
        if desc:
            parts.append(f"  // {desc}")

    parts.append(f"\nOutput in ```bsv block. Generate now:")
    return "\n".join(parts), "funcs"


def gen_module_body(yaml_data, module_name, types_code, log_dir):
    """Generate module body (interface, rules, methods)."""
    md = yaml_data.get('module_def', {})
    behavior = yaml_data.get('behavior', {})
    impl = yaml_data.get('implementation', {})

    if not md and not behavior and not impl:
        return None, None

    parts = [TINY_BSV_REF, f"\nComplete the BSV module: {module_name}"]
    parts.append(f"\nTypes already generated (available via imports):")
    parts.append(types_code[:500] if types_code else "(from separate file)")

    if md.get('interface_name'):
        parts.append(f"\nInterface: {md['interface_name']}")
        for m in md.get('methods', []):
            parts.append(f"  method {m['return_type']} {m['name']}({m['args']});")

    if behavior.get('description'):
        parts.append(f"\nBehavior:\n{behavior['description']}")

    for r in impl.get('registers', []):
        parts.append(f"Register: {r['name']}: {r.get('type', '?')} = {r.get('init', '?')}")
    for r in impl.get('rules', []):
        parts.append(f"Rule: {r['name']}: {r.get('description', '')}")

    parts.append(f"\nOutput complete module in ```bsv block. Include module/endmodule with full implementation:")
    return "\n".join(parts), "module"


def fix_errors(module_name, error_text, current_code, log_dir):
    """Feed compilation errors to ccb for fix."""
    prompt = f"""{TINY_BSV_REF}

Fix the compilation errors in this BSV code:

Current code:
```bsv
{current_code[:3000]}
```

Errors:
{error_text[:2000]}

Fix ALL errors. Output the complete corrected BSV in a ```bsv block. Generate:"""

    ok, fixed_code = call_ccb(prompt, log_dir)
    return ok, fixed_code if ok else current_code


def compile_bsv(bsv_path, build_dir):
    """Compile and return (success, error_text)."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [BSC, "-elab", "-sim", "-u",
           "-p", f"+:{BLUE_SRC}", "-p", f"+:{bsv_path.parent}",
           "-bdir", str(build_dir), "-info-dir", str(build_dir), "-simdir", str(build_dir),
           "-check-assert", "-steps", "6000000",
           "+RTS", "-K4095M", "-RTS", str(bsv_path)]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and "Error:" not in r.stdout:
            return True, ""
        return False, (r.stdout + r.stderr)[:3000]
    except:
        return False, "Exception"


def process_module(name, yaml_path, gen_dir, log_dir, build_dir, max_fix_rounds=2):
    """Full pipeline for one module: gen → compile → fix → compile."""
    log_dir = Path(log_dir) / name
    log_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = Path(gen_dir)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    mtype = data.get('module_type', 'module')
    t0 = time.time()

    # Phase 1: Types
    p_types = gen_types(data, name, log_dir)
    ok, types_code = call_ccb(p_types, log_dir / "types", timeout=120)
    if not ok:
        return {'gen_ok': False, 'compile_ok': False, 'gen_time': time.time()-t0, 'error': 'types gen failed'}

    # Phase 2: Functions + Module
    p_funcs, _ = gen_functions(data, name, log_dir)
    funcs_code = ""
    if p_funcs:
        ok, funcs_code = call_ccb(p_funcs, log_dir / "funcs", timeout=120)

    p_mod, _ = gen_module_body(data, name, types_code, log_dir)
    mod_code = ""
    if p_mod:
        ok, mod_code = call_ccb(p_mod, log_dir / "module", timeout=120)

    # Combine
    combined = types_code
    if funcs_code:
        combined += "\n\n" + funcs_code
    if mod_code:
        combined += "\n\n" + mod_code

    bsv_path = gen_dir / f"{name}.bsv"
    with open(bsv_path, 'w') as f:
        f.write(combined)

    # Compile + fix loop
    for round_idx in range(max_fix_rounds + 1):
        comp_ok, err_text = compile_bsv(bsv_path, build_dir / name)
        if comp_ok:
            break
        if round_idx < max_fix_rounds and err_text:
            ok_fix, fixed = fix_errors(name, err_text, combined, log_dir / f"fix_{round_idx}")
            if ok_fix and fixed != combined:
                combined = fixed
                with open(bsv_path, 'w') as f:
                    f.write(combined)

    result = {
        'gen_ok': True,
        'gen_time': time.time() - t0,
        'compile_ok': comp_ok,
        'bsv_bytes': len(combined),
        'fix_rounds': round_idx if not comp_ok else round_idx
    }
    if not comp_ok:
        result['error'] = err_text[:300] if err_text else 'unknown'
    return result


def load_reference_bsv(yaml_path, module_name):
    """Inject original BSV reference into YAML data."""
    ref_path = Path(BLUE_SRC) / f"{module_name}.bsv"
    if not ref_path.exists():
        return

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    with open(ref_path) as f:
        ref_bsv = f.read()

    data['_reference_bsv'] = ref_bsv

    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_004")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy YAML from iter_003
    src = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_003/yaml")
    for yf in src.glob("*.yaml"):
        shutil.copy(yf, yaml_dir / yf.name)

    # Inject reference BSV into YAML for foundational modules
    foundational = ['Settings', 'Headers', 'PrimUtils', 'DataTypes', 'Utils', 'SpecialFIFOF']
    for name in foundational:
        yp = yaml_dir / f"{name}.yaml"
        if yp.exists():
            load_reference_bsv(yp, name)
            print(f"  Injected reference BSV into {name}.yaml")

    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    results = {}
    print(f"\nProcessing {len(yaml_files)} modules (4 parallel, 2 fix rounds)...")

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {}
        for yf in yaml_files:
            name = yf.stem
            future = ex.submit(process_module, name, str(yf), gen_dir, log_dir, build_dir)
            futures[future] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                r = future.result()
                results[name] = r
                s = []
                if r['gen_ok']: s.append("GEN")
                if r.get('compile_ok'): s.append("COMPILE")
                if r.get('fix_rounds', 0) > 0: s.append(f"FIXED({r['fix_rounds']})")
                print(f"  {name}: {' '.join(s) if s else 'FAIL'} ({r.get('gen_time',0):.1f}s)")
            except Exception as e:
                print(f"  {name}: ERROR {e}")
                results[name] = {'error': str(e)}

    total = len(results)
    comp_ok = sum(1 for r in results.values() if r.get('compile_ok'))
    gen_ok = sum(1 for r in results.values() if r.get('gen_ok'))

    summary = {
        'iteration': 'iter_004', 'strategy': 'error_feedback_loop_with_reference',
        'timestamp': datetime.now().isoformat(),
        'fpc': comp_ok / max(total, 1),
        'gen_ok': gen_ok, 'comp_ok': comp_ok, 'total': total
    }
    with open(log_dir / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\nIter 004: Gen={gen_ok}/{total}, Compile={comp_ok}/{total}, FPC={comp_ok/max(total,1):.3f}")

if __name__ == "__main__":
    main()
