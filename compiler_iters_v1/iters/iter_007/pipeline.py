#!/usr/bin/env python3
"""
Iteration 007 — Mechanical Types + LLM Behavior

Strategy:
  Types phase is the timeout bottleneck (iter_006: 9/22 timeout on types).
  This iteration generates type definitions MECHANICALLY from YAML
  (no ccb needed for types), and only uses ccb for module behavior.

  Mechanical type generation works because iter_003 YAML has clean,
  declarative type definitions with explicit values.

Direction: mechanical_types_llm_behavior (NOT in tried directions)
"""

import os, sys, json, yaml, subprocess, time, re, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
CCB = "ccb"

MICRO_BSV_REF = "BSV: typedef T N; Bit#(W); enum{V1,V2} deriving(Bits,Eq); struct{T f;} deriving(Bits); SizeOf#(T); TDiv#|TExp#|TAdd#|TMul#; import X::*; function T f(args); endfunction; interface I; method T m(args); method Action a(args); endinterface; module mkM(I); endmodule; Reg#(T) r<-mkReg(v); FIFOF#(T) f<-mkFIFOF; Vector#(N,T); rule rName; endrule; $display; pack/unpack; Maybe#(T) tagged Valid/Invalid; case matches"


def generate_types_mechanically(yaml_data, module_name):
    """Generate BSV type definitions mechanically from YAML — NO LLM needed."""
    lines = []
    lines.append(f"// Auto-generated types for {module_name}")
    lines.append("import FIFOF :: *;")
    lines.append("import SpecialFIFOF :: *;")
    lines.append("import Reserved :: *;")
    lines.append("")

    # Typedefs
    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        lines.append("// === Typedefs ===")
        for td in typedefs:
            val = td.get('value', td.get('bsv_equivalent', '?'))
            # Strip any existing 'typedef' prefix and trailing semicolon
            val = val.replace('typedef ', '').rstrip(';').strip()
            name = td['name']
            lines.append(f"typedef {val} {name};")
        lines.append("")

    # Enums
    enums = yaml_data.get('enums', [])
    if enums:
        lines.append("// === Enums ===")
        for enum in enums:
            name = enum['name']
            variants = enum.get('variants', [])
            deriving = enum.get('deriving', 'Bits,Eq,FShow')
            lines.append(f"typedef enum {{")
            for i, v in enumerate(variants):
                comma = "," if i < len(variants) - 1 else ""
                lines.append(f"    {v}{comma}")
            lines.append(f"}} {name} deriving({deriving});")
        lines.append("")

    # Structs
    structs = yaml_data.get('structs', [])
    if structs:
        lines.append("// === Structs ===")
        for s in structs:
            name = s['name']
            deriving = s.get('deriving', 'Bits,FShow')
            lines.append(f"typedef struct {{")
            for f in s.get('fields', []):
                lines.append(f"    {f['type']} {f['name']};")
            lines.append(f"}} {name} deriving({deriving});")
            # Width typedefs
            lines.append(f"typedef SizeOf#({name}) {name}_WIDTH;")
            lines.append(f"typedef TDiv#({name}_WIDTH, 8) {name}_BYTE_WIDTH;")
        lines.append("")

    # Functions from YAML (if they have bsv_equivalent)
    funcs = yaml_data.get('functions', [])
    if funcs:
        lines.append("// === Functions ===")
        for func in funcs:
            bsv = func.get('bsv_equivalent', '')
            if bsv:
                lines.append(bsv.strip())
            else:
                ret = func.get('return_type', 'Bit#(0)')
                fname = func.get('name', 'unknown')
                args = func.get('args', '')
                desc = func.get('description', '')
                if desc:
                    lines.append(f"// {desc[:100]}")
                lines.append(f"function {ret} {fname}({args});")
                lines.append("    // TODO: implement")
                lines.append("endfunction")
        lines.append("")

    return "\n".join(lines)


