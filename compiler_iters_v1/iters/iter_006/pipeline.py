#!/usr/bin/env python3
"""
Iteration 006 — Minimal L0-L1 Declarative Prompts + Error-Fix Loop

Strategy:
  Prompt size was the dominant failure mode in iter_005 (19/22 timeout).
  This iteration strips prompts to L0-L1 abstraction level:
  - Ultra-compact BSV syntax reference (~200 bytes)
  - Type signatures only (no reference BSV, no implementation hints)
  - Interface contract + 1-2 sentence behavior description
  - Split prompt: types → module
  - 1-round error-fix loop

Direction: minimal_declarative_prompt_l0_l1 (NOT in tried directions)
"""

import os, sys, json, yaml, subprocess, time, re, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
CCB = "ccb"

# Ultra-compact BSV reference — only syntax patterns, ~200 bytes
MICRO_BSV_REF = "BSV: typedef T N; Bit#(W); enum{V1,V2} deriving(Bits,Eq); struct{T f;} deriving(Bits); SizeOf#(T); TDiv#|TExp#|TAdd#|TMul#; import X::*; function T f(args); endfunction; interface I; method T m(args); method Action a(args); endinterface; module mkM(I); endmodule; Reg#(T) r<-mkReg(v); FIFOF#(T) f<-mkFIFOF; rule rName; endrule; $display; pack/unpack"


def call_ccb(prompt, cwd, timeout=90):
    """Call ccb, extract code from stdout or generated file."""
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


def build_types_prompt(yaml_data, module_name):
    """Phase 1: Types only — minimal L0-L1, just names and structure."""
    parts = [MICRO_BSV_REF]

    desc = yaml_data.get('design_knowledge', {}).get('description', '')
    if desc:
        parts.append(f"\nModule: {module_name} — {desc[:150]}")

    typedefs = yaml_data.get('typedefs', [])
    enums = yaml_data.get('enums', [])
    structs = yaml_data.get('structs', [])

    if typedefs:
        parts.append("\nTypedefs:")
        for td in typedefs:
            val = td.get('value', td.get('bsv_equivalent', '?')).replace('typedef ', '').rstrip(';')
            parts.append(f"  typedef {val} {td['name']};")

    if enums:
        parts.append("\nEnums:")
        for enum in enums:
            variants = enum.get('variants', [])
            parts.append(f"  typedef enum {{{', '.join(variants[:20])}}} {enum['name']} deriving({enum.get('deriving', 'Bits,Eq')});")

    if structs:
        parts.append("\nStructs:")
        for s in structs:
            fields = ', '.join(f"{f['type']} {f['name']}" for f in s.get('fields', []))
            parts.append(f"  typedef struct {{{fields}}} {s['name']} deriving({s.get('deriving', 'Bits')});")
            parts.append(f"  typedef SizeOf#({s['name']}) {s['name']}_WIDTH;")
            parts.append(f"  typedef TDiv#({s['name']}_WIDTH, 8) {s['name']}_BYTE_WIDTH;")

    # Imports guess
    parts.append("\nInclude needed imports (FIFOF, SpecialFIFOF, Reserved, etc).")
    parts.append("Output ONLY BSV in ```bsv block. Generate now:")
    return "\n".join(parts)


def build_module_prompt(yaml_data, module_name):
    """Phase 2: Module body — interface contract + L0-L1 behavior only."""
    md = yaml_data.get('module_def', {})
    behavior = yaml_data.get('behavior', {})

    if not md:
        return None

    parts = [MICRO_BSV_REF]

    desc = yaml_data.get('design_knowledge', {}).get('description', '')
    if desc:
        parts.append(f"\nModule: {module_name} — {desc[:200]}")

    if md.get('interface_name'):
        parts.append(f"\nInterface {md['interface_name']}:")
        for m in md.get('methods', []):
            parts.append(f"  method {m.get('return_type','?')} {m.get('name','?')}({m.get('args','')});")

    if behavior.get('description'):
        parts.append(f"\nBehavior: {behavior['description'][:400]}")

    # Minimal implementation hints — only register names, no types or init values
    impl = yaml_data.get('implementation', {})
    regs = impl.get('registers', [])
    rules = impl.get('rules', [])
    if regs or rules:
        parts.append("\nKey elements:")
        for r in regs[:5]:
            parts.append(f"  Register: {r.get('name','?')}")
        for r in rules[:5]:
            parts.append(f"  Rule: {r.get('name','?')}")

    parts.append("\nOutput complete BSV module with FULL implementation (no stubs/TODOs) in ```bsv block. Generate now:")
    return "\n".join(parts)


