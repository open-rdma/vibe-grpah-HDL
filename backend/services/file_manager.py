import os
import yaml

class FileManager:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)

    def _safe_path(self, rel_path: str) -> str:
        full = os.path.abspath(os.path.join(self.project_root, rel_path))
        if not full.startswith(self.project_root):
            raise ValueError(f"Path escapes project root: {rel_path}")
        return full

    def read_yaml(self, rel_path: str) -> dict:
        path = self._safe_path(rel_path)
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def write_yaml(self, rel_path: str, data: dict) -> None:
        path = self._safe_path(rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def delete(self, rel_path: str) -> None:
        path = self._safe_path(rel_path)
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)

    def list_dir(self, rel_path: str) -> list[dict]:
        path = self._safe_path(rel_path)
        if not os.path.isdir(path):
            return []
        entries = []
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            entry = {
                'name': name,
                'type': 'dir' if os.path.isdir(full) else 'file',
                'path': os.path.join(rel_path, name).replace('\\', '/')
            }
            if name.endswith('.yaml'):
                entry['is_graph'] = True
            entries.append(entry)
        return entries

    def resolve_ref(self, ref_path: str, base_dir: str = '') -> dict:
        full_ref = os.path.normpath(os.path.join(base_dir, ref_path)).replace('\\', '/')
        return self.read_yaml(full_ref)

    def exists(self, rel_path: str) -> bool:
        return os.path.exists(self._safe_path(rel_path))
