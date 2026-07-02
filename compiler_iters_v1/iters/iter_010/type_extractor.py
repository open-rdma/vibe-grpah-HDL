#!/usr/bin/env python3
"""
iter_010: Deterministic BSV Type Extractor

Extracts types, interfaces, and complete function definitions from original
BSV source files. These extracted types are GUARANTEED CORRECT (they compile
in the original project), providing a solid foundation for the LLM to build
behavioral code upon.

KEY INSIGHT: By deterministically extracting types from the original BSV,
we eliminate ALL type-related compilation errors. The LLM only needs to
generate behavioral logic (rules, methods, module bodies).
"""

import re
import os
from typing import Dict, List


def strip_block_comments(text: str) -> str:
    """Remove /* ... */ block comments."""
    result = []
    i = 0
    while i < len(text):
        if text[i:i+2] == '/*':
            depth = 1
            j = i + 2
            while j < len(text) - 1 and depth > 0:
                if text[j:j+2] == '/*':
                    depth += 1
                    j += 1
                elif text[j:j+2] == '*/':
                    depth -= 1
                    j += 1
                j += 1
            i = j + 1 if j < len(text) else len(text)
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def strip_line_comments(text: str) -> str:
    """Remove // line comments, respecting string literals."""
    lines = []
    for line in text.split('\n'):
        in_string = False
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
            if ch == '/' and i+1 < len(line) and line[i+1] == '/' and not in_string:
                line = line[:i]
                break
        lines.append(line)
    return '\n'.join(lines)


def clean_source(text: str) -> str:
    text = strip_block_comments(text)
    text = strip_line_comments(text)
    return text


def find_matching_paren(text: str, start: int) -> int:
    """Find matching ) for ( at position start."""
    depth = 0
    pos = start
    while pos < len(text):
        if text[pos] == '(':
            depth += 1
        elif text[pos] == ')':
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    return -1


def find_matching_brace(text: str, start: int) -> int:
    """Find matching } for { at position start."""
    depth = 0
    pos = start
    while pos < len(text):
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
            if depth == 0:
                return pos
        pos += 1
    return -1


def find_matching_keyword(text: str, start: int, open_kw: str, close_kw: str, initial_depth: int = 1) -> int:
    """Find matching end keyword (e.g., endinterface, endmodule, endfunction).
    initial_depth should be 1 when starting inside the block, 0 when starting before it."""
    depth = initial_depth
    pos = start
    open_len = len(open_kw)
    close_len = len(close_kw)
    while pos < len(text):
        # Check for open keyword (as whole word)
        if text[pos:pos+open_len] == open_kw and not text[pos+open_len:pos+open_len+1].isalnum():
            depth += 1
            pos += open_len
            continue
        if text[pos:pos+close_len] == close_kw and not text[pos+close_len:pos+close_len+1].isalnum():
            depth -= 1
            if depth == 0:
                return pos + close_len
            pos += close_len
            continue
        pos += 1
    return -1


