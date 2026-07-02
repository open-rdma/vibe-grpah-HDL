#!/usr/bin/env python3
"""
Iteration 005 — Two-Agent Pipeline: Generator + Blind Reviewer

Per prompt_v2_compiler_flow.md §5.4:
"启动代码编写Agent,再启动一个审查Agent来独立客观的对代码进行审查,
审查Agent的prompt要与代码生成Agent隔离,仅提供必要的审查背景和审查目标"

Architecture:
  1. Generator Agent: Full YAML knowledge → generate BSV
  2. Blind Reviewer Agent: Interface contract (L2 only) + generated BSV → review
  3. Generator fixes based on reviewer feedback (1 round)

Direction: two_agent_blind_review (NOT in tried directions)
"""

import os, sys, json, yaml, subprocess, time, re, shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BSC = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BLUE_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
CCB = "ccb"

BSV_REF = """BSV reference:
typedef VALUE NAME; | Bit#(W) | enum{V1,V2} deriving(Bits,Eq) | struct{T f;} deriving(Bits)
SizeOf#(T) | TDiv#(a,b) | TExp#(n) | TAdd# | TMul# | valueOf(X)
import Module :: *; | import Reserved :: *; for ReservedZero#(n)
function RTYPE f(ARGS); ... endfunction
interface IFC; method RTYPE m(ARGS); method Action a(ARGS); endinterface
module mkM(IFC); ... endmodule
Reg#(T) r <- mkReg(v); | Reg#(T) r[N] <- mkCReg(N, v)
FIFOF#(T) f <- mkFIFOF; | Vector#(N, T) v <- replicateM(mkReg(0))
Maybe#(T) with tagged Valid v / tagged Invalid
case (expr) matches tagged Valid .v: ... endcase
rule rName; ... endrule with (* fire_when_enabled *) etc.
Bool | Bit#(n) | pack(v) | unpack(b) | $display(...) | $finish(0)
"""

def call_ccb(prompt, cwd, timeout=120):
    """Call ccb, extract code from stdout or generated file. Create CWD."""
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

        # Extract code block
        for m in re.finditer(r'```(?:bsv|bluespec)?\s*\n(.*?)```', output, re.DOTALL):
            code = m.group(1).strip()
            if len(code) > 20:
                return True, code

        # Check generated files
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


def build_generator_prompt(yaml_data, module_name):
    """Generator prompt: full knowledge (L0-L4)."""
    parts = [BSV_REF, f"\n## Task: Generate BSV module `{module_name}`\n"]

    # Module description
    dk = yaml_data.get('design_knowledge', {})
    desc = dk.get('description', yaml_data.get('meta', {}).get('description', ''))
    if desc:
        parts.append(f"**Purpose**: {desc}\n")

    # Type definitions to generate
    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        parts.append("### Type Definitions (generate exactly these)")
        for td in typedefs:
            val = td.get('value', td.get('bsv_equivalent', '?')).replace('typedef ', '').rstrip(';')
            parts.append(f"typedef {val} {td['name']};")

    enums = yaml_data.get('enums', [])
    if enums:
        parts.append("\n### Enums")
        for enum in enums:
            parts.append(f"typedef enum {{")
            for v in enum.get('variants', []):
                parts.append(f"    {v},")
            parts.append(f"}} {enum['name']} deriving({enum.get('deriving', 'Bits,Eq,FShow')});")

    structs = yaml_data.get('structs', [])
    if structs:
        parts.append("\n### Structs (include SizeOf# and TDiv# width typedefs)")
        for s in structs:
            parts.append(f"typedef struct {{")
            for f in s.get('fields', []):
                parts.append(f"    {f['type']} {f['name']};")
            parts.append(f"}} {s['name']} deriving({s.get('deriving', 'Bits,FShow')});")

    # Functions
    funcs = yaml_data.get('functions', [])
    if funcs:
        parts.append("\n### Functions to Implement")
        for func in funcs:
            parts.append(f"\nfunction {func.get('return_type','?')} {func.get('name','?')}({func.get('args','')});")
            desc_f = func.get('description', '')
            if desc_f:
                parts.append(f"  // {desc_f}")

    # Module definition
    md = yaml_data.get('module_def', {})
    if md:
        parts.append(f"\n### Module: {md.get('name', module_name)}")
        if md.get('interface_name'):
            parts.append(f"Interface: {md['interface_name']}")
            for m in md.get('methods', []):
                parts.append(f"  method {m.get('return_type','?')} {m.get('name','?')}({m.get('args','')});")

    # Implementation hints
    behavior = yaml_data.get('behavior', {})
    if behavior.get('description'):
        parts.append(f"\n### Implementation Guidance\n{behavior['description']}")

    impl = yaml_data.get('implementation', {})
    for r in impl.get('registers', []):
        parts.append(f"Register: {r.get('name','?')}: {r.get('type','?')}")
    for r in impl.get('rules', []):
        parts.append(f"Rule: {r.get('name','?')}: {r.get('description','')}")

    # Reference BSV if available (L4)
    ref = yaml_data.get('_reference_bsv', '')
    if ref:
        # Only include key structural elements, limit size
        ref_lines = [l for l in ref.split('\n') if l.strip() and not l.strip().startswith('//')]
        ref_compact = '\n'.join(ref_lines[:60])  # Max ~60 lines
        parts.append(f"\n### Reference Implementation (structure only)\n```bsv\n{ref_compact}\n```")

    parts.append(f"\nGenerate COMPLETE, COMPILABLE BSV in a ```bsv block. No stubs, no TODOs.")
    return "\n".join(parts)


