#!/usr/bin/env python3
"""Improved multi-level knowledge merge script for nested_v2.

Key improvements over nested_v1:
  - LAYER 0: Shared language template (templates/bluespec_sv/template.md)
  - LAYER 1: Project-specific knowledge only (not language-generic BSV syntax)
  - LAYER 2-3: Module interface + behavioral knowledge + declared signals
  - LAYER 4: Child INTERFACE CONTRACT only (no implementation knowledge)
  - LAYER 5: Connection computation descriptions with transforms
  - LAYER 6: Derived proviso closure (child provisos with param substitution)
  - LAYER 7: Import guidance (decision table, use-only-what-you-need)

Output: merged knowledge as plain text for injection into a fresh claude session.
"""

import yaml
import sys
import os
import re
from pathlib import Path


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_text(path):
    if not os.path.exists(path):
        return ""
    with open(path) as f:
        return f.read()


def find_project_root(yaml_path):
    """Walk upward from yaml_path to find the directory with project.yaml."""
    p = Path(yaml_path).resolve().parent
    while p != p.root:
        if (p / "project.yaml").exists():
            return str(p)
        p = p.parent
    raise FileNotFoundError(f"Cannot find project.yaml above {yaml_path}")


def find_language_template(project_root):
    """Find the shared language template directory."""
    # Look for templates directory relative to project root siblings
    # First check if project.yaml specifies a language_template path
    project_yaml = load_yaml(os.path.join(project_root, "project.yaml"))
    lang_template = project_yaml.get("properties", {}).get("language_template", "")
    if lang_template:
        template_path = os.path.join(project_root, lang_template)
        if os.path.exists(template_path):
            return os.path.dirname(template_path)

    # Fallback: search for templates/<target>/template.md
    target = project_yaml.get("properties", {}).get("target", "bluespec_sv")
    candidates = [
        os.path.join(project_root, "templates", target),
        # Walk up to find shared templates
        os.path.join(Path(project_root).parent, "templates", target),
    ]
    for cand in candidates:
        if os.path.exists(os.path.join(cand, "template.md")):
            return cand
    return None


def resolve_child_path(project_root, ref_path):
    """Resolve a relative ref path from project root."""
    return os.path.join(project_root, ref_path)


def substitute_proviso(proviso_str, param_bindings):
    """Substitute parameter names in a proviso string with their concrete values.

    Args:
        proviso_str: e.g. "Add#(1, _, reqNum)"
        param_bindings: dict mapping param name to value, e.g. {"reqNum": "TDiv#(reqNum, 2)"}

    Returns:
        Substituted proviso string, or None if param not found in bindings.
    """
    result = proviso_str
    for param, value in param_bindings.items():
        result = result.replace(param, value)
    return result


def should_skip_proviso(proviso_str):
    """Check if a proviso should be skipped when deriving for parent.

    NumAlias entries are LOCAL convenience aliases for the child module.
    The parent doesn't need them — the non-NumAlias provisos carry the
    full type constraints. Propagating NumAlias causes naming collisions
    when multiple children alias to the same convenience name.
    """
    return "NumAlias" in proviso_str


def compute_child_derived_provisos(child_yaml, param_bindings):
    """Compute the provisos the PARENT needs when instantiating a child.

    Takes the child's provisos, substitutes the parent's type parameters,
    filters out NumAlias (local aliases), and returns the list.
    """
    child_provisos = child_yaml.get("provisos", [])
    derived = []
    for p in child_provisos:
        if should_skip_proviso(p):
            continue  # NumAlias are local to child, skip to avoid naming collisions
        substituted = substitute_proviso(p, param_bindings)
        if substituted:
            derived.append(substituted)
    return derived


def extract_computation_provisos(connections, signals):
    """Analyze connection transforms to detect bit-manipulation provisos needed.

    Returns a set of proviso patterns that the parent needs.
    """
    provisos = set()

    # Patterns to detect from transforms and signal types
    for conn in connections:
        transform = conn.get("transform", "")
        if not transform:
            continue

        t = transform.lower()
        if "truncate" in t or "truncatelsb" in t:
            # truncate/extract implies Add#(result_sz, _, source_sz)
            # We can't always determine sizes from strings, so check signals
            pass
        if "zeroextend" in t:
            # zeroExtend implies Add#(source_sz, _, target_sz)
            pass

    return sorted(provisos)


def is_external_port(port):
    """Check if a port is an external interface port (not internal state)."""
    return port.get("category", "data") == "data"