def fix_errors(module_name, error_text, current_code, log_dir):
    """Feed compilation errors back for fix."""
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
    """Minimal L0-L1 pipeline: types → module → compile → fix → compile."""
    log_dir = Path(log_dir) / name
    log_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = Path(gen_dir)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    t0 = time.time()
    mtype = data.get('module_type', 'module')

    # Phase 1: Types
    prompt_types = build_types_prompt(data, name)
    ok, types_code = call_ccb(prompt_types, log_dir / "types", timeout=90)
    if not ok:
        return {'gen_ok': False, 'compile_ok': False, 'gen_time': time.time()-t0,
                'error': f'types failed: {types_code[:150]}'}

    # Phase 2: Module (skip for typedef_only)
    if mtype != 'typedef_only':
        prompt_mod = build_module_prompt(data, name)
        if prompt_mod:
            ok, mod_code = call_ccb(prompt_mod, log_dir / "module", timeout=90)
            if ok:
                combined = types_code + "\n\n" + mod_code
            else:
                combined = types_code
        else:
            combined = types_code
    else:
        combined = types_code

    # Save
    bsv_path = gen_dir / f"{name}.bsv"
    with open(bsv_path, 'w') as f:
        f.write(combined)

    # Compile + 1 fix round
    comp_ok, err = compile_bsv(bsv_path, build_dir / name)
    fixed = False
    if not comp_ok and err:
        ok_fix, fixed_code = fix_errors(name, err, combined, log_dir / "fix")
        if ok_fix and fixed_code != combined:
            fixed = True
            combined = fixed_code
            with open(bsv_path, 'w') as f:
                f.write(combined)
            comp_ok, err = compile_bsv(bsv_path, build_dir / name)

    result = {
        'gen_ok': True,
        'gen_time': time.time() - t0,
        'compile_ok': comp_ok,
        'bsv_bytes': len(combined),
        'fixed': fixed
    }
    if not comp_ok:
        result['error'] = err[:300] if err else 'unknown'
    return result


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_006")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy YAML from iter_003 (declarative baseline, no reference BSV)
    src = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_003/yaml")
    for yf in src.glob("*.yaml"):
        shutil.copy(yf, yaml_dir / yf.name)

    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    results = {}
    print(f"Processing {len(yaml_files)} modules (L0-L1 minimal, 4 parallel)...")

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
        'iteration': 'iter_006',
        'strategy': 'minimal_declarative_prompt_l0_l1',
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

    with open(log_dir / "summary_iter_006.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Write findings
    findings = {
        'direction': 'minimal_declarative_prompt_l0_l1',
        'fpc': summary['fpc'],
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'key_observation': 'L0-L1 minimal prompts to avoid timeout; no reference BSV; 1-round error fix'
    }
    state_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_dir / "findings.jsonl", 'a') as f:
        f.write(json.dumps(findings) + '\n')

    # Update state files
    progress = {'iteration': 6, 'total_findings': comp_ok, 'status': 'active', 'stale_count': 0,
                'last_fpc': summary['fpc'], 'strategy': 'minimal_declarative_prompt_l0_l1'}
    with open(state_dir / "progress.json", 'w') as f:
        json.dump(progress, f)

    directions = [
        "direct_mechanical_yaml_to_bsv",
        "single_large_prompt_llm_agent",
        "split_prompt_parallel_only",
        "reference_bsv_error_fix_loop",
        "two_agent_blind_review",
        "minimal_declarative_prompt_l0_l1"
    ]
    with open(state_dir / "directions_tried.json", 'w') as f:
        json.dump(directions, f)

    print(f"\nIter 006 (L0-L1 minimal): Gen={gen_ok}/{total}, Compile={comp_ok}/{total}, FPC={comp_ok/max(total,1):.3f}")


if __name__ == "__main__":
    main()
