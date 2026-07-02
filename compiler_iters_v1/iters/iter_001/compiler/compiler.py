#!/usr/bin/env python3
"""
Compiler: YAML (nested graph + NL descriptions) → BSV RTL Code
Uses ccb (Claude Code) as the LLM agent for code generation.

Strategy: Two-Phase
  Phase 1: Generate all type definitions → types.bsv
  Phase 2: Generate module code (bottom-up, leaf→root)
"""

import os
import sys
import json
import yaml
import subprocess
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

BSC_BIN = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin"
BSC = os.path.join(BSC_BIN, "bsc")
CCB = "ccb"

# BSV source directory for includes
BSV_SRC_DIR = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
BSV_TEST_DIR = "/data/mmh/vibe-grpah-HDL/blue-rdma/test"


def log(msg, level="info"):
    ts = datetime.now().isoformat()
    print(f"[{ts}] [{level}] {msg}")


def read_yaml(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(content)


def call_ccb(prompt, workdir, timeout=180):
    """Call ccb (Claude Code) to generate code. Returns stdout."""
    cmd = [
        CCB, "-p", prompt,
        "--output-format", "text",
        "--max-turns", "3",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=workdir, env={**os.environ, "NO_COLOR": "1"}
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", -1
    except FileNotFoundError:
        log("ccb not found, falling back to direct template generation", "warn")
        return "", "CCB_NOT_FOUND", -2


def compile_bsv(bsv_files, top_module, build_dir, timeout=180):
    """Compile BSV files with BSC (elaboration only)."""
    os.makedirs(build_dir, exist_ok=True)

    src_files = " ".join(bsv_files)
    bsc_flags = (
        f"-elab -sim "
        f"-p +:{BSV_SRC_DIR} "
        f"-bdir {build_dir} -info-dir {build_dir} -simdir {build_dir} "
        f"-aggressive-conditions -lift "
        f"-u -show-compiles "
        f"-check-assert -continue-after-errors "
        f"-promote-warnings ALL "
        f"+RTS -K4095M -RTS "
        f"-steps 6000000"
    )

    cmd = f"{BSC} {bsc_flags} -g {top_module} {src_files}"
    log(f"Compiling: {cmd[:200]}...")

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PATH": f"{BSC_BIN}:{os.environ.get('PATH', '')}"}
        )
        errors = []
        warnings = []
        for line in result.stdout.split('\n') + result.stderr.split('\n'):
            if 'Error' in line or 'error' in line:
                errors.append(line)
            elif 'Warning' in line or 'warning' in line:
                warnings.append(line)

        success = len(errors) == 0 and result.returncode == 0
        return {
            "success": success,
            "returncode": result.returncode,
            "errors": errors[-20:],  # last 20 errors
            "warnings": warnings[-20:],
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-1000:]
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "returncode": -1, "errors": ["TIMEOUT"], "stdout": "", "stderr": ""}


def run_simulation(sim_script, timeout=180):
    """Run a BSC simulation script."""
    try:
        result = subprocess.run(
            [sim_script], capture_output=True, text=True, timeout=timeout
        )
        passed = "PASS" in result.stdout or "passed" in result.stdout.lower()
        return {
            "passed": passed,
            "returncode": result.returncode,
            "stdout": result.stdout[-3000:],
            "stderr": result.stderr[-1000:]
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "returncode": -1, "stdout": "", "stderr": "TIMEOUT"}


def link_bsv(build_dir, top_module, timeout=120):
    """Link compiled BSV to executable simulation."""
    bsc_flags = f"-sim -bdir {build_dir} -info-dir {build_dir} -simdir {build_dir} -e {top_module} -o {build_dir}/{top_module}.sh"
    cmd = f"{BSC} {bsc_flags}"

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "PATH": f"{BSC_BIN}:{os.environ.get('PATH', '')}"}
        )
        return result.returncode == 0, f"{build_dir}/{top_module}.sh"
    except subprocess.TimeoutExpired:
        return False, ""


