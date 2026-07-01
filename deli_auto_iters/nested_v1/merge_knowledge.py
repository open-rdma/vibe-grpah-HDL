#!/usr/bin/env python3
"""Multi-level knowledge merge script for nested graph experiments.

Merges knowledge from project → parent → child levels.
For a given module YAML, collects:
  1. Project-level: system_knowledge.md + types.yaml
  2. Module's own: meta.knowledge + meta.description + ports
  3. Children's: one level down via nodes[].ref
  4. Wiring: connections section

Output: merged knowledge as plain text, suitable for injection
into a fresh claude session as generation prompt.
"""

import yaml
import sys
import os
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


def merge_knowledge(yaml_path):
    """Merge knowledge for a single module."""
    project_root = find_project_root(yaml_path)
    module_yaml = load_yaml(yaml_path)

    lines = []

    # === Level 0: Project-level BSV conventions ===
    sk_path = os.path.join(project_root, "system_knowledge.md")
    sk = load_text(sk_path)
    if sk:
        lines.append("=" * 70)
        lines.append("PROJECT-LEVEL KNOWLEDGE (BSV Coding Conventions)")
        lines.append("=" * 70)
        lines.append(sk.strip())

    # === Level 1: Shared type definitions ===
    types_path = os.path.join(project_root, "types.yaml")
    if os.path.exists(types_path):
        types_yaml = load_yaml(types_path)
        lines.append("")
        lines.append("=" * 70)
        lines.append("SHARED TYPE DEFINITIONS")
        lines.append("=" * 70)
        for tname, tdef in types_yaml.get("types", {}).items():
            lines.append(f"  {tname}: {tdef.get('description', '')}")
            lines.append(f"    Category: {tdef.get('category', 'unknown')}")

    # === Level 2: Module's own definition ===
    lines.append("")
    lines.append("=" * 70)
    lines.append("MODULE TO GENERATE")
    lines.append("=" * 70)
    meta = module_yaml.get("meta", {})
    lines.append(f"Name: {meta.get('name', 'unknown')}")
    lines.append(f"Description: {meta.get('description', '')}")
    lines.append("")

    knowledge = meta.get("knowledge", "")
    if knowledge:
        lines.append("--- Behavioral Knowledge ---")
        lines.append(knowledge.strip())

    lines.append("")
    lines.append("--- Ports ---")
    for port in module_yaml.get("ports", []):
        lines.append(
            f"  {port['name']} | {port['direction']} | {port['type']} | {port.get('description', '')}"
        )

    # === Level 3: Child submodules (one level down) ===
    nodes = module_yaml.get("nodes", [])
    if nodes:
        lines.append("")
        lines.append("=" * 70)
        lines.append("SUBMODULES TO INSTANTIATE")
        lines.append("=" * 70)

        # Deduplicate by ref path
        seen_refs = set()
        for node in nodes:
            ref = node["ref"]
            if ref in seen_refs:
                continue
            seen_refs.add(ref)

            child_path = os.path.join(project_root, ref)
            if not os.path.exists(child_path):
                lines.append(f"\nWARNING: Child YAML not found: {child_path}")
                continue

            child_yaml = load_yaml(child_path)
            child_meta = child_yaml.get("meta", {})

            lines.append(f"\n### Submodule: {child_meta.get('name', 'unknown')}")
            lines.append(
                f"Local instance(s): {', '.join(n['id'] for n in nodes if n['ref'] == ref)}"
            )
            lines.append(f"Description: {node.get('description', '')}")
            lines.append("")

            child_knowledge = child_meta.get("knowledge", "")
            if child_knowledge:
                lines.append("  --- Child's Behavioral Knowledge ---")
                for line in child_knowledge.strip().split("\n"):
                    lines.append(f"  {line}")
                lines.append("")

            lines.append("  --- Child's Ports ---")
            for port in child_yaml.get("ports", []):
                lines.append(
                    f"    {port['name']} | {port['direction']} | {port['type']} | {port.get('description', '')}"
                )

    # === Level 4: Wiring / Connections ===
    connections = module_yaml.get("connections", [])
    if connections:
        lines.append("")
        lines.append("=" * 70)
        lines.append("WIRING (how submodules and self are connected)")
        lines.append("=" * 70)
        for conn in connections:
            from_str = f"{conn['from']['node']}.{conn['from']['port']}"
            lines.append(f"\n  From: {from_str}")
            for target in conn["to"]:
                lines.append(f"    → To: {target['node']}.{target['port']}")
            if conn.get("description"):
                lines.append(f"    Note: {conn['description']}")

    # === Generation Instructions ===
    lines.append("")
    lines.append("=" * 70)
    lines.append("GENERATION INSTRUCTIONS")
    lines.append("=" * 70)
    lines.append(f"""
You are generating ONLY the module `mk{meta.get('name', 'UnknownModule')}`.
Do NOT generate code for submodules — they are generated separately.
You MUST:
1. Write a complete, compilable Bluespec SystemVerilog file
2. Use ONLY the types and interfaces defined in the knowledge above
3. Include a package declaration
4. Use the correct BSV syntax for all constructs
5. Follow all proviso patterns shown in the project-level knowledge

Output file: generated/{meta.get('name', 'module')}.bsv
""")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path/to/module.yaml>")
        print("Merges multi-level knowledge for a single module.")
        sys.exit(1)

    yaml_path = sys.argv[1]
    merged = merge_knowledge(yaml_path)
    print(merged)


if __name__ == "__main__":
    main()
