#!/usr/bin/env python3
"""
Direct YAML-to-BSV converter for Iteration 001 baseline.
This mechanically reconstructs BSV from the YAML fields
to validate that the YAML format captures sufficient information.

In later iterations, this will be replaced by the LLM-based compiler.
"""

import os
import yaml
from pathlib import Path

def yaml_to_bsv(yaml_data):
    """Convert YAML data to BSV source code."""
    lines = []

    module_type = yaml_data.get('module_type', 'module')
    meta = yaml_data.get('meta', {})

    # Header comment
    lines.append(f"// Generated from YAML: {meta.get('name', 'unknown')}")
    lines.append(f"// Module type: {module_type}")
    lines.append("")

    # For typedef_only and typedef_and_functions, we need to handle them differently
    # They don't have module/interface/endmodule, just typedefs and functions

    has_module_wrapper = module_type == 'module'

    # Imports
    dk = yaml_data.get('design_knowledge', {})
    structural = dk.get('structural_info', '')

    # Determine needed imports from structural info
    needed_imports = set()
    import_map = {
        'FIFOF': 'FIFOF',
        'FIFO': 'FIFO',
        'SpecialFIFO': 'FIFOF',
        'Reg': '',
        'CReg': '',
        'Vector': 'Vector',
        'PipeOut': 'FIFOF',
        'CountCF': '',
        'FlagsType': '',
        'Server': 'Server',
        'Client': 'Client',
        'GetPut': '',
        'BRAM': 'BRAM',
        'Reserved': 'Reserved',
        'Ehr': 'EHR',
        'Printf': 'Printf',
        'Assert': 'Assert',
        'Stmt': 'Stmt',
    }

    imports_from_struct = structural
    if yaml_data.get('typedefs'):
        for td in yaml_data['typedefs']:
            imports_from_struct += ' ' + td.get('value', '') + ' ' + td.get('bsv_equivalent', '')

    # Check for known dependencies
    if 'FIFOF' in imports_from_struct or 'FIFO' in imports_from_struct:
        needed_imports.add('FIFOF :: *')
    if 'Vector' in imports_from_struct:
        needed_imports.add('Vector :: *')
    if 'Reserved' in imports_from_struct:
        needed_imports.add('Reserved :: *')
    if 'BRAM' in imports_from_struct or 'BRAMServer' in imports_from_struct:
        needed_imports.add('BRAM :: *')
    if 'PAClib' in imports_from_struct:
        needed_imports.add('PAClib :: *')
    if 'ClientServer' in imports_from_struct:
        needed_imports.add('ClientServer :: *')
    if 'FShow' in imports_from_struct:
        needed_imports.add('FShow :: *')
    if 'Printf' in imports_from_struct:
        needed_imports.add('Printf :: *')
    if 'Assert' in imports_from_struct:
        needed_imports.add('Assert :: *')
    if 'Stmt' in imports_from_struct:
        needed_imports.add('Stmt :: *')
    if 'GetPut' in imports_from_struct:
        needed_imports.add('GetPut :: *')
    if 'Ehr' in imports_from_struct or 'mkCReg' in imports_from_struct:
        needed_imports.add('EHR :: *')

    # Check for references to other modules
    ref_modules = [
        'Settings', 'Headers', 'PrimUtils', 'DataTypes', 'Utils',
        'SpecialFIFOF', 'Arbitration', 'WorkCompGen', 'ExtractAndPrependPipeOut',
        'DupReadAtomicCache', 'InputPktHandle', 'SendQ', 'ReqGenSQ',
        'QueuePair', 'RetryHandleSQ', 'RespHandleSQ', 'PayloadConAndGen',
        'PayloadGen', 'ReqHandleRQ', 'MetaData', 'Controller', 'TransportLayer'
    ]

    module_name = meta.get('name', '')
    for ref_mod in ref_modules:
        if ref_mod == module_name:
            continue
        if ref_mod in imports_from_struct or ref_mod in structural:
            needed_imports.add(f'{ref_mod} :: *')

    # Write imports
    for imp in sorted(needed_imports):
        lines.append(f'import {imp};')

    if needed_imports:
        lines.append("")

    # Generate typedefs
    if yaml_data.get('typedefs'):
        for td in yaml_data['typedefs']:
            bsv = td.get('bsv_equivalent', f"typedef {td.get('value', '?')} {td['name']};")
            lines.append(bsv)
        lines.append("")

    # Generate enums - use variants list, fixing bsv_equivalent formatting
    if yaml_data.get('enums'):
        for enum in yaml_data['enums']:
            name = enum['name']
            deriving = enum.get('deriving', 'Bits, Eq')
            variants = enum.get('variants', [])
            bsv = f"typedef enum {{\n"
            for i, v in enumerate(variants):
                comma = "," if i < len(variants) - 1 else ""
                bsv += f"    {v}{comma}\n"
            bsv += f"}} {name} deriving({deriving});"
            lines.append(bsv)
            lines.append("")

    # Generate structs
    if yaml_data.get('structs'):
        for struct in yaml_data['structs']:
            name = struct['name']
            deriving = struct.get('deriving', 'Bits, Bounded, FShow')
            fields = struct.get('fields', [])
            bsv = f"typedef struct {{\n"
            for fld in fields:
                bsv += f"    {fld['type']} {fld['name']};\n"
            bsv += f"}} {name} deriving({deriving});"
            lines.append(bsv)
            lines.append("")

    # Generate width typedefs for structs
    if yaml_data.get('structs'):
        for struct in yaml_data['structs']:
            name = struct['name']
            lines.append(f"typedef SizeOf#{name} {name}_WIDTH;")
            lines.append(f"typedef TDiv#({name}_WIDTH, 8) {name}_BYTE_WIDTH;")
        lines.append("")

    # For typedef_only modules, stop here
    if module_type == 'typedef_only':
        return '\n'.join(lines)

    # Generate functions
    if yaml_data.get('functions'):
        for func in yaml_data['functions']:
            bsv = func.get('bsv_equivalent', '')
            if bsv:
                lines.append(bsv)
                lines.append("")

    # For typedef_and_functions modules, stop here (if no interface/module)
    if module_type == 'typedef_and_functions':
        md = yaml_data.get('module_def', {})
        impl = yaml_data.get('implementation', {})
        if not md and not impl:
            return '\n'.join(lines)

    # Generate module code
    md = yaml_data.get('module_def', {})
    impl = yaml_data.get('implementation', {})

    if md:
        interface_name = md.get('interface_name', '')
        bsv_module_name = md.get('name', module_name)
        methods = md.get('methods', [])

        if interface_name:
            # Generate interface
            lines.append(f"interface {interface_name};")
            for m in methods:
                return_type = m.get('return_type', 'Action')
                method_name = m.get('name', '')
                args = m.get('args', '')
                if args:
                    lines.append(f"    method {return_type} {method_name}({args});")
                else:
                    lines.append(f"    method {return_type} {method_name};")
            lines.append(f"endinterface")
            lines.append("")

            # Generate module
            lines.append(f"module {bsv_module_name}({interface_name});")

            # Generate state elements
            if impl.get('registers'):
                for reg in impl['registers']:
                    reg_type = reg.get('type', '')
                    reg_name = reg.get('name', '')
                    array_size = reg.get('array_size')
                    if array_size:
                        lines.append(f"    Reg#({reg_type}) {reg_name}[{array_size}] <- mkCReg({array_size}, ?);")
                    else:
                        init_val = reg.get('init', '?')
                        lines.append(f"    Reg#({reg_type}) {reg_name} <- mkReg({init_val});")

            if impl.get('fifos'):
                for fifo in impl['fifos']:
                    f_type = fifo.get('type', '')
                    f_name = fifo.get('name', '')
                    lines.append(f"    {f_type} {f_name} <- mkFIFOF;")

            if impl.get('submodules'):
                for sub in impl['submodules']:
                    s_type = sub.get('type', '')
                    s_name = sub.get('name', '')
                    lines.append(f"    {s_type} {s_name} <- mk{s_type};")

            # Generate rules (as stub rules with comments)
            if impl.get('rules'):
                lines.append("")
                for rule in impl['rules']:
                    r_name = rule.get('name', '')
                    r_attr = rule.get('attribute', '')
                    if r_attr:
                        lines.append(f"    (* {r_attr} *)")
                    lines.append(f"    rule {r_name};")
                    lines.append(f"        // TODO: implement {r_name}")
                    lines.append(f"    endrule")
                    lines.append("")

            # Generate method implementations (stubs)
            lines.append("")
            for m in methods:
                return_type = m.get('return_type', 'Action')
                method_name = m.get('name', '')
                args = m.get('args', '')
                if args:
                    lines.append(f"    method {return_type} {method_name}({args});")
                else:
                    lines.append(f"    method {return_type} {method_name};")
                lines.append(f"        // TODO: implement {method_name}")
                if return_type != 'Action':
                    lines.append(f"        return ?;")
                lines.append(f"    endmethod")
                lines.append("")

            lines.append("endmodule")
        else:
            # No interface - just output what we have as a partial module
            lines.append(f"// Module stub for {bsv_module_name}")
            lines.append("// Interface and full implementation not captured in YAML")

    return '\n'.join(lines)