def merge_knowledge(yaml_path):
    """Merge knowledge for a single module using the improved layered approach."""
    project_root = find_project_root(yaml_path)
    module_yaml = load_yaml(yaml_path)
    meta = module_yaml.get("meta", {})
    module_name = meta.get("name", "unknown")

    lines = []

    # ═══════════════════════════════════════════════════════════════
    # LAYER 0: Shared Language Template
    # ═══════════════════════════════════════════════════════════════
    lang_template_dir = find_language_template(project_root)
    if lang_template_dir:
        template_md = load_text(os.path.join(lang_template_dir, "template.md"))
        if template_md:
            lines.append("=" * 70)
            lines.append("LAYER 0 — BSV LANGUAGE TEMPLATE (Shared Conventions)")
            lines.append("=" * 70)
            lines.append(template_md.strip())

    # ═══════════════════════════════════════════════════════════════
    # LAYER 1: Project-Specific Knowledge
    # ═══════════════════════════════════════════════════════════════
    sk_path = os.path.join(project_root, "system_knowledge.md")
    sk = load_text(sk_path)
    if sk:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LAYER 1 — PROJECT-SPECIFIC KNOWLEDGE")
        lines.append("=" * 70)
        lines.append(sk.strip())

    # ═══════════════════════════════════════════════════════════════
    # LAYER 2: Module Interface
    # ═══════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("LAYER 2 — MODULE INTERFACE")
    lines.append("=" * 70)
    # Convert snake_case to PascalCase: "priority_encoder" → "PriorityEncoder"
    pascal_name = "".join(word.capitalize() for word in module_name.split("_"))
    lines.append(f"Module Name: mk{pascal_name}")
    lines.append(f"Package Name: {pascal_name}")
    lines.append(f"Description: {meta.get('description', '')}")

    lines.append("")
    lines.append("--- External Ports ---")
    for port in module_yaml.get("ports", []):
        if is_external_port(port):
            lines.append(
                f"  {port['name']} | {port['direction']} | {port['type']} | {port.get('description', '')}"
            )

    # Methods
    methods = module_yaml.get("methods", [])
    if methods:
        lines.append("")
        lines.append("--- Method Signatures ---")
        for m in methods:
            args = ", ".join(
                f"{a['type']} {a['name']}" for a in m.get("arguments", [])
            )
            lines.append(f"  method {m['returns']} {m['name']}({args});")
            if m.get("description"):
                lines.append(f"    // {m['description']}")

    # ═══════════════════════════════════════════════════════════════
    # LAYER 3: Module Behavioral Knowledge + Internal Signals
    # ═══════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("LAYER 3 — BEHAVIORAL KNOWLEDGE & INTERNAL SIGNALS")
    lines.append("=" * 70)

    knowledge = meta.get("knowledge", "")
    if knowledge:
        lines.append("")
        lines.append("--- Implementation Algorithm ---")
        lines.append(knowledge.strip())

    # Module's own provisos
    own_provisos = module_yaml.get("provisos", [])
    if own_provisos:
        lines.append("")
        lines.append("--- Module's Required Provisos ---")
        for p in own_provisos:
            lines.append(f"  {p}")

    # Declared signals
    signals = module_yaml.get("signals", [])
    if signals:
        lines.append("")
        lines.append("--- Internal Signals ---")
        for sig in signals:
            init_str = f" init = {sig['init']}" if sig.get("init") else ""
            lines.append(f"  {sig['name']} : {sig['type']}{init_str}")
            if sig.get("description"):
                lines.append(f"    // {sig['description']}")

    # ═══════════════════════════════════════════════════════════════
    # LAYER 4: Child Interfaces (INTERFACE CONTRACT ONLY)
    # ═══════════════════════════════════════════════════════════════
    nodes = module_yaml.get("nodes", [])
    if nodes:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LAYER 4 — CHILD SUBMODULE INTERFACES (Contract Only)")
        lines.append("=" * 70)
        lines.append("NOTE: Only the child's INTERFACE is shown. Implementation details")
        lines.append("are the child module's responsibility. You only need to:")
        lines.append("  - Instantiate the child with the specified parameters")
        lines.append("  - Call the child's methods as described")
        lines.append("  - Add the DERIVED PROVISOS shown below to your module's provisos")

        # Group by (ref, params) since same ref can have different parameterizations
        seen_groups = {}
        for node in nodes:
            ref = node["ref"]
            params_key = str(sorted(node.get("parameters", {}).items()))
            group_key = (ref, params_key)
            if group_key not in seen_groups:
                seen_groups[group_key] = {"nodes": [], "params": node.get("parameters", {})}
            seen_groups[group_key]["nodes"].append(node)

        for (ref, _), group_info in seen_groups.items():
            child_path = resolve_child_path(project_root, ref)
            if not os.path.exists(child_path):
                lines.append(f"\nWARNING: Child YAML not found: {child_path}")
                continue

            child_yaml = load_yaml(child_path)
            child_meta = child_yaml.get("meta", {})
            child_name = child_meta.get("name", "unknown")
            params = group_info["params"]
            node_group = group_info["nodes"]
            instance_ids = [n["id"] for n in node_group]

            lines.append(f"\n### Child: {child_name}")
            lines.append(f"    Local instances: {', '.join(instance_ids)}")
            lines.append(f"    Description: {node_group[0].get('description', '')}")

            # EXTERNAL ports only (filter out internal signals)
            lines.append(f"\n    --- Interface Ports ---")
            for port in child_yaml.get("ports", []):
                if is_external_port(port):
                    lines.append(
                        f"      {port['name']} | {port['direction']} | {port['type']} | {port.get('description', '')}"
                    )

            # Method signatures
            child_methods = child_yaml.get("methods", [])
            if child_methods:
                lines.append(f"\n    --- Methods ---")
                for m in child_methods:
                    args = ", ".join(
                        f"{a['type']} {a['name']}" for a in m.get("arguments", [])
                    )
                    lines.append(f"      {m['returns']} {m['name']}({args});")
                    if m.get("description"):
                        lines.append(f"        // {m['description']}")

            # Instantiation template - show proper BSV syntax
            if params:
                lines.append(f"\n    --- Instantiation ---")
                # BSV: RoundRobinArbiter#(TDiv#(reqNum, 2)) inst_name <- mkRoundRobinArbiter;
                # The #(...) contains the type parameter VALUES directly (positional)
                type_args = ", ".join(params.values())
                iface_name = child_name.title().replace("_", "")
                mod_name = "mk" + iface_name
                for inst_id in instance_ids:
                    lines.append(f"    //   {iface_name}#({type_args}) {inst_id} <- {mod_name};")

            # DERIVED PROVISOS: child's provisos with param substitution
            derived = compute_child_derived_provisos(child_yaml, params)
            if derived:
                lines.append(f"\n    --- Derivation Provisos REQUIRED ---")
                lines.append(f"    (from {child_name}'s provisos with parameter substitution)")
                for d in derived:
                    lines.append(f"      {d}")

    # ═══════════════════════════════════════════════════════════════
    # LAYER 5: Connection Computations
    # ═══════════════════════════════════════════════════════════════
    connections = module_yaml.get("connections", [])
    if connections:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LAYER 5 — WIRING & CONNECTION COMPUTATIONS")
        lines.append("=" * 70)

        # Group connections by source
        for conn in connections:
            from_node = conn["from"].get("node", conn["from"].get("signal", "?"))
            from_port = conn["from"].get("port", conn["from"].get("signal", "?"))

            from_str = f"{from_node}.{from_port}" if "node" in conn["from"] else f"signal:{from_port}"

            lines.append(f"\n  Source: {from_str}")

            transform = conn.get("transform", "")
            if transform:
                lines.append(f"    Transform: {transform.strip()}")

            for target in conn.get("to", []):
                tgt_node = target.get("node", target.get("signal", "?"))
                tgt_port = target.get("port", target.get("signal", "?"))
                tgt_str = f"{tgt_node}.{tgt_port}" if "node" in target else f"signal:{tgt_port}"
                lines.append(f"    → Target: {tgt_str}")

            if conn.get("description"):
                lines.append(f"    Note: {conn['description']}")

    # ═══════════════════════════════════════════════════════════════
    # LAYER 6: Derived Proviso Closure
    # ═══════════════════════════════════════════════════════════════
    all_derived = []
    if nodes:
        seen_params = set()
        for node in nodes:
            ref = node["ref"]
            params_key = str(sorted(node.get("parameters", {}).items()))
            if (ref, params_key) in seen_params:
                continue
            seen_params.add((ref, params_key))

            child_path = resolve_child_path(project_root, ref)
            if os.path.exists(child_path):
                child_yaml = load_yaml(child_path)
                params = node.get("parameters", {})
                all_derived.extend(compute_child_derived_provisos(child_yaml, params))

    if all_derived:
        lines.append("")
        lines.append("=" * 70)
        lines.append("LAYER 6 — COMPLETE PROVISO CLOSURE")
        lines.append("=" * 70)
        lines.append("Your module MUST include ALL of the following provisos:")
        lines.append("")

        # Module's own
        if own_provisos:
            lines.append("  // Module's own provisos:")
            for p in own_provisos:
                lines.append(f"  {p}")
            lines.append("")

        # Derived from children (deduplicated)
        unique_derived = sorted(set(all_derived))
        lines.append("  // Derived from child instances (parameter substitution):")
        for d in unique_derived:
            lines.append(f"  {d}")

        # Deduplicate and show combined
        all_provisos = list(dict.fromkeys(own_provisos + unique_derived))  # preserve order, dedup
        lines.append("")
        lines.append("  // COMBINED (all required — copy this exactly):")
        lines.append(f"  provisos(")
        for i, p in enumerate(all_provisos):
            comma = "," if i < len(all_provisos) - 1 else ""
            lines.append(f"    {p}{comma}")
        lines.append(f"  );")

    # ═══════════════════════════════════════════════════════════════
    # LAYER 7: Import Guidance
    # ═══════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("LAYER 7 — IMPORT GUIDANCE")
    lines.append("=" * 70)
    lines.append("""
Import ONLY packages your module actually uses. See the Language Template for
the full decision table. Key rules:

  - Reg#(T), Bit#(n), Bool, Integer: BUILT-IN (no import needed)
  - FIFOF#(T): import FIFOF::*
  - Vector#(n, T): import Vector::*
  - PipeOut#(T), mkFork: import PAClib::*
  - CReg, toPipeOut: import PrimUtils::*

If your module is purely combinational or uses only Reg + Bit manipulation,
you likely need ZERO imports beyond what child modules provide.

For THIS specific module, consider:
""")

    # Analyze what's needed based on signals and knowledge
    needs_fifof = False
    needs_vector = False
    needs_paclib = False
    needs_primutils = False

    for sig in signals:
        sig_type = sig.get("type", "")
        if "FIFOF" in sig_type:
            needs_fifof = True
        if "Vector" in sig_type:
            needs_vector = True
        if "PipeOut" in sig_type:
            needs_paclib = True
        if "CReg" in sig_type:
            needs_primutils = True

    # Also check knowledge text for usage hints
    knowledge_text = knowledge.lower() if knowledge else ""
    if "fifof" in knowledge_text or "fifo" in knowledge_text:
        needs_fifof = True
    if "vector" in knowledge_text:
        needs_vector = True

    if not any([needs_fifof, needs_vector, needs_paclib, needs_primutils]):
        lines.append("  → This module likely needs NO imports from project libraries.")
        lines.append("  → Built-in types (Reg, Bit, Bool) require no import.")
    else:
        lines.append("  Based on signal analysis, you likely need:")
        if needs_fifof:
            lines.append("    import FIFOF::*;")
        if needs_vector:
            lines.append("    import Vector::*;")
        if needs_paclib:
            lines.append("    import PAClib::*;")
        if needs_primutils:
            lines.append("    import PrimUtils::*;")

    # ═══════════════════════════════════════════════════════════════
    # GENERATION INSTRUCTIONS
    # ═══════════════════════════════════════════════════════════════
    lines.append("")
    lines.append("=" * 70)
    lines.append("GENERATION INSTRUCTIONS")
    lines.append("=" * 70)
    lines.append(f"""
You are generating ONLY the module `mk{module_name}`.
Do NOT generate code for submodules — they are generated separately.

CRITICAL RULES:
1. Write a complete, compilable Bluespec SystemVerilog file
2. Include a package declaration with package name matching your module
3. Import ONLY the packages your module actually uses (see LAYER 7)
4. Use the EXACT interface, methods, and provisos from the layers above
5. ALL provisos listed in LAYER 6 MUST appear in your module's provisos clause
6. For child submodules, use the instantiation pattern from LAYER 4
7. Internal signals from LAYER 3 should be declared as Reg or local variables
8. Follow the BSV patterns from the language template (LAYER 0)

Output file: generated/{pascal_name}.bsv
""")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path/to/module.yaml>")
        print("Merges multi-level knowledge for a single module (nested_v2 improved algorithm).")
        sys.exit(1)

    yaml_path = sys.argv[1]
    merged = merge_knowledge(yaml_path)
    print(merged)


if __name__ == "__main__":
    main()