def build_reviewer_prompt(yaml_data, module_name, generated_code):
    """Blind reviewer: only sees interface contract + generated code. NOT implementation hints."""
    parts = [BSV_REF, f"\n## Task: Review BSV module `{module_name}`\n"]

    # Interface contract ONLY (L2) - no behavior hints, no reference BSV
    parts.append("### Required Interface Contract")
    md = yaml_data.get('module_def', {})
    if md and md.get('interface_name'):
        parts.append(f"Interface: {md['interface_name']}")
        for m in md.get('methods', []):
            parts.append(f"  method {m.get('return_type','?')} {m.get('name','?')}({m.get('args','')});")

    # Required types
    typedefs = yaml_data.get('typedefs', [])
    if typedefs:
        parts.append("\n### Required Type Definitions")
        for td in typedefs[:20]:  # Limit
            val = td.get('value', '?').replace('typedef ', '').rstrip(';')
            parts.append(f"typedef {val} {td['name']};")

    enums = yaml_data.get('enums', [])
    if enums:
        parts.append("\n### Required Enums")
        for e in enums[:5]:
            parts.append(f"  {e['name']} with variants: {', '.join(e.get('variants', [])[:10])}")

    # Module purpose (minimal context)
    desc = yaml_data.get('design_knowledge', {}).get('description', '')
    if desc:
        parts.append(f"\n### Module Purpose\n{desc[:300]}")

    # Generated code to review
    parts.append(f"\n## Generated Code to Review\n```bsv\n{generated_code[:4000]}\n```")

    parts.append(f"""
## Review Criteria
Check the generated code against the interface contract above:
1. Are ALL required methods implemented (not stubs/TODOs)?
2. Are ALL typedefs/enums/structs present and correct?
3. Are imports correct and complete?
4. Is the module structure correct (interface/endinterface, module/endmodule)?
5. Are there any syntax errors visible?

Output your review as:
```
REVIEW: PASS|FAIL
ISSUES:
- [issue description]
MISSING:
- [what's missing]
```

If PASS, also output the code in a ```bsv block. If FAIL, list all issues.""")

    return "\n".join(parts)


def build_fix_prompt(yaml_data, module_name, original_code, review_feedback):
    """Generator fix prompt: incorporates reviewer feedback."""
    parts = [BSV_REF, f"\n## Task: Fix BSV module `{module_name}`\n"]

    parts.append(f"### Reviewer Feedback\n{review_feedback[:2000]}")
    parts.append(f"\n### Current Code\n```bsv\n{original_code[:3000]}\n```")

    # Re-include key requirements
    md = yaml_data.get('module_def', {})
    if md and md.get('interface_name'):
        parts.append(f"\n### Required Interface: {md['interface_name']}")
        for m in md.get('methods', []):
            parts.append(f"  method {m.get('return_type','?')} {m.get('name','?')}({m.get('args','')});")

    parts.append(f"\nFix ALL issues. Output COMPLETE corrected BSV in a ```bsv block. No stubs.")
    return "\n".join(parts)


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
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        ok = r.returncode == 0 and "Error:" not in r.stdout
        return ok, (r.stdout + r.stderr)[:2000] if not ok else ""
    except:
        return False, "Exception"