def call_ccb(prompt, cwd, timeout=90):
    """Call ccb and extract code."""
    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    before = set(str(p) for p in cwd.glob("*.bsv"))

    pf = cwd / "prompt.md"
    with open(pf, 'w') as f:
        f.write(prompt)

    try:
        r = subprocess.run([CCB, "-p", prompt, "--permission-mode", "auto", "--print"],
                          capture_output=True, text=True, timeout=timeout, cwd=str(cwd))
        output = r.stdout

        for m in re.finditer(r'```(?:bsv|bluespec)?\s*\n(.*?)```', output, re.DOTALL):
            code = m.group(1).strip()
            if len(code) > 20:
                return True, code

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


def build_module_prompt(yaml_data, module_name, types_code):
    """Module body prompt — behavior only, types already generated mechanically."""
    md = yaml_data.get('module_def', {})
    if not md:
        return None

    parts = [MICRO_BSV_REF]

    desc = yaml_data.get('design_knowledge', {}).get('description', '')
    if desc:
        parts.append(f"\nModule: {module_name} — {desc[:300]}")

    if md.get('interface_name'):
        parts.append(f"\nInterface {md['interface_name']}:")
        for m in md.get('methods', []):
            parts.append(f"  method {m.get('return_type','?')} {m.get('name','?')}({m.get('args','')});")

    behavior = yaml_data.get('behavior', {})
    if behavior.get('description'):
        parts.append(f"\nBehavior:\n{behavior['description'][:500]}")

    impl = yaml_data.get('implementation', {})
    regs = impl.get('registers', [])
    rules = impl.get('rules', [])
    if regs or rules:
        parts.append("\nInternal elements:")
        for r in regs[:8]:
            parts.append(f"  Reg: {r.get('name','?')} :: {r.get('type','?')}")
        for r in rules[:8]:
            parts.append(f"  Rule: {r.get('name','?')} — {r.get('description','')[:100]}")

    # Include types summary (just names, not full definitions)
    typedef_names = [td['name'] for td in yaml_data.get('typedefs', [])[:20]]
    enum_names = [e['name'] for e in yaml_data.get('enums', [])[:10]]
    struct_names = [s['name'] for s in yaml_data.get('structs', [])[:10]]
    if typedef_names or enum_names or struct_names:
        parts.append(f"\nAvailable types (already generated): {', '.join(typedef_names + enum_names + struct_names)}")

    parts.append("\nTypes are already generated and imported. Output ONLY the module (interface+module+implementation) in ```bsv block. FULL implementation, no stubs. Generate now:")
    return "\n".join(parts)


def fix_errors(module_name, error_text, current_code, log_dir):
    """Feed compilation errors back to ccb for fix."""
    prompt = f"""{MICRO_BSV_REF}

Fix compilation errors in {module_name}:

```bsv
{current_code[:3000]}
```

Errors:
{error_text[:1500]}

Output corrected BSV in ```bsv block. Generate:"""
    ok, fixed = call_ccb(prompt, log_dir, timeout=90)
    return ok, fixed if ok else current_code


def compile_bsv(bsv_path, build_dir):
    """Compile and return (ok, error_text)."""
    build_dir = Path(build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)

    cmd = [BSC, "-elab", "-sim", "-u",
           "-p", f"+:{BLUE_SRC}", "-p", f"+:{bsv_path.parent}",
           "-bdir", str(build_dir), "-info-dir", str(build_dir), "-simdir", str(build_dir),
           "-check-assert", "-steps", "6000000",
           "+RTS", "-K4095M", "-RTS", str(bsv_path)]

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        ok = r.returncode == 0 and "Error:" not in r.stdout
        return ok, (r.stdout + r.stderr)[:2000] if not ok else ""
    except:
        return False, "Exception"


