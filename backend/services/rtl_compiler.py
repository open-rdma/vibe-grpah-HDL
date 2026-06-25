import os
from collections import deque

class RTLCompiler:
    def __init__(self, file_manager, llm_agent):
        self.fm = file_manager
        self.agent = llm_agent

    def get_build_order(self, target_path: str, scope: str) -> list[str]:
        """Return ordered list of graph paths to build (bottom-up)."""
        if scope == 'this':
            return [target_path]

        all_paths = []
        visited = set()
        queue = deque()
        queue.append(target_path)

        while queue:
            path = queue.popleft()
            if path in visited:
                continue
            visited.add(path)
            all_paths.append(path)

            if scope in ('descendants', 'all'):
                data = self.fm.read_yaml(path)
                base_dir = os.path.dirname(path)
                for node in data.get('nodes', []):
                    ref = node.get('ref', '')
                    if ref:
                        ref_path = os.path.normpath(os.path.join(base_dir, ref)).replace('\\', '/')
                        if ref_path not in visited:
                            queue.append(ref_path)

        if scope == 'ancestors':
            all_paths.reverse()
        elif scope in ('descendants', 'all'):
            all_paths.reverse()

        return all_paths

    def build_prompt(self, graph_path: str, mode: str, include_testbench: bool,
                     generated_dir: str, target_lang: str) -> tuple[str, str]:
        """Build system and user prompts for a graph."""
        data = self.fm.read_yaml(graph_path)
        meta = data.get('meta', {})
        ports = data.get('ports', [])
        nodes = data.get('nodes', [])
        connections = data.get('connections', [])
        properties = data.get('properties', {})

        # Collect sub-module interfaces
        sub_interfaces = []
        base_dir = os.path.dirname(graph_path)
        for node in nodes:
            ref = node.get('ref', '')
            if ref:
                ref_path = os.path.normpath(os.path.join(base_dir, ref)).replace('\\', '/')
                try:
                    sub_data = self.fm.read_yaml(ref_path)
                    sub_interfaces.append({
                        'instance': node.get('id'),
                        'ref': ref,
                        'ports': sub_data.get('ports', [])
                    })
                except Exception:
                    pass

        system_prompt = (
            f"You are an expert RTL design engineer. "
            f"Output only synthesizable {target_lang} code. "
            f"Do not include explanations outside of code comments. "
            f"Use proper {target_lang} syntax and conventions."
        )

        user_lines = [
            f"Generate {target_lang} RTL code for module '{meta.get('name', 'unknown')}'.",
            f"",
            f"## Module Description",
            f"{meta.get('description', 'No description provided.')}",
            f"",
            f"## Ports",
        ]
        for p in ports:
            extra = []
            if p.get('category') == 'clock':
                extra.append('clock')
            if p.get('category') == 'reset':
                extra.append(f"reset({p.get('reset_type', 'async')}, active={p.get('active_level', 'high')})")
            if p.get('clock_domain'):
                extra.append(f"domain={p['clock_domain']}")
            etag = f"  [{', '.join(extra)}]" if extra else ""
            user_lines.append(f"  - {p.get('direction', 'input')} {p.get('name', '?')}: {p.get('type', p.get('category', '?'))}{etag}")

        user_lines.append(f"")
        user_lines.append(f"## Properties")
        for k, v in properties.items():
            user_lines.append(f"  {k}: {v}")

        if sub_interfaces:
            user_lines.append(f"")
            user_lines.append(f"## Sub-module Instances")
            for si in sub_interfaces:
                user_lines.append(f"  {si['instance']} (ref: {si['ref']})")
                for sp in si['ports']:
                    user_lines.append(f"    - {sp.get('direction', 'input')} {sp.get('name')}: {sp.get('type', sp.get('category', '?'))}")

        user_lines.append(f"")
        user_lines.append(f"## Connections")
        for conn in connections:
            from_ = conn.get('from', {})
            for to in conn.get('to', []):
                user_lines.append(f"  {from_.get('node')}.{from_.get('port')} → {to.get('node')}.{to.get('port')}")

        if mode == 'incremental':
            generated_path = os.path.join(generated_dir, graph_path).replace('.yaml', '.sv')
            if os.path.exists(generated_path):
                with open(generated_path, 'r', encoding='utf-8') as f:
                    existing = f.read()
                user_lines.append(f"")
                user_lines.append(f"## Existing Code (refine this)")
                user_lines.append(f"```{target_lang}")
                user_lines.append(existing)
                user_lines.append(f"```")

        if include_testbench:
            user_lines.append(f"")
            user_lines.append(f"## Testbench Requirements")
            test_method = meta.get('test_method', '')
            if test_method:
                user_lines.append(f"Test strategy: {test_method}")
            user_lines.append(f"Generate a testbench that instantiates the module, generates realistic stimulus, and checks outputs.")
            user_lines.append(f"Study connected modules' interfaces to produce compatible traffic patterns.")

        return system_prompt, '\n'.join(user_lines)

    def compile_node(self, graph_path: str, mode: str, include_testbench: bool,
                     generated_dir: str, target_lang: str) -> str:
        system, user = self.build_prompt(graph_path, mode, include_testbench,
                                          generated_dir, target_lang)
        return self.agent.generate(system, user)

    def save_output(self, graph_path: str, code: str, generated_dir: str,
                    suffix: str = '.sv'):
        out_path = os.path.join(generated_dir, graph_path).replace('.yaml', suffix)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return out_path
