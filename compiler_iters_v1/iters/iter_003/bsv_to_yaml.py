#!/usr/bin/env python3
"""
Iteration 003: Automatic BSV-to-YAML structural extractor
Direction: "auto-yaml-from-bsv-extractor"
Strategy: Parse BSV source code to extract module structure (typedefs, functions,
interfaces, modules, rules, methods) and represent as structured YAML.
This is NOT the compiler - it's the pre-processing step that converts BSV to YAML.
The compiler (LLM) then reads the YAML and generates new BSV.
"""

import re
import yaml
import sys
import os

def extract_typedefs(content):
    """Extract typedef statements from BSV content."""
    typedefs = []
    # Match simple typedef: typedef <value> <name>;
    pattern = r'typedef\s+(.+?)\s+(\w+)\s*;'
    for match in re.finditer(pattern, content):
        typedefs.append({
            'id': match.group(2),
            'definition': match.group(1).strip()
        })
    return typedefs

def extract_enums(content):
    """Extract enum definitions."""
    enums = []
    # Match: typedef enum { ... } TypeName deriving(...);
    pattern = r'typedef\s+enum\s*\{([^}]*)\}\s*(\w+)\s*deriving\s*\(([^)]*)\)\s*;'
    for match in re.finditer(pattern, content, re.DOTALL):
        variants = []
        body = match.group(1)
        for var_match in re.finditer(r'(\w+)(?:\s*=\s*([^,\n]+))?', body):
            name = var_match.group(1)
            value = var_match.group(2).strip() if var_match.group(2) else None
            variants.append({'name': name, 'value': value})
        enums.append({
            'id': match.group(2),
            'deriving': [d.strip() for d in match.group(3).split(',')],
            'variants': variants
        })
    return enums

def extract_interfaces(content):
    """Extract interface definitions."""
    interfaces = []
    # Match: interface <Name>#(...)
    pattern = r'interface\s+(\w+(?:#\([^)]*\))?)\s*;((?:\s*//[^\n]*\n|\s*\n)*\s*(?:method|interface|subinterface)\s+[^;]*;)*'
    for match in re.finditer(pattern, content, re.DOTALL):
        name = match.group(1)
        body = match.group(2)
        methods = []
        for m in re.finditer(r'method\s+(.+?)\s+(\w+)\s*\(([^)]*)\)\s*;', body):
            methods.append({
                'return_type': m.group(1).strip(),
                'name': m.group(2),
                'params': m.group(3).strip()
            })
        interfaces.append({'name': name, 'methods': methods})
    return interfaces

def extract_functions(content):
    """Extract function definitions."""
    functions = []
    # Match: function <ret> <name>(<params>); ... endfunction
    pattern = r'function\s+(.+?)\s+(\w+)\s*\(([^)]*)\)\s*;(.*?)endfunction'
    for match in re.finditer(pattern, content, re.DOTALL):
        functions.append({
            'return_type': match.group(1).strip(),
            'name': match.group(2),
            'params': match.group(3).strip(),
            'body': match.group(4).strip()
        })
    return functions

def extract_modules(content):
    """Extract module definitions with their rules and methods."""
    modules = []
    # Match: module <name>#(...)(<ifc>) provisos(...);
    pattern = r'module\s+(\w+)\s*((?:#\([^)]*\))?)\s*\(([^)]*)\)\s*provisos\s*\(([^)]*)\)\s*;(.*?)endmodule'
    for match in re.finditer(pattern, content, re.DOTALL):
        mod_name = match.group(1)
        params = match.group(2).strip()
        ifc_name = match.group(3).strip()
        provisos = match.group(4).strip()
        body = match.group(5)

        # Extract rules
        rules = []
        for rm in re.finditer(r'rule\s+(\w+)(.*?);(.*?)endrule', body, re.DOTALL):
            rules.append({
                'name': rm.group(1),
                'condition': rm.group(2).strip(),
                'body': rm.group(3).strip()
            })

        # Extract sub-module instantiations
        submodules = []
        for sm in re.finditer(r'(\w+(?:#\([^)]*\))?)\s+(\w+)\s*<-\s*(mk\w+(?:#\([^)]*\))?)\s*;', body):
            submodules.append({
                'type': sm.group(1),
                'name': sm.group(2),
                'constructor': sm.group(3)
            })

        # Extract interface methods
        methods = []
        for mm in re.finditer(r'method\s+(.+?)\s+(\w+)\s*\(([^)]*)\)\s*;(.*?)(?=method|endinterface|$)', body, re.DOTALL):
            methods.append({
                'return_type': mm.group(1).strip(),
                'name': mm.group(2),
                'params': mm.group(3).strip(),
                'body': mm.group(4).strip()
            })

        modules.append({
            'name': mod_name,
            'params': params,
            'interface': ifc_name,
            'provisos': provisos,
            'submodules': submodules,
            'rules': rules,
            'methods': methods
        })
    return modules

def bsv_to_yaml(bsv_path, output_path):
    """Convert a BSV file to YAML representation."""
    with open(bsv_path, 'r') as f:
        content = f.read()

    # Remove comments for cleaner parsing
    content_no_block = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    content_clean = re.sub(r'//[^\n]*', '', content_no_block)

    result = {
        'meta': {
            'source_file': os.path.basename(bsv_path),
            'description': f'Auto-extracted from {os.path.basename(bsv_path)}'
        },
        'imports': [],
        'typedefs': extract_typedefs(content_clean),
        'enums': extract_enums(content_clean),
        'interfaces': extract_interfaces(content_clean),
        'functions': extract_functions(content_clean),
        'modules': extract_modules(content_clean)
    }

    # Extract imports
    for m in re.finditer(r'import\s+(\w+)\s*::\s*\*;', content):
        result['imports'].append(m.group(1))

    with open(output_path, 'w') as f:
        yaml.dump(result, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"Extracted YAML -> {output_path}")
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Extract from SpecialFIFOF.bsv by default
        bsv_file = "/data/mmh/vibe-grpah-HDL/blue-rdma/src/SpecialFIFOF.bsv"
    else:
        bsv_file = sys.argv[1]

    output = sys.argv[2] if len(sys.argv) > 2 else "SpecialFIFOF_auto.yaml"
    bsv_to_yaml(bsv_file, output)