class Compiler:
    """Main compiler that orchestrates YAML→BSV generation."""

    def __init__(self, project_dir, output_dir, iter_dir):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.iter_dir = Path(iter_dir)
        self.project = None
        self.types = {}
        self.modules = {}
        self.generated_files = {}

    def load_project(self, project_yaml_path):
        """Load project configuration."""
        self.project = read_yaml(project_yaml_path)
        log(f"Loaded project: {self.project.get('meta', {}).get('name', 'unknown')}")

    def load_types(self, types_yaml_path):
        """Load type definitions."""
        types_data = read_yaml(types_yaml_path)
        self.types = {t['id']: t for t in types_data.get('types', [])}
        log(f"Loaded {len(self.types)} type definitions")

    def load_module(self, module_yaml_path):
        """Load a module definition."""
        module_data = read_yaml(module_yaml_path)
        name = module_data.get('meta', {}).get('name', 'unknown')
        self.modules[name] = module_data
        return module_data

    def phase1_generate_types(self):
        """Phase 1: Generate type definitions (types.bsv)."""
        log("=== Phase 1: Generating type definitions ===")

        # Build the prompt for type generation
        type_descriptions = []
        for tid, tdef in self.types.items():
            desc = tdef.get('description', tid)
            generics = tdef.get('generics', [])
            props = tdef.get('properties', {})
            type_descriptions.append(f"- {tid}: {desc}")
            if generics:
                type_descriptions.append(f"  Generics: {generics}")

        prompt = f"""You are generating Bluespec SystemVerilog (BSV) type definitions.

Generate ONLY the following type definitions in BSV format. Output ONLY valid BSV code, no markdown, no explanations.

Types to define:
{chr(10).join(type_descriptions)}

Target language: Bluespec SystemVerilog (BSV)
Output: A complete types.bsv file with all typedef, enum, struct definitions.

IMPORTANT:
- Use exact BSV syntax (typedef, enum, struct, Bit#(n), Bool, deriving(Bits,Eq,FShow))
- Include all necessary imports
- For numeric types use the exact values specified
- Use BSV numeric type functions: TAdd#(), TLog#(), TDiv#(), TExp#(), TMul#()
- Output ONLY the BSV code, nothing else."""

        # Write the prompt to a file for ccb
        prompt_file = self.iter_dir / "phase1_prompt.txt"
        write_file(prompt_file, prompt)

        # Call ccb to generate types
        log("Calling ccb for type generation...")
        stdout, stderr, rc = call_ccb(
            f"Read the file {prompt_file} and generate Bluespec SystemVerilog type definitions. "
            f"Write the output to {self.iter_dir}/output/types.bsv. "
            f"Output ONLY valid BSV code.",
            str(self.iter_dir), timeout=180
        )

        if rc == 0 and os.path.exists(f"{self.iter_dir}/output/types.bsv"):
            log("Type generation completed")
            self.generated_files['types.bsv'] = f"{self.iter_dir}/output/types.bsv"
            return True
        else:
            log(f"Type generation failed: rc={rc}", "error")
            # Write a fallback types file
            fallback = self._generate_types_fallback()
            write_file(f"{self.iter_dir}/output/types.bsv", fallback)
            self.generated_files['types.bsv'] = f"{self.iter_dir}/output/types.bsv"
            return False

    def _generate_types_fallback(self):
        """Fallback type generation without LLM."""
        lines = [
            "// Auto-generated type definitions",
            "import Reserved :: *;",
            "import FIFOF :: *;",
            "import PAClib :: *;",
            "import ClientServer :: *;",
            "import GetPut :: *;",
            "import Vector :: *;",
            "import Randomizable :: *;",
            "",
        ]

        for tid, tdef in self.types.items():
            desc = tdef.get('description', '')
            lines.append(f"// {tid}: {desc}")

            if 'bsv' in tdef.get('properties', {}):
                lines.append(tdef['properties']['bsv'])
            elif 'bsv_type' in tdef:
                lines.append(tdef['bsv_type'])
            else:
                # Generate from description
                if 'enum' in desc.lower():
                    lines.append(f"// TODO: enum definition for {tid}")
                elif 'struct' in desc.lower():
                    lines.append(f"// TODO: struct definition for {tid}")
                else:
                    lines.append(f"// TODO: typedef for {tid}")
            lines.append("")

        return "\n".join(lines)

    def phase2_generate_module(self, module_yaml, module_name):
        """Phase 2: Generate module BSV code."""
        log(f"Generating module: {module_name}")

        meta = module_yaml.get('meta', {})
        ports = module_yaml.get('ports', [])
        nodes = module_yaml.get('nodes', [])
        connections = module_yaml.get('connections', [])
        behavior = module_yaml.get('behavior', {})
        knowledge = module_yaml.get('knowledge', {})

        # Build the module prompt
        parts = []

        # Header
        parts.append(f"Module: {module_name}")
        parts.append(f"Description: {meta.get('description', 'No description')}")
        parts.append("")

        # Interfaces and methods
        if behavior:
            interface = behavior.get('interface', {})
            if interface:
                parts.append("Interface:")
                for method_name, method_info in interface.items():
                    if isinstance(method_info, dict):
                        parts.append(f"  {method_name}: {method_info.get('description', '')}")
                    else:
                        parts.append(f"  {method_name}: {method_info}")
                parts.append("")

            methods = behavior.get('methods', [])
            if methods:
                parts.append("Methods:")
                for m in methods:
                    parts.append(f"  {m.get('name', '?')}: {m.get('description', '')}")
                parts.append("")

            rules = behavior.get('rules', [])
            if rules:
                parts.append("Rules:")
                for r in rules:
                    parts.append(f"  {r.get('name', '?')}: {r.get('description', '')}")
                parts.append("")

            state_regs = behavior.get('state_registers', [])
            if state_regs:
                parts.append("State registers:")
                for sr in state_regs:
                    parts.append(f"  {sr.get('name', '?')}: {sr.get('description', '')}")
                parts.append("")

        # Ports
        if ports:
            parts.append("Ports:")
            for p in ports:
                parts.append(f"  {p.get('name', '?')}: {p.get('direction', 'in')} {p.get('type', '?')} - {p.get('description', '')}")
            parts.append("")

        # Sub-modules
        if nodes:
            parts.append("Sub-module instances:")
            for n in nodes:
                parts.append(f"  {n.get('id', '?')}: ref={n.get('ref', '?')}")
            parts.append("")

        # Connections
        if connections:
            parts.append("Connections:")
            for c in connections:
                frm = c.get('from', {})
                to_list = c.get('to', [])
                for to in (to_list if isinstance(to_list, list) else [to_list]):
                    parts.append(f"  {frm.get('node','?')}.{frm.get('port','?')} -> {to.get('node','?')}.{to.get('port','?')}")
            parts.append("")

        # BSV-specific knowledge
        bsv_knowledge = knowledge.get('bsv', {})
        if bsv_knowledge:
            parts.append("BSV-specific knowledge:")
            parts.append(json.dumps(bsv_knowledge, indent=2))
            parts.append("")

        module_prompt = "\n".join(parts)

        full_prompt = f"""You are generating Bluespec SystemVerilog (BSV) module code.

Generate a complete BSV module based on this specification:

{module_prompt}

IMPORTANT:
- Generate ONLY valid BSV code for the module
- Include the interface definition and module implementation
- Import types from types.bsv (located in the same directory)
- Use standard BSV libraries (FIFOF, ClientServer, GetPut, Vector, etc.)
- Output ONLY the BSV code, no markdown, no explanations
- The file should be named {module_name}.bsv"""

        prompt_file = self.iter_dir / f"phase2_{module_name}_prompt.txt"
        write_file(prompt_file, full_prompt)

        stdout, stderr, rc = call_ccb(
            f"Read the file {prompt_file} and generate Bluespec SystemVerilog code for the module. "
            f"Write the output to {self.iter_dir}/output/{module_name}.bsv. "
            f"Output ONLY valid BSV code.",
            str(self.iter_dir), timeout=180
        )

        output_path = f"{self.iter_dir}/output/{module_name}.bsv"
        if rc == 0 and os.path.exists(output_path):
            log(f"Module {module_name} generated successfully")
        else:
            log(f"Module {module_name} generation failed, using template", "warn")
            # Write fallback from explicit BSV knowledge
            fallback = bsv_knowledge.get('code', f"// TODO: {module_name}")
            write_file(output_path, fallback)

        self.generated_files[module_name] = output_path
        return output_path

    def run_test(self, test_file, top_module, timeout=180):
        """Run a single test: compile + simulate."""
        bsv_files = [v for v in self.generated_files.values() if v.endswith('.bsv')]
        bsv_files.append(test_file)

        build_dir = f"{self.iter_dir}/build/{top_module}"
        os.makedirs(build_dir, exist_ok=True)

        # Compile
        comp_result = compile_bsv(bsv_files, top_module, build_dir, timeout)
        if not comp_result['success']:
            return {"compile": comp_result, "link": None, "simulate": None, "passed": False}

        # Link
        link_ok, sim_script = link_bsv(build_dir, top_module, timeout=120)
        if not link_ok:
            return {"compile": comp_result, "link": {"success": False}, "simulate": None, "passed": False}

        # Simulate
        sim_result = run_simulation(sim_script, timeout=timeout)
        return {
            "compile": comp_result,
            "link": {"success": link_ok},
            "simulate": sim_result,
            "passed": sim_result['passed']
        }

    def collect_metrics(self, test_results, original_bsv_files):
        """Collect metrics for the iteration."""
        metrics = {
            "iteration": "iter_001",
            "timestamp": datetime.now().isoformat(),
            "dimension_a": {},
            "dimension_b": {},
            "efficiency": {},
        }

        # B1: First-pass compilation rate
        total_modules = len(test_results)
        fpc_passed = sum(1 for r in test_results.values()
                        if r.get("compile", {}).get("success", False))
        metrics["dimension_b"]["fpc"] = fpc_passed / total_modules if total_modules > 0 else 0

        # B2: Test pass rate
        tpr_passed = sum(1 for r in test_results.values() if r.get("passed", False))
        metrics["dimension_b"]["tpr"] = tpr_passed / total_modules if total_modules > 0 else 0

        # B3: ZFPR - at this point, same as TPR since we only have one set
        metrics["dimension_b"]["zfpr"] = metrics["dimension_b"]["tpr"]

        metrics["per_module"] = {}
        for name, result in test_results.items():
            metrics["per_module"][name] = {
                "compile_success": result.get("compile", {}).get("success", False),
                "test_passed": result.get("passed", False),
                "errors": result.get("compile", {}).get("errors", [])[:5],
            }

        return metrics