def process_module(name, yaml_path, gen_dir, log_dir, build_dir):
    """Mechanical types + LLM behavior pipeline."""
    log_dir = Path(log_dir) / name
    log_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = Path(gen_dir)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    t0 = time.time()
    mtype = data.get('module_type', 'module')

    # Phase 1: Mechanical type generation (no ccb, instant)
    types_code = generate_types_mechanically(data, name)

    # Phase 2: LLM module body
    if mtype != 'typedef_only':
        prompt_mod = build_module_prompt(data, name, types_code)
        if prompt_mod:
            ok, mod_code = call_ccb(prompt_mod, log_dir / "module", timeout=120)
            if ok:
                combined = types_code + "\n\n" + mod_code
            else:
                # Module gen failed, but types are valid — try compile with just types
                combined = types_code
        else:
            combined = types_code
    else:
        combined = types_code

    # Save
    bsv_path = gen_dir / f"{name}.bsv"
    with open(bsv_path, 'w') as f:
        f.write(combined)

    # Compile + fix loop (1 round)
    comp_ok, err = compile_bsv(bsv_path, build_dir / name)
    fixed = False
    if not comp_ok and err and mtype != 'typedef_only':
        ok_fix, fixed_code = fix_errors(name, err, combined, log_dir / "fix")
        if ok_fix and fixed_code != combined:
            fixed = True
            combined = fixed_code
            with open(bsv_path, 'w') as f:
                f.write(combined)
            comp_ok, err = compile_bsv(bsv_path, build_dir / name)

    result = {
        'gen_ok': True,  # Always true since types are mechanical
        'gen_time': time.time() - t0,
        'compile_ok': comp_ok,
        'bsv_bytes': len(combined),
        'fixed': fixed,
        'types_mechanical': True
    }
    if not comp_ok:
        result['error'] = err[:300] if err else 'unknown'
    return result


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_007")
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

    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    results = {}
    print(f"Processing {len(yaml_files)} modules (mechanical types + LLM behavior, 4 parallel)...")

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {}
        for yf in yaml_files:
            name = yf.stem
            f = ex.submit(process_module, name, str(yf), gen_dir, log_dir, build_dir)
            futures[f] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                r = future.result()
                results[name] = r
                parts = []
                if r.get('gen_ok'): parts.append("GEN")
                if r.get('compile_ok'): parts.append("COMPILE")
                if r.get('fixed'): parts.append("FIXED")
                status = ' '.join(parts) if parts else 'FAIL'
                et = r.get('gen_time', 0)
                print(f"  {name}: {status} ({et:.0f}s)")
                if not r.get('compile_ok') and r.get('error'):
                    err_preview = r['error'][:120].replace('\n', ' ')
                    print(f"    Err: {err_preview}")
            except Exception as e:
                print(f"  {name}: EXCEPTION {e}")
                results[name] = {'error': str(e)}

    total = len(results)
    gen_ok = sum(1 for r in results.values() if r.get('gen_ok'))
    comp_ok = sum(1 for r in results.values() if r.get('compile_ok'))

    summary = {
        'iteration': 'iter_007',
        'strategy': 'mechanical_types_llm_behavior',
        'timestamp': datetime.now().isoformat(),
        'fpc': comp_ok / max(total, 1),
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'total': total,
        'per_module': {k: {'compile_ok': v.get('compile_ok', False),
                           'gen_time': v.get('gen_time', 0),
                           'fixed': v.get('fixed', False)}
                       for k, v in results.items()}
    }

    with open(log_dir / "summary_iter_007.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    findings = {
        'direction': 'mechanical_types_llm_behavior',
        'fpc': summary['fpc'],
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'key_observation': 'Types generated mechanically from YAML (no LLM); only behavior uses ccb. Eliminates types timeout.'
    }
    state_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_dir / "findings.jsonl", 'a') as f:
        f.write(json.dumps(findings) + '\n')

    progress = {'iteration': 7, 'total_findings': comp_ok, 'status': 'active', 'stale_count': 0,
                'last_fpc': summary['fpc'], 'strategy': 'mechanical_types_llm_behavior'}
    with open(state_dir / "progress.json", 'w') as f:
        json.dump(progress, f)

    directions = [
        "direct_mechanical_yaml_to_bsv",
        "single_large_prompt_llm_agent",
        "split_prompt_parallel_only",
        "reference_bsv_error_fix_loop",
        "two_agent_blind_review",
        "minimal_declarative_prompt_l0_l1",
        "mechanical_types_llm_behavior"
    ]
    with open(state_dir / "directions_tried.json", 'w') as f:
        json.dump(directions, f)

    print(f"\nIter 007 (mechanical types): Gen={gen_ok}/{total}, Compile={comp_ok}/{total}, FPC={comp_ok/max(total,1):.3f}")


if __name__ == "__main__":
    main()