def process_module_two_agent(name, yaml_path, gen_dir, log_dir, build_dir):
    """Two-agent pipeline for one module."""
    log_dir = Path(log_dir) / name
    log_dir.mkdir(parents=True, exist_ok=True)
    gen_dir = Path(gen_dir)

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    t0 = time.time()
    mtype = data.get('module_type', 'module')

    # Phase 1: Generator Agent
    gen_prompt = build_generator_prompt(data, name)
    gen_ok, gen_code = call_ccb(gen_prompt, log_dir / "generator", timeout=120)

    if not gen_ok:
        return {'gen_ok': False, 'compile_ok': False, 'gen_time': time.time()-t0,
                'error': f'Generator failed: {gen_code[:150]}'}

    # Phase 2: Blind Reviewer Agent
    if mtype != 'typedef_only':  # Skip review for typedef-only (no behavior to review)
        rev_prompt = build_reviewer_prompt(data, name, gen_code)
        rev_ok, review = call_ccb(rev_prompt, log_dir / "reviewer", timeout=90)

        review_failed = False
        if rev_ok and 'REVIEW: FAIL' in review:
            review_failed = True
            # Phase 3: Fix based on review
            fix_prompt = build_fix_prompt(data, name, gen_code, review)
            fix_ok, fixed_code = call_ccb(fix_prompt, log_dir / "fixer", timeout=90)
            if fix_ok:
                gen_code = fixed_code
    else:
        review_failed = False

    # Save
    bsv_path = gen_dir / f"{name}.bsv"
    with open(bsv_path, 'w') as f:
        f.write(gen_code)

    # Compile
    comp_ok, err = compile_bsv(bsv_path, build_dir / name)

    result = {
        'gen_ok': True,
        'gen_time': time.time() - t0,
        'compile_ok': comp_ok,
        'bsv_bytes': len(gen_code),
        'reviewed': mtype != 'typedef_only',
        'review_failed': review_failed if mtype != 'typedef_only' else False
    }
    if not comp_ok:
        result['error'] = err[:300]
    return result


def load_reference_bsv(yaml_path, module_name):
    """Inject original BSV as reference (L4 knowledge)."""
    ref_path = Path(BLUE_SRC) / f"{module_name}.bsv"
    if not ref_path.exists():
        return
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
    with open(ref_path) as f:
        data['_reference_bsv'] = f.read()
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def main():
    iter_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_005")
    yaml_dir = iter_dir / "yaml"
    gen_dir = iter_dir / "generated"
    log_dir = iter_dir / "logs"
    build_dir = iter_dir / "build"

    for d in [gen_dir, log_dir, build_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Copy YAML from iter_003 (declarative, no reference BSV pollution)
    src = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_003/yaml")
    for yf in src.glob("*.yaml"):
        shutil.copy(yf, yaml_dir / yf.name)

    # Inject reference BSV as L4 knowledge for foundational modules
    foundational = ['Settings', 'Headers', 'PrimUtils', 'DataTypes', 'Utils', 'SpecialFIFOF']
    for name in foundational:
        yp = yaml_dir / f"{name}.yaml"
        if yp.exists():
            load_reference_bsv(yp, name)

    yaml_files = sorted(yaml_dir.glob("*.yaml"))
    results = {}
    print(f"Processing {len(yaml_files)} modules (two-agent, 4 parallel)...")

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {}
        for yf in yaml_files:
            name = yf.stem
            f = ex.submit(process_module_two_agent, name, str(yf), gen_dir, log_dir, build_dir)
            futures[f] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                r = future.result()
                results[name] = r
                parts = []
                if r.get('gen_ok'): parts.append("GEN")
                if r.get('compile_ok'): parts.append("COMPILE")
                if r.get('reviewed'): parts.append("REVIEWED")
                if r.get('review_failed'): parts.append("FIXED")
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
        'iteration': 'iter_005',
        'strategy': 'two_agent_blind_review',
        'timestamp': datetime.now().isoformat(),
        'fpc': comp_ok / max(total, 1),
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'total': total,
        'per_module': {k: {'compile_ok': v.get('compile_ok', False),
                           'reviewed': v.get('reviewed', False),
                           'review_failed': v.get('review_failed', False),
                           'gen_time': v.get('gen_time', 0)}
                       for k, v in results.items()}
    }

    with open(log_dir / "summary_iter_005.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    # Write findings
    findings = {
        'direction': 'two_agent_blind_review',
        'fpc': summary['fpc'],
        'gen_ok': gen_ok,
        'comp_ok': comp_ok,
        'key_observation': 'Blind reviewer adds second verification layer; generator+reviewer+fix three-phase pipeline'
    }
    state_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/state")
    state_dir.mkdir(parents=True, exist_ok=True)
    with open(state_dir / "findings.jsonl", 'a') as f:
        f.write(json.dumps(findings) + '\n')

    # Update progress
    progress = {'iteration': 5, 'total_findings': comp_ok, 'status': 'active', 'stale_count': 0,
                'last_fpc': summary['fpc'], 'strategy': 'two_agent_blind_review'}
    with open(state_dir / "progress.json", 'w') as f:
        json.dump(progress, f)

    # Update directions tried
    directions = [
        "direct_mechanical_yaml_to_bsv",
        "single_large_prompt_llm_agent",
        "split_prompt_parallel_only",
        "reference_bsv_error_fix_loop",
        "two_agent_blind_review"
    ]
    with open(state_dir / "directions_tried.json", 'w') as f:
        json.dump(directions, f)

    print(f"\nIter 005 (two-agent): Gen={gen_ok}/{total}, Compile={comp_ok}/{total}, FPC={comp_ok/max(total,1):.3f}")

if __name__ == "__main__":
    main()