def main():
    parser = argparse.ArgumentParser(description="YAML→BSV Compiler")
    parser.add_argument("--iter-dir", required=True, help="Iteration directory")
    parser.add_argument("--project-yaml", help="Project YAML file")
    parser.add_argument("--test", nargs="*", help="Test targets (e.g., T01 T02)")
    parser.add_argument("--parallel", action="store_true", help="Parallel generation")
    args = parser.parse_args()

    iter_dir = Path(args.iter_dir)
    output_dir = iter_dir / "output"
    os.makedirs(output_dir, exist_ok=True)

    compiler = Compiler(
        project_dir=iter_dir / "yamls",
        output_dir=output_dir,
        iter_dir=iter_dir
    )

    # Load project
    if args.project_yaml:
        compiler.load_project(args.project_yaml)

    # Load types
    types_path = iter_dir / "yamls" / "types.yaml"
    if os.path.exists(types_path):
        compiler.load_types(types_path)

    # Load modules
    yamls_dir = iter_dir / "yamls" / "modules"
    if os.path.exists(yamls_dir):
        for yf in sorted(os.listdir(yamls_dir)):
            if yf.endswith('.yaml'):
                compiler.load_module(os.path.join(yamls_dir, yf))

    # Phase 1: Generate types
    compiler.phase1_generate_types()

    # Phase 2: Generate modules
    for name in sorted(compiler.modules.keys()):
        compiler.phase2_generate_module(compiler.modules[name], name)

    # Run tests
    test_results = {}
    if args.test:
        test_targets = args.test
    else:
        test_targets = []

    for test in test_targets:
        test_yaml_path = iter_dir / "yamls" / "tests" / f"{test}.yaml"
        if os.path.exists(test_yaml_path):
            test_data = read_yaml(test_yaml_path)
            test_file = test_data.get('test_file', '')
            top_module = test_data.get('top_module', f'mkTest{test}')
            log(f"Running test: {test} ({top_module})")

            result = compiler.run_test(test_file, top_module)
            test_results[test] = result
        else:
            log(f"Test {test} YAML not found at {test_yaml_path}", "warn")

    # Collect metrics
    metrics = compiler.collect_metrics(test_results, {})
    metrics_path = iter_dir / "metrics.json"
    write_file(metrics_path, json.dumps(metrics, indent=2))
    log(f"Metrics saved to {metrics_path}")

    # Print summary
    log("=== Iteration Summary ===")
    log(f"FPC: {metrics['dimension_b']['fpc']:.2f}")
    log(f"TPR: {metrics['dimension_b']['tpr']:.2f}")
    log(f"ZFPR: {metrics['dimension_b']['zfpr']:.2f}")


if __name__ == "__main__":
    main()