def main():
    yaml_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/yaml")
    output_dir = Path("/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    for yf in sorted(yaml_dir.glob("*.yaml")):
        if yf.name in ('project.yaml', 'types.yaml'):
            continue

        name = yf.stem
        try:
            with open(yf) as f:
                yaml_data = yaml.safe_load(f)

            bsv_code = yaml_to_bsv(yaml_data)

            output_path = output_dir / f"{name}.bsv"
            with open(output_path, 'w') as f:
                f.write(bsv_code)

            yaml_size = yf.stat().st_size
            bsv_size = len(bsv_code)
            ratio = bsv_size / max(yaml_size, 1)
            lines_count = bsv_code.count('\n')

            # Check if the generated BSV has actual content (not just stubs)
            has_stubs = '// TODO:' in bsv_code
            has_real_content = any(
                kw in bsv_code for kw in ['typedef', 'struct', 'enum', 'function', 'endfunction', 'rule']
            )

            results[name] = {
                'yaml_bytes': yaml_size,
                'bsv_bytes': bsv_size,
                'bsv_lines': lines_count,
                'ratio': ratio,
                'has_stubs': has_stubs,
                'has_real_content': has_real_content,
            }

            status = "OK" if has_real_content else "STUBS_ONLY"
            if has_stubs:
                status += "+STUBS"
            print(f"  {name}: {status} YAML={yaml_size}B -> BSV={bsv_size}B (ratio={ratio:.2f}, {lines_count} lines)")

        except Exception as e:
            print(f"ERROR {name}: {e}")
            results[name] = {'error': str(e)}

    # Write results summary
    import json
    with open(output_dir / "generation_results.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Stats
    total = len(results)
    ok_count = sum(1 for r in results.values() if r.get('has_real_content'))
    print(f"\nSummary: {ok_count}/{total} modules generated with real content")

if __name__ == "__main__":
    main()
