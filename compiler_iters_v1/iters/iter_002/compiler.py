#!/usr/bin/env python3
"""
Iteration 002 Compiler - LLM-based (Agent-driven)
Direction: declarative-yaml-llm-compiler
Strategy: Read YAML, construct prompt, the LLM agent (Claude) generates BSV.
The generated BSV is written directly by the agent after reading the YAML spec.

This script serves as the orchestrator: it reads YAML, prepares context,
and validates the generated BSV.
"""

import yaml
import sys
import os
import subprocess
from pathlib import Path

BSC_BIN = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc"
BSC_LIB = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/lib"

def build_prompt(yaml_data):
    """Build a detailed prompt for the LLM to generate BSV code."""
    meta = yaml_data.get('meta', {})
    knowledge = yaml_data.get('knowledge', {}).get('bsv', {})
    functions = yaml_data.get('functions', [])

    prompt_parts = []
    prompt_parts.append(f"Generate Bluespec SystemVerilog (BSV) code for: {meta['name']}")
    prompt_parts.append(f"\nModule purpose: {meta.get('description', '').strip()}")
    prompt_parts.append("")

    imports = knowledge.get('imports', [])
    if imports:
        prompt_parts.append("Required imports:")
        for imp in imports:
            prompt_parts.append(f"  import {imp} :: *;")
        prompt_parts.append("")

    hints = knowledge.get('hints', [])
    if hints:
        prompt_parts.append("Type context:")
        for hint in hints:
            prompt_parts.append(f"  - {hint}")
        prompt_parts.append("")

    for func in functions:
        prompt_parts.append(f"--- Function: {func['name']} ---")
        prompt_parts.append(f"Behavior: {func['description'].strip()}")
        inputs = func.get('inputs', [])
        if inputs:
            prompt_parts.append("Inputs:")
            for inp in inputs:
                d = f" ({inp['description']})" if inp.get('description') else ""
                prompt_parts.append(f"  {inp['name']}: {inp['type']}{d}")
        outputs = func.get('outputs', [])
        if outputs:
            prompt_parts.append("Returns:")
            for out in outputs:
                d = f" ({out['description']})" if out.get('description') else ""
                prompt_parts.append(f"  {out['type']}{d}")
        prompt_parts.append("")

    prompt_parts.append("Output: Write complete BSV file. No module/interface. Only function definitions.")
    return '\n'.join(prompt_parts)


def compile_generated(output_dir, module_name):
    """Try to compile the generated BSV with bsc."""
    bsv_file = os.path.join(output_dir, f"{module_name}.bsv")
    if not os.path.exists(bsv_file):
        return False, "BSV file not found"

    build_dir = os.path.join(output_dir, "build")
    os.makedirs(build_dir, exist_ok=True)

    cmd = [
        BSC_BIN, '-elab', '-sim', '-v',
        '-bdir', build_dir,
        '-info-dir', build_dir,
        '-simdir', build_dir,
        '-p', f'+:{os.path.dirname(output_dir)}',
        '-p', f'+:/data/mmh/vibe-grpah-HDL/blue-rdma/src',
        '-p', f'+:/data/mmh/vibe-grpah-HDL/blue-rdma/test',
        '-show-compiles',
        '-check-assert',
        bsv_file
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, 'PATH': f"{os.path.dirname(BSC_BIN)}:{os.environ['PATH']}"}
        )
        output = result.stdout + result.stderr
        success = result.returncode == 0
        return success, output
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 2:
        print("Usage: compiler.py <yaml_file> [output_dir]")
        # When called without args, print the prompt for the agent
        sys.exit(1)

    yaml_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./generated"

    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Print the prompt for the LLM agent
    prompt = build_prompt(data)
    print("=" * 60)
    print("PROMPT FOR LLM AGENT:")
    print("=" * 60)
    print(prompt)
    print("=" * 60)
    print(f"Write generated BSV to: {os.path.join(output_dir, data['meta']['name'])}.bsv")


if __name__ == "__main__":
    main()
