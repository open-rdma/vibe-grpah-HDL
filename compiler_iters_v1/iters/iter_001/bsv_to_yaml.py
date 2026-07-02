#!/usr/bin/env python3
"""
Convert BSV source files to YAML representation.
This creates the initial YAML baseline for Iteration 001.

Strategy: Parse BSV files, extract structure, produce YAML.
The YAML is intentionally detailed for Iteration 001 (baseline),
and will be progressively abstracted in later iterations.
"""

import os
import re
import yaml
from pathlib import Path

BLUE_RDMA_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
BLUE_RDMA_TEST = "/data/mmh/vibe-grpah-HDL/blue-rdma/test"

def read_bsv(filepath):
    with open(filepath) as f:
        return f.read()

def parse_typedefs(content):
    """Extract typedef statements from BSV code."""
    typedefs = []
    # Match typedef <value> <name>; and typedef <type_expr> <name>;
    pattern = r'typedef\s+(.+?)\s+(\w+)\s*;'
    for match in re.finditer(pattern, content):
        value = match.group(1).strip()
        name = match.group(2).strip()
        # Filter out complex typedefs (enum, struct handled separately)
        if not value.startswith('enum') and not value.startswith('struct'):
            typedefs.append({
                'name': name,
                'bsv_equivalent': f'typedef {value} {name};',
                'value': value
            })
    return typedefs

def parse_enums(content):
    """Extract enum definitions."""
    enums = []
    # Match typedef enum { ... } EnumName deriving(...);
    pattern = r'typedef\s+enum\s*\{(.*?)\}\s*(\w+)\s*deriving\s*\(([^)]+)\)\s*;'
    for match in re.finditer(pattern, content, re.DOTALL):
        body = match.group(1).strip()
        name = match.group(2).strip()
        deriving = match.group(3).strip()

        variants = []
        for line in body.split('\n'):
            line = line.strip().rstrip(',')
            if '=' in line:
                parts = line.split('=')
                var_name = parts[0].strip()
                var_val = parts[1].strip().rstrip(',')
                variants.append(f"{var_name} = {var_val}")
            elif line and not line.startswith('//'):
                variants.append(line)

        enums.append({
            'name': name,
            'deriving': deriving,
            'variants': variants,
            'bsv_equivalent': f'typedef enum {{\n    {chr(10).join("    "+v for v in variants)}\n}} {name} deriving({deriving});'
        })
    return enums

def parse_structs(content):
    """Extract struct definitions."""
    structs = []
    pattern = r'typedef\s+struct\s*\{(.*?)\}\s*(\w+)\s*deriving\s*\(([^)]+)\)\s*;'
    for match in re.finditer(pattern, content, re.DOTALL):
        body = match.group(1).strip()
        name = match.group(2).strip()
        deriving = match.group(3).strip()

        fields = []
        for line in body.split('\n'):
            line = line.strip()
            if not line or line.startswith('//'):
                continue
            # Match: Type fieldName; or ReservedZero#(n) fieldName;
            fmatch = re.match(r'((?:ReservedZero#\(\d+\)|Bit#\(\d+\)|\w+(?:#\(\w+(?:,\s*\w+)*\))?)\s+)(\w+)\s*;', line)
            if fmatch:
                fields.append({
                    'type': fmatch.group(1).strip(),
                    'name': fmatch.group(2).strip()
                })
            else:
                # Try simpler pattern
                smatch = re.match(r'(\S+)\s+(\w+)\s*;', line)
                if smatch:
                    fields.append({
                        'type': smatch.group(1).strip(),
                        'name': smatch.group(2).strip()
                    })

        if fields:
            structs.append({
                'name': name,
                'deriving': deriving,
                'fields': fields
            })
    return structs