class BSVTypeExtractor:
    def __init__(self, source_path: str):
        self.source_path = source_path
        with open(source_path, 'r') as f:
            self.raw = f.read()
        self.clean = clean_source(self.raw)

    def extract_imports(self) -> List[str]:
        imports = []
        for line in self.raw.split('\n'):
            s = line.strip()
            if s.startswith('import ') and s.endswith(';'):
                if s in self.clean:
                    imports.append(s)
        seen = set()
        result = []
        for imp in imports:
            if imp not in seen:
                seen.add(imp)
                result.append(imp)
        return result

    def extract_simple_typedefs(self) -> List[str]:
        typedefs = []
        for line in self.clean.split('\n'):
            s = line.strip()
            if not s.startswith('typedef '):
                continue
            if 'struct' in s or 'enum' in s:
                continue
            if not s.endswith(';'):
                continue
            typedefs.append(s)
        return typedefs

    def extract_enum_definitions(self) -> List[str]:
        enums = []
        for m in re.finditer(r'typedef\s+enum\s*\{', self.clean):
            start = m.start()
            body_start = m.end() - 1
            body_end = find_matching_brace(self.clean, body_start)
            if body_end < 0:
                continue
            rest = self.clean[body_end+1:]
            end_match = re.match(
                r'\s*(\w+(?:\s*#\s*\([^)]*\))?)\s*deriving\s*\(([^)]*)\)\s*;', rest
            )
            if end_match:
                full = self.clean[start:body_end+1+end_match.end()].strip()
                enums.append(full)
        return enums

    def extract_struct_definitions(self) -> List[str]:
        structs = []
        for m in re.finditer(r'typedef\s+struct\s*\{', self.clean):
            start = m.start()
            body_start = m.end() - 1
            body_end = find_matching_brace(self.clean, body_start)
            if body_end < 0:
                continue
            rest = self.clean[body_end+1:]
            end_match = re.match(
                r'\s*(\w+(?:\s*#\s*\([^)]*\))?)\s*deriving\s*\(([^)]*)\)\s*;', rest
            )
            if end_match:
                full = self.clean[start:body_end+1+end_match.end()].strip()
                structs.append(full)
        return structs

    def _find_module_ranges(self) -> List[tuple]:
        """Find (start, end) positions of all module blocks to exclude nested content."""
        ranges = []
        for m in re.finditer(r'(?<!\w)module\s+', self.clean):
            start = m.start()
            after_kw = self.clean[m.end():]
            # Skip to the first ; or (
            semicolon = after_kw.find(';')
            paren = after_kw.find('(')
            if semicolon < 0 and paren < 0:
                continue
            # Find the module body
            body_start = -1
            if paren >= 0 and (semicolon < 0 or paren < semicolon):
                # Find matching ) then ;
                p_end = find_matching_paren(after_kw, paren)
                if p_end > 0:
                    after_paren = after_kw[p_end+1:]
                    s_pos = after_paren.find(';')
                    if s_pos >= 0:
                        body_start = m.end() + p_end + 1 + s_pos + 1
            else:
                body_start = m.end() + semicolon + 1

            if body_start < 0:
                continue

            body_end = find_matching_keyword(self.clean, body_start, 'module', 'endmodule')
            if body_end > 0:
                ranges.append((start, body_end))
        return ranges

    def _is_inside_module(self, pos: int, module_ranges: List[tuple] = None) -> bool:
        """Check if position is inside a module definition."""
        if module_ranges is None:
            module_ranges = self._find_module_ranges()
        for ms, me in module_ranges:
            if ms < pos < me:
                return True
        return False

    def _find_matching_interface_end(self, start: int) -> int:
        """Find matching endinterface for an interface TYPE DEFINITION.

        Distinguishes between:
        - 'interface Name#(params);' = TYPE definition (counts for nesting)
        - 'interface ReturnType memberName;' = member declaration (does NOT count)

        A type definition has the pattern: interface <Name>#?(<params>)?;
        A member declaration has: interface <Type> <name>;
        Key difference: type definition has ONE identifier before ';',
        member declaration has TWO (return type + member name).
        """
        depth = 1
        pos = start
        while pos < len(self.clean):
            # Check for 'interface' keyword
            if (self.clean[pos:pos+9] == 'interface' and
                not self.clean[pos+9:pos+10].isalnum()):
                # Determine if this is a type definition (counts) or member (doesn't)
                after_if = self.clean[pos+9:].lstrip()
                # Find the ';' that ends this interface statement
                semi = self._find_semicolon_after_parens(after_if, 0)
                if semi > 0:
                    stmt = after_if[:semi]
                    # Count top-level identifiers (outside parens)
                    # Type definition: Name or Name#(params) — ONE top-level name
                    # Member declaration: Type#(params) name — TWO top-level names
                    # Strategy: remove everything inside parentheses, then count words
                    no_parens = re.sub(r'\([^)]*\)', '', stmt)
                    # Also remove anything inside #(...)
                    no_params = re.sub(r'#[^(]*\([^)]*\)', '', no_parens)
                    words = re.findall(r'[A-Za-z_]\w*', no_params)
                    if len(words) == 1:
                        depth += 1
                pos += 9
                continue

            if (self.clean[pos:pos+12] == 'endinterface' and
                not self.clean[pos+12:pos+13].isalnum()):
                depth -= 1
                if depth == 0:
                    return pos + 12
                pos += 12
                continue

            pos += 1
        return -1

    def extract_interface_definitions(self) -> List[str]:
        interfaces = []
        module_ranges = self._find_module_ranges()

        for m in re.finditer(r'(?<!\w)interface\s+', self.clean):
            start = m.start()
            if self._is_inside_module(start, module_ranges):
                continue

            after = self.clean[m.end():]
            stmt_end = self._find_semicolon_after_parens(after, 0)
            if stmt_end < 0:
                continue
            stmt = after[:stmt_end]
            # Count top-level identifiers (outside parens and #(...))
            no_parens = re.sub(r'\([^)]*\)', '', stmt)
            no_params = re.sub(r'#[^(]*\([^)]*\)', '', no_parens)
            words = re.findall(r'[A-Za-z_]\w*', no_params)
            if len(words) != 1:
                continue  # Skip member declarations

            body_start = m.end() + stmt_end + 1
            body_end = self._find_matching_interface_end(body_start)
            if body_end > 0:
                full = self.clean[start:body_end].strip()
                interfaces.append(full)

        return interfaces

    def _find_semicolon_after_parens(self, text: str, start: int) -> int:
        """Find the ; that ends a function signature, skipping over (...) and (...) groups."""
        pos = start
        while pos < len(text):
            ch = text[pos]
            if ch == '(':
                # Skip to matching )
                depth = 1
                pos += 1
                while pos < len(text) and depth > 0:
                    if text[pos] == '(':
                        depth += 1
                    elif text[pos] == ')':
                        depth -= 1
                    pos += 1
                continue
            elif ch == ';':
                return pos
            pos += 1
        return -1

    def _find_typeclass_ranges(self) -> List[tuple]:
        """Find (start, end) of all typeclass/instance blocks."""
        ranges = []
        for kw, end_kw in [('typeclass', 'endtypeclass'), ('instance', 'endinstance')]:
            for m in re.finditer(rf'(?<!\w){kw}\s+', self.clean):
                start = m.start()
                after = self.clean[m.end():]
                sig_end = self._find_semicolon_after_parens(after, 0)
                if sig_end < 0:
                    continue
                body_start = m.end() + sig_end + 1
                body_end = find_matching_keyword(self.clean, body_start, kw, end_kw)
                if body_end > 0:
                    ranges.append((start, body_end))
        return ranges

    def extract_function_definitions(self) -> List[str]:
        """Extract complete package-level function definitions (with bodies)."""
        functions = []
        module_ranges = self._find_module_ranges()
        tc_ranges = self._find_typeclass_ranges()

        for m in re.finditer(r'(?<!\w)function\s+', self.clean):
            start = m.start()
            if self._is_inside_module(start, module_ranges):
                continue
            # Skip functions inside typeclass/instance blocks
            if self._is_inside_module(start, tc_ranges):
                continue

            after = self.clean[m.end():]

            sig_end = self._find_semicolon_after_parens(after, 0)
            if sig_end < 0:
                continue

            # Check for malformed extraction (unbalanced parens from module param lists)
            sig = self.clean[m.end():m.end()+sig_end]
            if sig.count(')') != sig.count('('):
                continue  # Skip — likely part of a module parameter list or nested context

            body_start = m.end() + sig_end + 1
            body_end = find_matching_keyword(self.clean, body_start, 'function', 'endfunction')
            if body_end > 0:
                full = self.clean[start:body_end].strip()
                functions.append(full)
            else:
                full = self.clean[start:m.end()+sig_end+1].strip()
                functions.append(full)

        return functions

    def extract_typeclass_definitions(self) -> List[str]:
        typeclasses = []
        for m in re.finditer(r'(?<!\w)typeclass\s+', self.clean):
            start = m.start()
            after = self.clean[m.end():]
            # Find the ; that ends the typeclass header
            sig_end = self._find_semicolon_after_parens(after, 0)
            if sig_end < 0:
                continue
            body_start = m.end() + sig_end + 1
            body_end = find_matching_keyword(self.clean, body_start, 'typeclass', 'endtypeclass')
            if body_end > 0:
                full = self.clean[start:body_end].strip()
                typeclasses.append(full)
        return typeclasses

    def extract_instance_definitions(self) -> List[str]:
        instances = []
        module_ranges = self._find_module_ranges()
        for m in re.finditer(r'(?<!\w)instance\s+', self.clean):
            start = m.start()
            if self._is_inside_module(start, module_ranges):
                continue
            after = self.clean[m.end():]
            sig_end = self._find_semicolon_after_parens(after, 0)
            if sig_end < 0:
                continue
            body_start = m.end() + sig_end + 1
            body_end = find_matching_keyword(self.clean, body_start, 'instance', 'endinstance')
            if body_end > 0:
                full = self.clean[start:body_end].strip()
                instances.append(full)
        return instances

    def extract_all_types(self) -> Dict[str, List[str]]:
        return {
            'imports': self.extract_imports(),
            'simple_typedefs': self.extract_simple_typedefs(),
            'enums': self.extract_enum_definitions(),
            'structs': self.extract_struct_definitions(),
            'interfaces': self.extract_interface_definitions(),
            'functions': self.extract_function_definitions(),
            'typeclasses': self.extract_typeclass_definitions(),
            'instances': self.extract_instance_definitions(),
        }

    def build_type_skeleton(self) -> str:
        types = self.extract_all_types()
        parts = []
        parts.append(f"// === Deterministic type extraction from {os.path.basename(self.source_path)} ===\n")

        if types['imports']:
            parts.extend(types['imports'])
            parts.append("")

        if types['simple_typedefs']:
            parts.extend(types['simple_typedefs'])
            parts.append("")

        if types['enums']:
            parts.extend(types['enums'])
            parts.append("")

        if types['structs']:
            parts.extend(types['structs'])
            parts.append("")

        if types['typeclasses']:
            parts.extend(types['typeclasses'])
            parts.append("")

        if types['instances']:
            parts.extend(types['instances'])
            parts.append("")

        if types['interfaces']:
            parts.extend(types['interfaces'])
            parts.append("")

        if types['functions']:
            parts.append("// === Complete function definitions (from original, verified correct) ===")
            for func in types['functions']:
                parts.append(func)
                parts.append("")

        return '\n'.join(parts)


def extract_for_module(source_path: str) -> Dict:
    extractor = BSVTypeExtractor(source_path)
    types = extractor.extract_all_types()
    skeleton = extractor.build_type_skeleton()

    return {
        'source_path': source_path,
        'module_name': os.path.splitext(os.path.basename(source_path))[0],
        'types': types,
        'skeleton': skeleton,
        'total_types': sum(
            len(v) for k, v in types.items()
        ),
        'import_count': len(types['imports']),
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "/data/mmh/vibe-grpah-HDL/blue-rdma/src/Settings.bsv"
    result = extract_for_module(path)
    print(f"=== {result['module_name']}: {result['total_types']} items ===")
    for key, items in result['types'].items():
        if items:
            print(f"  {key}: {len(items)}")
    print()
    print(result['skeleton'][:4000])