def parse_functions(content):
    """Extract function definitions."""
    functions = []
    # Match function Type name(args) provisos(...); ... endfunction
    # We need to find function blocks
    lines = content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('function '):
            # Collect the full function block
            func_lines = [lines[i]]
            brace_count = 0
            i += 1
            while i < len(lines):
                func_lines.append(lines[i])
                line_stripped = lines[i].strip()
                brace_count += line_stripped.count('(') - line_stripped.count(')')
                if 'endfunction' in line_stripped:
                    break
                i += 1

            func_text = '\n'.join(func_lines)
            # Extract function signature
            sig_match = re.match(r'function\s+(\S+)\s+(\w+)\s*\(([^)]*)\)', func_lines[0])
            if sig_match:
                functions.append({
                    'name': sig_match.group(2),
                    'return_type': sig_match.group(1),
                    'args': sig_match.group(3).strip(),
                    'bsv_equivalent': func_text
                })
            else:
                functions.append({
                    'name': 'unknown',
                    'bsv_equivalent': func_text
                })
        i += 1
    return functions

def generate_yaml_for_module(bsv_path, module_type, test_info=None):
    """Generate YAML for a single BSV module."""
    content = read_bsv(bsv_path)
    module_name = Path(bsv_path).stem

    # Extract the module description (first comment block)
    desc_lines = []
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('//'):
            desc_lines.append(line[2:].strip())
        elif line:
            break
    description = '\n'.join(desc_lines[:5]) if desc_lines else module_name

    # Parse components
    typedefs = parse_typedefs(content)
    enums = parse_enums(content)
    structs = parse_structs(content)
    functions = parse_functions(content)

    # Extract interface
    interface_match = re.search(r'interface\s+(\w+)\s*;', content)
    interface_name = interface_match.group(1) if interface_match else None

    # Extract methods from interface
    methods = []
    if interface_match:
        iface_start = interface_match.start()
        # Find the interface block
        brace_depth = 0
        in_interface = False
        for line in content[interface_match.start():].split('\n'):
            line_stripped = line.strip()
            if 'interface' in line_stripped:
                in_interface = True
                continue
            if in_interface:
                method_match = re.match(r'method\s+(\S+)\s+(\w+)\s*\(([^)]*)\)', line_stripped)
                if method_match:
                    methods.append({
                        'return_type': method_match.group(1),
                        'name': method_match.group(2),
                        'args': method_match.group(3).strip()
                    })
                if 'endinterface' in line_stripped:
                    break

    # Extract module name
    module_match = re.search(r'module\s+(\w+)\s*\(', content)
    bsv_module_name = module_match.group(1) if module_match else None

    # Extract registers
    registers = []
    for match in re.finditer(r'Reg#\((\S+)\)\s+(\w+)\s*(?:\[(\d+)\])?\s*<-\s*mkReg', content):
        registers.append({
            'type': match.group(1),
            'name': match.group(2),
            'array_size': match.group(3)
        })

    # Extract FIFOs
    fifos = []
    for match in re.finditer(r'((?:Special)?FIFOF?#?\(\S+\))\s+(\w+)\s*<-\s*mk\w+FIFO', content):
        fifos.append({
            'type': match.group(1),
            'name': match.group(2)
        })

    # Extract rules
    rules = []
    rule_pattern = r'(?:\(\*\s*([^*]+)\s*\*\)\s*\n\s*)?rule\s+(\w+)'
    for match in re.finditer(rule_pattern, content):
        attr = match.group(1)
        name = match.group(2)
        rules.append({
            'name': name,
            'attribute': attr.strip() if attr else None
        })

    # Extract submodule instantiations
    submodules = []
    for match in re.finditer(r'(\w+(?:#\(\S+\))?)\s+(\w+)\s*<-\s*mk\w+', content):
        sub_type = match.group(1)
        sub_name = match.group(2)
        if sub_name not in ['cntReg', 'incrQ', 'decrQ']:  # Filter obvious register/FIFO names
            if not any(c in sub_type.lower() for c in ['reg', 'fifo', 'mkreg', 'mkfifo']):
                submodules.append({
                    'type': sub_type,
                    'name': sub_name
                })

    # Build the YAML structure
    yaml_data = {
        'meta': {
            'name': module_name,
            'description': description if description else f"BSV module: {module_name}"
        },
        'module_type': module_type,
        'design_knowledge': {
            'description': f"This module defines: {module_name}.",
            'structural_info': f"Original BSV file: {Path(bsv_path).name}",
        }
    }

    if typedefs:
        yaml_data['typedefs'] = typedefs
    if enums:
        yaml_data['enums'] = enums
    if structs:
        yaml_data['structs'] = structs
    if functions:
        yaml_data['functions'] = functions

    if interface_name or bsv_module_name or methods or registers or rules:
        module_def = {}
        if bsv_module_name:
            module_def['name'] = bsv_module_name
        if interface_name:
            module_def['interface_name'] = interface_name
        if methods:
            module_def['methods'] = methods
        yaml_data['module_def'] = module_def

        impl = {}
        if registers:
            impl['registers'] = registers
        if fifos:
            impl['fifos'] = fifos
        if rules:
            impl['rules'] = rules
        if submodules:
            impl['submodules'] = submodules
        if impl:
            yaml_data['implementation'] = impl

    # Add structural_info to design_knowledge
    yaml_data['design_knowledge']['structural_info'] += (
        f"\nContains: {len(typedefs)} typedefs, {len(enums)} enums, "
        f"{len(structs)} structs, {len(functions)} functions, "
        f"{len(methods)} methods, {len(registers)} registers, "
        f"{len(rules)} rules, {len(submodules)} submodules"
    )

    # For test info
    if test_info:
        yaml_data['test_method'] = test_info

    return yaml_data

def main():
    """Generate YAML for all test modules."""
    output_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/yaml")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define test cases
    test_cases = {
        "Settings": {"type": "typedef_only", "bsv": f"{BLUE_RDMA_SRC}/Settings.bsv"},
        "Headers": {"type": "typedef_and_functions", "bsv": f"{BLUE_RDMA_SRC}/Headers.bsv"},
        "PrimUtils": {"type": "typedef_and_functions", "bsv": f"{BLUE_RDMA_SRC}/PrimUtils.bsv"},
        "DataTypes": {"type": "typedef_and_functions", "bsv": f"{BLUE_RDMA_SRC}/DataTypes.bsv"},
        "Utils": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/Utils.bsv"},
        "SpecialFIFOF": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/SpecialFIFOF.bsv"},
        "Arbitration": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/Arbitration.bsv"},
        "WorkCompGen": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/WorkCompGen.bsv"},
        "ExtractAndPrependPipeOut": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/ExtractAndPrependPipeOut.bsv"},
        "DupReadAtomicCache": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/DupReadAtomicCache.bsv"},
        "InputPktHandle": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/InputPktHandle.bsv"},
        "SendQ": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/SendQ.bsv"},
        "ReqGenSQ": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/ReqGenSQ.bsv"},
        "QueuePair": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/QueuePair.bsv"},
        "RetryHandleSQ": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/RetryHandleSQ.bsv"},
        "RespHandleSQ": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/RespHandleSQ.bsv"},
        "PayloadConAndGen": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/PayloadConAndGen.bsv"},
        "PayloadGen": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/PayloadGen.bsv"},
        "ReqHandleRQ": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/ReqHandleRQ.bsv"},
        "MetaData": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/MetaData.bsv"},
        "Controller": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/Controller.bsv"},
        "TransportLayer": {"type": "module", "bsv": f"{BLUE_RDMA_SRC}/TransportLayer.bsv"},
    }

    for name, info in test_cases.items():
        bsv_path = info['bsv']
        if not os.path.exists(bsv_path):
            print(f"SKIP {name}: BSV file not found at {bsv_path}")
            continue

        try:
            yaml_data = generate_yaml_for_module(bsv_path, info['type'])

            # Write YAML file
            output_path = output_dir / f"{name}.yaml"
            with open(output_path, 'w') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            # Report stats
            content = read_bsv(bsv_path)
            bsv_size = len(content)
            yaml_size = output_path.stat().st_size
            print(f"  {name}: BSV={bsv_size}B -> YAML={yaml_size}B (ratio={yaml_size/bsv_size:.2f})")

        except Exception as e:
            print(f"ERROR {name}: {e}")

    # Also create project.yaml and types.yaml
    project_yaml = {
        'meta': {'name': 'RDMA Engine', 'version': '1.0'},
        'target_languages': ['bsv'],
        'knowledge': {
            'bsv': 'This is an RDMA (RoCEv2) hardware engine implementation in Bluespec SystemVerilog.'
        }
    }
    with open(output_dir / "project.yaml", 'w') as f:
        yaml.dump(project_yaml, f, default_flow_style=False)

    print("\nDone! YAML files generated in:", output_dir)

if __name__ == "__main__":
    main()
