# RTL Blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a visual digital circuit design tool where users create multi-level module blueprints on a graph canvas, then compile them via LLM into synthesizable Bluespec SystemVerilog.

**Architecture:** Vite-bundled vanilla JS frontend with litegraph.js for graph editing, Flask backend for REST APIs and LLM orchestration. YAML files for graph persistence, Git for versioning. The frontend communicates with the backend via REST; the backend shells out to Claude Code CLI or OpenAI API for RTL generation.

**Tech Stack:** Vite, Vanilla JS (ES modules), litegraph.js v0.7.14 (3rd/ submodule), Flask, PyYAML, GitPython, openai

## Global Constraints

- Target language default: Bluespec SystemVerilog (configurable via templates)
- Port categories: clock, reset, data (with clock_domain, reset_domain fields)
- Connection validation: type-compatibility, category rules, cross-domain blocking
- File format: one YAML per graph, directory hierarchy mirrors module hierarchy
- Version control: Git-based history via GitPython
- LLM: Claude Code CLI (primary), OpenAI API (configurable fallback), ABC-based agent interface
- Frontend: vanilla JS with ES modules, no framework

---

## Phase 1: Project Scaffolding

### Task 1: Scaffold Vite Frontend

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.js`
- Create: `frontend/src/styles/main.css`
- Create: `frontend/src/main.js`

**Interfaces:**
- Consumes: `3rd/litegraph.js/` (existing submodule)
- Produces: Vite dev server serving index.html with litegraph.js loaded

- [ ] **Step 1: Create frontend directory and package.json**

```bash
mkdir -p frontend/src/styles frontend/src/core frontend/src/nodes frontend/src/ui frontend/src/services
```

Create `frontend/package.json`:
```json
{
  "name": "rtl-blueprint",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "vite": "^5.4.0"
  },
  "dependencies": {
    "litegraph.js": "file:../3rd/litegraph.js"
  }
}
```

- [ ] **Step 2: Create vite.config.js**

Create `frontend/vite.config.js`:
```js
import { defineConfig } from 'vite';

export default defineConfig({
  root: '.',
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000'
    }
  },
  build: {
    outDir: 'dist'
  },
  resolve: {
    alias: {
      '@': '/src'
    }
  }
});
```

- [ ] **Step 3: Create index.html**

Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>RTL Blueprint</title>
  <link rel="stylesheet" href="/src/styles/main.css" />
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create main.css with IDE layout**

Create `frontend/src/styles/main.css`:
```css
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --toolbar-height: 40px;
  --statusbar-height: 24px;
  --panel-bg: #1e1e1e;
  --panel-border: #333;
  --text-color: #ccc;
  --text-dim: #888;
  --accent: #4a9eff;
  --clock-color: #0af;
  --reset-color: #f80;
}

html, body, #app {
  width: 100%; height: 100%;
  overflow: hidden;
  background: #121212;
  color: var(--text-color);
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 13px;
}

#toolbar {
  height: var(--toolbar-height);
  background: #252526;
  border-bottom: 1px solid var(--panel-border);
  display: flex;
  align-items: center;
  padding: 0 8px;
  gap: 4px;
}

#toolbar button {
  background: #3a3a3a;
  color: var(--text-color);
  border: 1px solid #555;
  padding: 4px 10px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
}
#toolbar button:hover { background: #4a4a4a; }
#toolbar button:active { background: #505050; }
#toolbar .separator { width: 1px; height: 24px; background: #444; margin: 0 4px; }

#main-area {
  display: flex;
  height: calc(100% - var(--toolbar-height) - var(--statusbar-height));
}

#project-panel {
  width: 240px;
  min-width: 160px;
  background: var(--panel-bg);
  border-right: 1px solid var(--panel-border);
  overflow-y: auto;
  padding: 8px;
}

#canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

#canvas-container canvas {
  position: absolute;
  top: 0; left: 0;
}

#property-panel {
  width: 280px;
  min-width: 200px;
  background: var(--panel-bg);
  border-left: 1px solid var(--panel-border);
  overflow-y: auto;
  padding: 8px;
}

#statusbar {
  height: var(--statusbar-height);
  background: #007acc;
  color: #fff;
  display: flex;
  align-items: center;
  padding: 0 10px;
  font-size: 12px;
  justify-content: space-between;
}

.property-group {
  margin-bottom: 12px;
}
.property-group label {
  display: block;
  color: var(--text-dim);
  font-size: 11px;
  margin-bottom: 2px;
  text-transform: uppercase;
}
.property-group input, .property-group textarea, .property-group select {
  width: 100%;
  padding: 4px 6px;
  background: #2d2d2d;
  border: 1px solid #444;
  color: var(--text-color);
  border-radius: 2px;
  font-size: 12px;
}
.property-group textarea {
  resize: vertical;
  min-height: 60px;
}

.tree-item {
  padding: 3px 6px;
  cursor: pointer;
  border-radius: 2px;
  user-select: none;
}
.tree-item:hover { background: #2a2a2a; }
.tree-item.selected { background: #094771; }
.tree-item .icon { margin-right: 4px; }

.dialog-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.6);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.dialog {
  background: #252526;
  border: 1px solid #555;
  border-radius: 4px;
  padding: 16px;
  min-width: 360px;
}
.dialog h3 { margin-bottom: 12px; font-size: 14px; }
.dialog .dialog-actions {
  margin-top: 12px; display: flex; justify-content: flex-end; gap: 6px;
}

.toast {
  position: fixed; bottom: 40px; right: 16px;
  background: #333; color: #fff;
  padding: 8px 16px; border-radius: 4px;
  font-size: 12px; z-index: 2000;
  animation: fadeIn 0.2s ease;
}
.toast.error { background: #a33; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
```

- [ ] **Step 5: Create main.js entry point**

Create `frontend/src/main.js`:
```js
import { App } from './app.js';

document.addEventListener('DOMContentLoaded', () => {
  window.__app = new App();
});
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd frontend && npm install
```
Expected: installs vite + litegraph.js without errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/ && git commit -m "feat: scaffold Vite frontend with IDE layout CSS"
```

---

### Task 2: Scaffold Flask Backend

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app.py`

**Interfaces:**
- Produces: Flask app on port 5000 with CORS, serving static files from `frontend/dist/` in production

- [ ] **Step 1: Create requirements.txt**

Create `backend/requirements.txt`:
```
flask==3.1.0
flask-cors==5.0.1
pyyaml==6.0.2
gitpython==3.1.44
openai==1.58.1
```

- [ ] **Step 2: Create app.py**

Create `backend/app.py`:
```python
import os
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
CORS(app)

# In production, serve the Vite build output
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)

@app.route('/src/<path:filename>')
def serve_src(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'src'), filename)

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

- [ ] **Step 3: Install dependencies and verify**

```bash
cd backend && pip install -r requirements.txt
python -c "from app import app; print('Flask app created')"
```
Expected: "Flask app created"

- [ ] **Step 4: Commit**

```bash
git add backend/ && git commit -m "feat: scaffold Flask backend"
```

---

## Phase 2: Backend Core Services

### Task 3: File Manager Service

**Files:**
- Create: `backend/services/__init__.py` (empty)
- Create: `backend/services/file_manager.py`

**Interfaces:**
- Produces:
  - `FileManager.read_yaml(path: str) -> dict`
  - `FileManager.write_yaml(path: str, data: dict) -> None`
  - `FileManager.delete(path: str) -> None`
  - `FileManager.list_dir(path: str) -> list[dict]`
  - `FileManager.resolve_ref(ref_path: str, base_dir: str) -> dict`

- [ ] **Step 1: Create file_manager.py**

Create `backend/services/__init__.py`:
```python
```

Create `backend/services/file_manager.py`:
```python
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
```

- [ ] **Step 2: Verify with Python import**

```bash
cd backend && python -c "from services.file_manager import FileManager; print('FileManager imported OK')"
```
Expected: "FileManager imported OK"

- [ ] **Step 3: Commit**

```bash
git add backend/services/ && git commit -m "feat: add FileManager service for YAML read/write"
```

---

### Task 4: Backend Type System API

**Files:**
- Create: `backend/api/__init__.py` (empty)
- Create: `backend/api/types.py`
- Modify: `backend/app.py` (register blueprint)

**Interfaces:**
- Produces:
  - `GET /api/types/list` → `{"types": {...}}`
  - `POST /api/types/save` body: `{"types": {...}}` → `{"ok": true}`
  - `GET /api/types/check?from=X&to=Y` → `{"compatible": bool, "reason": str}`

- [ ] **Step 1: Create types API blueprint**

Create `backend/api/__init__.py`:
```python
```

Create `backend/api/types.py`:
```python
import re
from flask import Blueprint, request, jsonify, current_app

types_bp = Blueprint('types', __name__)

def _types_path():
    return current_app.config.get('TYPES_PATH', 'types.yaml')

def _fm():
    return current_app.config['FILE_MANAGER']

@types_bp.route('/list', methods=['GET'])
def list_types():
    fm = _fm()
    path = _types_path()
    if not fm.exists(path):
        return jsonify({'types': {}})
    return jsonify({'types': fm.read_yaml(path).get('types', {})})

@types_bp.route('/save', methods=['POST'])
def save_types():
    data = request.get_json()
    fm = _fm()
    fm.write_yaml(_types_path(), {'types': data.get('types', {})})
    return jsonify({'ok': True})

def _parse_type(type_str: str) -> dict:
    """Parse a type string like 'logic[7:0]' into structured form."""
    m = re.match(r'^(\w+)(?:\[(\d+):(\d+)\])?$', type_str)
    if not m:
        return {'base': type_str}
    return {'base': m.group(1), 'msb': int(m.group(2)), 'lsb': int(m.group(3))}

@types_bp.route('/check', methods=['GET'])
def check_types():
    from_type = request.args.get('from', '')
    to_type = request.args.get('to', '')
    if from_type == to_type:
        return jsonify({'compatible': True, 'reason': ''})

    fp = _parse_type(from_type)
    tp = _parse_type(to_type)

    if fp.get('base') != tp.get('base'):
        return jsonify({'compatible': False, 'reason': f"Base types differ: {fp.get('base')} vs {tp.get('base')}"})

    if 'msb' in fp and 'msb' in tp:
        fw = fp['msb'] - fp['lsb'] + 1
        tw = tp['msb'] - tp['lsb'] + 1
        if fw != tw:
            return jsonify({'compatible': False, 'reason': f"Width mismatch: {fw} vs {tw}"})

    return jsonify({'compatible': True, 'reason': ''})
```

- [ ] **Step 2: Register blueprint in app.py**

Modify `backend/app.py`: replace the file content with:
```python
import os
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
CORS(app)

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')

from services.file_manager import FileManager

@app.before_request
def setup_fm():
    project_root = app.config.get('PROJECT_ROOT', os.getcwd())
    if 'FILE_MANAGER' not in app.config:
        app.config['FILE_MANAGER'] = FileManager(project_root)

from api.types import types_bp
app.register_blueprint(types_bp, url_prefix='/api/types')

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)

@app.route('/src/<path:filename>')
def serve_src(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'src'), filename)

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

- [ ] **Step 3: Verify with a quick test**

```bash
cd backend && python -c "
import tempfile, os
from app import app
from services.file_manager import FileManager

# Create a temp project dir
d = tempfile.mkdtemp()
app.config['PROJECT_ROOT'] = d
app.config['FILE_MANAGER'] = FileManager(d)

with app.test_client() as client:
    # Test save
    resp = client.post('/api/types/save', json={'types': {'logic': {'description': 'bit'}}})
    assert resp.status_code == 200
    # Test list
    resp = client.get('/api/types/list')
    assert resp.json['types']['logic']['description'] == 'bit'
    # Test check
    resp = client.get('/api/types/check?from=logic&to=logic')
    assert resp.json['compatible'] == True
print('All type API tests passed')
"
```
Expected: "All type API tests passed"

- [ ] **Step 4: Commit**

```bash
git add backend/api/ backend/app.py && git commit -m "feat: add type system API endpoints"
```

---

### Task 5: Graph CRUD API

**Files:**
- Create: `backend/api/graph.py`
- Modify: `backend/app.py` (register blueprint)

**Interfaces:**
- Produces:
  - `GET /api/graph/load?path=top/top.yaml` → graph YAML as JSON
  - `POST /api/graph/save` body: `{"path": "...", "data": {...}}` → `{"ok": true}`
  - `POST /api/graph/validate` body: `{"path": "..."}` → `{"valid": bool, "errors": [...]}`
  - `DELETE /api/graph/delete?path=...` → `{"ok": true}`

- [ ] **Step 1: Create graph API blueprint**

Create `backend/api/graph.py`:
```python
from flask import Blueprint, request, jsonify, current_app

graph_bp = Blueprint('graph', __name__)

def _fm():
    return current_app.config['FILE_MANAGER']

@graph_bp.route('/load', methods=['GET'])
def load_graph():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'error': 'path required'}), 400
    fm = _fm()
    if not fm.exists(path):
        return jsonify({'error': 'Graph not found'}), 404
    data = fm.read_yaml(path)
    return jsonify({'path': path, 'data': data})

@graph_bp.route('/save', methods=['POST'])
def save_graph():
    body = request.get_json()
    path = body.get('path', '')
    data = body.get('data', {})
    if not path:
        return jsonify({'error': 'path required'}), 400
    _fm().write_yaml(path, data)
    return jsonify({'ok': True})

@graph_bp.route('/validate', methods=['POST'])
def validate_graph():
    body = request.get_json()
    path = body.get('path', '')
    if not path:
        return jsonify({'error': 'path required'}), 400
    fm = _fm()
    if not fm.exists(path):
        return jsonify({'valid': False, 'errors': ['Graph file not found']})
    data = fm.read_yaml(path)
    errors = []

    if not data.get('meta', {}).get('name'):
        errors.append('Missing meta.name')

    for port in data.get('ports', []):
        if not port.get('name'):
            errors.append('Port missing name')
        if port.get('category') == 'data' and not port.get('type'):
            errors.append(f"Data port '{port.get('name', '?')}' missing type")

    for node in data.get('nodes', []):
        if not node.get('id'):
            errors.append('Node missing id')
        if not node.get('description'):
            errors.append(f"Node '{node.get('id', '?')}' missing description")
        if node.get('ref') and not fm.exists(node['ref']):
            errors.append(f"Node '{node['id']}' ref '{node['ref']}' not found")

    return jsonify({'valid': len(errors) == 0, 'errors': errors})

@graph_bp.route('/delete', methods=['DELETE'])
def delete_graph():
    path = request.args.get('path', '')
    if not path:
        return jsonify({'error': 'path required'}), 400
    _fm().delete(path)
    return jsonify({'ok': True})
```

- [ ] **Step 2: Register blueprint in app.py**

Edit `backend/app.py`, add after the types blueprint registration:
```python
from api.graph import graph_bp
app.register_blueprint(graph_bp, url_prefix='/api/graph')
```

- [ ] **Step 3: Verify with a quick test**

```bash
cd backend && python -c "
import tempfile, os
from app import app
from services.file_manager import FileManager

d = tempfile.mkdtemp()
app.config['PROJECT_ROOT'] = d
app.config['FILE_MANAGER'] = FileManager(d)

graph_data = {
    'meta': {'name': 'test', 'description': 'test module'},
    'ports': [{'name': 'clk', 'direction': 'input', 'category': 'clock'}],
    'nodes': [],
    'connections': []
}

with app.test_client() as client:
    resp = client.post('/api/graph/save', json={'path': 'top/test.yaml', 'data': graph_data})
    assert resp.status_code == 200
    resp = client.get('/api/graph/load?path=top/test.yaml')
    assert resp.json['data']['meta']['name'] == 'test'
    resp = client.post('/api/graph/validate', json={'path': 'top/test.yaml'})
    assert resp.json['valid'] == True
print('All graph API tests passed')
"
```
Expected: "All graph API tests passed"

- [ ] **Step 4: Commit**

```bash
git add backend/api/graph.py backend/app.py && git commit -m "feat: add graph CRUD API endpoints"
```

---

### Task 6: Project Management API

**Files:**
- Create: `backend/api/project.py`
- Modify: `backend/app.py` (register blueprint)

**Interfaces:**
- Produces:
  - `POST /api/project/create` body: `{"path": "...", "name": "..."}` → scaffold project with project.yaml, types.yaml, top/ and library/ dirs
  - `POST /api/project/open` body: `{"path": "..."}` → reads project.yaml, sets PROJECT_ROOT
  - `POST /api/project/save` body: `{"config": {...}}` → writes project.yaml
  - `GET /api/project/trees` → list tree roots
  - `POST /api/project/tree/create` body: `{"name": "..."}` → create new tree directory

- [ ] **Step 1: Create project API blueprint**

Create `backend/api/project.py`:
```python
import os
from flask import Blueprint, request, jsonify, current_app

project_bp = Blueprint('project', __name__)

DEFAULT_PROJECT_YAML = {
    'name': '',
    'version': '0.1.0',
    'target_language': 'bluespec_sv',
    'trees': ['top', 'library'],
    'llm_config': {
        'provider': 'claude_code',
        'openai_model': 'gpt-4o',
        'openai_api_key': ''
    }
}

DEFAULT_TYPES_YAML = {
    'types': {
        'logic': {'description': 'Single-bit logic signal', 'category': 'builtin'},
        'logic[N:M]': {'description': 'Multi-bit bus', 'category': 'builtin',
                        'params': [{'name': 'N', 'type': 'int'}, {'name': 'M', 'type': 'int'}]}
    }
}

def _fm():
    return current_app.config['FILE_MANAGER']

@project_bp.route('/create', methods=['POST'])
def create_project():
    body = request.get_json()
    project_path = body.get('path', '')
    name = body.get('name', 'new_project')

    if not project_path:
        return jsonify({'error': 'path required'}), 400

    fm = _fm()
    project_root = os.path.abspath(os.path.join(fm.project_root, project_path))
    os.makedirs(project_root, exist_ok=True)

    app = current_app
    app.config['PROJECT_ROOT'] = project_root
    app.config['FILE_MANAGER'] = __import__('services.file_manager', fromlist=['FileManager']).FileManager(project_root)
    fm = app.config['FILE_MANAGER']

    proj_config = dict(DEFAULT_PROJECT_YAML)
    proj_config['name'] = name

    fm.write_yaml('project.yaml', proj_config)
    fm.write_yaml('types.yaml', DEFAULT_TYPES_YAML)

    os.makedirs(os.path.join(project_root, 'top'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'library'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'generated'), exist_ok=True)

    top_graph = {
        'meta': {'name': name, 'description': '', 'test_method': ''},
        'properties': {},
        'ports': [],
        'nodes': [],
        'connections': []
    }
    fm.write_yaml(f'top/{name}.yaml', top_graph)

    return jsonify({'ok': True, 'project': proj_config, 'trees': proj_config['trees']})

@project_bp.route('/open', methods=['POST'])
def open_project():
    body = request.get_json()
    project_path = body.get('path', '')
    if not project_path:
        return jsonify({'error': 'path required'}), 400

    fm = _fm()
    project_root = os.path.abspath(os.path.join(fm.project_root, project_path))
    if not os.path.exists(os.path.join(project_root, 'project.yaml')):
        return jsonify({'error': 'Not a valid project'}), 400

    current_app.config['PROJECT_ROOT'] = project_root
    current_app.config['FILE_MANAGER'] = __import__('services.file_manager', fromlist=['FileManager']).FileManager(project_root)
    fm = current_app.config['FILE_MANAGER']

    config = fm.read_yaml('project.yaml')
    return jsonify({'ok': True, 'project': config, 'trees': config.get('trees', [])})

@project_bp.route('/save', methods=['POST'])
def save_project():
    body = request.get_json()
    config = body.get('config', {})
    if not config:
        return jsonify({'error': 'config required'}), 400
    _fm().write_yaml('project.yaml', config)
    return jsonify({'ok': True})

@project_bp.route('/trees', methods=['GET'])
def list_trees():
    config = _fm().read_yaml('project.yaml')
    trees = config.get('trees', ['top', 'library'])
    return jsonify({'trees': trees})

@project_bp.route('/tree/create', methods=['POST'])
def create_tree():
    body = request.get_json()
    tree_name = body.get('name', '')
    if not tree_name:
        return jsonify({'error': 'name required'}), 400
    fm = _fm()
    os.makedirs(os.path.join(fm.project_root, tree_name), exist_ok=True)

    config = fm.read_yaml('project.yaml')
    if tree_name not in config.get('trees', []):
        config.setdefault('trees', []).append(tree_name)
        fm.write_yaml('project.yaml', config)

    return jsonify({'ok': True, 'tree': tree_name})
```

- [ ] **Step 2: Register blueprint in app.py**

Edit `backend/app.py`, add after the graph blueprint registration:
```python
from api.project import project_bp
app.register_blueprint(project_bp, url_prefix='/api/project')
```

- [ ] **Step 3: Verify**

```bash
cd backend && python -c "
import tempfile, os
from app import app
from services.file_manager import FileManager

d = tempfile.mkdtemp()
base_fm = FileManager(d)
app.config['PROJECT_ROOT'] = d
app.config['FILE_MANAGER'] = base_fm

with app.test_client() as client:
    resp = client.post('/api/project/create', json={'path': 'my_proj', 'name': 'my_proj'})
    assert resp.status_code == 200
    assert resp.json['trees'] == ['top', 'library']
    assert os.path.exists(os.path.join(d, 'my_proj', 'project.yaml'))
print('Project API tests passed')
"
```
Expected: "Project API tests passed"

- [ ] **Step 4: Commit**

```bash
git add backend/api/project.py backend/app.py && git commit -m "feat: add project management API"
```

---

### Task 7: Git API

**Files:**
- Create: `backend/api/git.py`
- Modify: `backend/app.py` (register blueprint)

**Interfaces:**
- Produces:
  - `POST /api/git/commit` body: `{"message": "..."}` → `{"ok": true, "hash": "..."}`
  - `GET /api/git/log` → `{"commits": [{"hash":..., "message":..., "date":...}, ...]}`
  - `POST /api/git/checkout` body: `{"hash": "..."}` → `{"ok": true}`

- [ ] **Step 1: Create git API blueprint**

Create `backend/api/git.py`:
```python
import os
from git import Repo, GitCommandError
from flask import Blueprint, request, jsonify, current_app

git_bp = Blueprint('git', __name__)

def _get_repo():
    project_root = current_app.config['PROJECT_ROOT']
    try:
        return Repo(project_root)
    except Exception:
        return Repo.init(project_root)

@git_bp.route('/commit', methods=['POST'])
def commit():
    body = request.get_json()
    message = body.get('message', 'snapshot')
    repo = _get_repo()
    repo.git.add(A=True)
    commit = repo.index.commit(message)
    return jsonify({'ok': True, 'hash': commit.hexsha})

@git_bp.route('/log', methods=['GET'])
def log():
    repo = _get_repo()
    count = request.args.get('count', 50, type=int)
    commits = []
    for c in repo.iter_commits(max_count=count):
        commits.append({
            'hash': c.hexsha[:8],
            'full_hash': c.hexsha,
            'message': c.message.strip(),
            'date': c.committed_datetime.isoformat(),
            'author': str(c.author)
        })
    return jsonify({'commits': commits})

@git_bp.route('/checkout', methods=['POST'])
def checkout():
    body = request.get_json()
    ref = body.get('hash', '')
    if not ref:
        return jsonify({'error': 'hash required'}), 400
    repo = _get_repo()
    try:
        repo.git.checkout(ref)
        return jsonify({'ok': True})
    except GitCommandError as e:
        return jsonify({'error': str(e)}), 400
```

- [ ] **Step 2: Register blueprint in app.py**

Edit `backend/app.py`, add after project blueprint:
```python
from api.git import git_bp
app.register_blueprint(git_bp, url_prefix='/api/git')
```

- [ ] **Step 3: Verify**

```bash
cd backend && python -c "
import tempfile, os
from app import app
from services.file_manager import FileManager

d = tempfile.mkdtemp()
app.config['PROJECT_ROOT'] = d
app.config['FILE_MANAGER'] = FileManager(d)

# Create a file so git has something to commit
with open(os.path.join(d, 'test.txt'), 'w') as f:
    f.write('hello')

with app.test_client() as client:
    resp = client.post('/api/git/commit', json={'message': 'test commit'})
    assert resp.status_code == 200
    resp = client.get('/api/git/log')
    assert len(resp.json['commits']) == 1
print('Git API tests passed')
"
```
Expected: "Git API tests passed"

- [ ] **Step 4: Commit**

```bash
git add backend/api/git.py backend/app.py && git commit -m "feat: add git version control API"
```

---

### Task 8: LLM Agent Service

**Files:**
- Create: `backend/services/llm_agent.py`

**Interfaces:**
- Produces:
  - `LLMAgent` ABC with `generate(system_prompt, user_prompt, context_files=None) -> str`
  - `ClaudeCodeAgent(LLMAgent)` — subprocess call to `claude`
  - `OpenAIAgent(LLMAgent)` — OpenAI SDK
  - `create_agent(config: dict) -> LLMAgent` factory

- [ ] **Step 1: Create llm_agent.py**

Create `backend/services/llm_agent.py`:
```python
from abc import ABC, abstractmethod
import subprocess
import tempfile
import os

class LLMAgent(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        """Generate text from the LLM."""


class ClaudeCodeAgent(LLMAgent):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model = self.config.get('model', 'claude-sonnet-4-6')

    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt',
                                         delete=False, encoding='utf-8') as f:
            f.write(f"{system_prompt}\n\n---\n\n{user_prompt}")
            prompt_file = f.name

        try:
            result = subprocess.run(
                ['claude', '--print', '--prompt', prompt_file,
                 '--model', self.model],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                raise RuntimeError(f"Claude Code error: {result.stderr}")
            return result.stdout.strip()
        finally:
            os.unlink(prompt_file)


class OpenAIAgent(LLMAgent):
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.model = self.config.get('model', 'gpt-4o')
        self.api_key = self.config.get('api_key', '')

    def generate(self, system_prompt: str, user_prompt: str,
                 context_files: list[str] = None) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        messages = [{"role": "system", "content": system_prompt}]
        if context_files:
            for cf in context_files:
                if os.path.exists(cf):
                    with open(cf, 'r', encoding='utf-8') as f:
                        messages.append({"role": "user", "content": f"Context file {cf}:\n```\n{f.read()}\n```"})

        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content.strip()


def create_agent(config: dict) -> LLMAgent:
    provider = config.get('provider', 'claude_code')
    if provider == 'openai':
        return OpenAIAgent(config.get('openai_config', {}))
    return ClaudeCodeAgent(config.get('claude_config', {}))
```

- [ ] **Step 2: Verify import**

```bash
cd backend && python -c "
from services.llm_agent import ClaudeCodeAgent, OpenAIAgent, create_agent

agent = create_agent({'provider': 'claude_code'})
assert isinstance(agent, ClaudeCodeAgent)

agent2 = create_agent({'provider': 'openai', 'openai_config': {'api_key': 'sk-test'}})
assert isinstance(agent2, OpenAIAgent)
print('LLM Agent tests passed')
"
```
Expected: "LLM Agent tests passed"

- [ ] **Step 3: Commit**

```bash
git add backend/services/llm_agent.py && git commit -m "feat: add LLM agent service with Claude Code and OpenAI backends"
```

---

### Task 9: Build Pipeline API

**Files:**
- Create: `backend/api/build.py`
- Create: `backend/services/rtl_compiler.py`
- Modify: `backend/app.py` (register build blueprint)

**Interfaces:**
- Produces:
  - `POST /api/build` body: `{"target_node": "...", "scope": "...", "mode": "...", "include_testbench": bool}` → `{"task_id": "uuid"}`
  - `GET /api/build/status/<task_id>` → `{"status": "pending|running|done|failed", "progress": {...}}`
  - `GET /api/build/output/<task_id>` → `{"files": {"path": "content", ...}}`

- [ ] **Step 1: Create rtl_compiler.py**

Create `backend/services/rtl_compiler.py`:
```python
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
```

- [ ] **Step 2: Create build API blueprint**

Create `backend/api/build.py`:
```python
import uuid
import threading
from flask import Blueprint, request, jsonify, current_app

build_bp = Blueprint('build', __name__)

_tasks = {}

def _fm():
    return current_app.config['FILE_MANAGER']

def _run_build(task_id, target_node, scope, mode, include_testbench):
    from services.rtl_compiler import RTLCompiler
    from services.llm_agent import create_agent

    task = _tasks[task_id]
    task['status'] = 'running'
    task['progress'] = {'current': '', 'completed': [], 'total': 0}

    try:
        fm = _fm()
        config = fm.read_yaml('project.yaml')
        llm_config = config.get('llm_config', {})
        agent = create_agent(llm_config)
        compiler = RTLCompiler(fm, agent)

        target_lang = config.get('target_language', 'bluespec_sv')
        generated_dir = 'generated'

        paths = compiler.get_build_order(target_node, scope)
        task['progress']['total'] = len(paths)

        for path in paths:
            task['progress']['current'] = path
            code = compiler.compile_node(path, mode, include_testbench,
                                          generated_dir, target_lang)
            compiler.save_output(path, code, generated_dir)
            task['progress']['completed'].append(path)

        task['status'] = 'done'
    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)

@build_bp.route('', methods=['POST'])
def start_build():
    body = request.get_json()
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        'id': task_id,
        'status': 'pending',
        'target_node': body.get('target_node', ''),
        'scope': body.get('scope', 'this'),
        'mode': body.get('mode', 'fresh'),
        'include_testbench': body.get('include_testbench', False),
        'progress': {}
    }

    thread = threading.Thread(
        target=_run_build,
        args=(task_id,
              body.get('target_node', ''),
              body.get('scope', 'this'),
              body.get('mode', 'fresh'),
              body.get('include_testbench', False))
    )
    thread.daemon = True
    thread.start()

    return jsonify({'task_id': task_id})

@build_bp.route('/status/<task_id>', methods=['GET'])
def build_status(task_id):
    task = _tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify({
        'status': task['status'],
        'progress': task.get('progress', {}),
        'error': task.get('error', '')
    })

@build_bp.route('/output/<task_id>', methods=['GET'])
def build_output(task_id):
    import os as _os
    task = _tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    if task['status'] != 'done':
        return jsonify({'error': 'Build not complete'}), 400

    fm = _fm()
    generated_dir = 'generated'
    files = {}
    for path in task.get('progress', {}).get('completed', []):
        out_path = path.replace('.yaml', '.sv')
        full_path = _os.path.join(fm.project_root, generated_dir, out_path)
        if _os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                files[out_path] = f.read()

    return jsonify({'files': files})
```

- [ ] **Step 3: Register blueprint in app.py**

Edit `backend/app.py`, add after git blueprint:
```python
from api.build import build_bp
app.register_blueprint(build_bp, url_prefix='/api/build')
```

- [ ] **Step 4: Verify import chain**

```bash
cd backend && python -c "
from app import app
from services.rtl_compiler import RTLCompiler
print('Build pipeline imports OK')
"
```
Expected: "Build pipeline imports OK"

- [ ] **Step 5: Commit**

```bash
git add backend/api/build.py backend/services/rtl_compiler.py backend/app.py && git commit -m "feat: add build pipeline with RTL compiler"
```

---

## Phase 3: Frontend Core

### Task 10: litegraph.js Integration & RTL Module Node

**Files:**
- Create: `frontend/src/nodes/rtl-module.js`

**Interfaces:**
- Produces: `RTLModuleNode` class registered as `rtl/module`
  - Constructor sets up ports from graph data
  - `getPortColor(category)` → color string
  - `onConnectInput/onConnectOutput` validation hooks (delegates to validator)
  - `onDblClick` → opens subgraph if node has `_subgraph` set

- [ ] **Step 1: Create rtl-module.js**

Create `frontend/src/nodes/rtl-module.js`:
```js
const PORT_COLORS = {
  clock: '#0af',
  reset: '#f80',
  data: '#aaa'
};

/**
 * RTL Module Node — represents a module instance on the canvas.
 * Subclassed via litegraph.js prototype copying system.
 */
function RTLModuleNode() {
  // Ports will be added by the graph manager after construction
  this.properties = {};
  this._module_ref = null;
  this._module_data = null;
}

RTLModuleNode.title = 'RTL Module';
RTLModuleNode.desc = 'An RTL module instance';

RTLModuleNode.prototype.getPortColor = function(category) {
  return PORT_COLORS[category] || PORT_COLORS.data;
};

RTLModuleNode.prototype.onConnectInput = function(target_slot, type, output_slot, output_node) {
  // Delegate to global connection validator if registered
  if (window.__connectionValidator) {
    var result = window.__connectionValidator.validate(
      output_node, output_slot,
      this, target_slot
    );
    if (!result.allowed) {
      window.__showToast('Connection blocked: ' + result.reason, 'error');
      return false;
    }
  }
  return true;
};

RTLModuleNode.prototype.onConnectOutput = function(output_slot, type, input_slot, input_node) {
  if (window.__connectionValidator) {
    var result = window.__connectionValidator.validate(
      this, output_slot,
      input_node, input_slot
    );
    if (!result.allowed) {
      window.__showToast('Connection blocked: ' + result.reason, 'error');
      return false;
    }
  }
  return true;
};

RTLModuleNode.prototype.onDblClick = function(e, pos, graphcanvas) {
  if (this._subgraph) {
    graphcanvas.openSubgraph(this._subgraph);
    return true;
  }
  return false;
};

RTLModuleNode.prototype.setPortsFromData = function(moduleData) {
  // Clear existing ports
  this.inputs.length = 0;
  this.outputs.length = 0;

  var ports = moduleData.ports || [];
  for (var i = 0; i < ports.length; i++) {
    var p = ports[i];
    var color = this.getPortColor(p.category);
    if (p.direction === 'input') {
      this.addInput(p.name, p.type || p.category || 'data');
      var idx = this.inputs.length - 1;
      this.inputs[idx].color_on = color;
      this.inputs[idx]._port_data = p;
    } else {
      this.addOutput(p.name, p.type || p.category || 'data');
      var idx2 = this.outputs.length - 1;
      this.outputs[idx2].color_on = color;
      this.outputs[idx2]._port_data = p;
    }
  }
};

LiteGraph.registerNodeType('rtl/module', RTLModuleNode);
```

- [ ] **Step 2: Update main.js to import the node**

Modify `frontend/src/main.js`:
```js
import 'litegraph.js';
import './nodes/rtl-module.js';
import { App } from './app.js';

document.addEventListener('DOMContentLoaded', () => {
  window.__app = new App();
});
```

- [ ] **Step 3: Verify Vite dev server loads without errors**

```bash
cd frontend && npx vite build 2>&1 | tail -5
```
Expected: build completes, no fatal errors about module resolution.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/nodes/ frontend/src/main.js && git commit -m "feat: add RTL module node type for litegraph.js"
```

---

### Task 11: Type System (Frontend)

**Files:**
- Create: `frontend/src/core/type-system.js`

**Interfaces:**
- Produces: `TypeSystem` class
  - `loadFromServer() -> Promise` — fetches from /api/types/list
  - `getTypes() -> object`
  - `addType(name, definition)`
  - `removeType(name)`
  - `areCompatible(typeA, typeB) -> bool` — local check

- [ ] **Step 1: Create type-system.js**

Create `frontend/src/core/type-system.js`:
```js
class TypeSystem {
  constructor() {
    this._types = {};
  }

  async loadFromServer() {
    try {
      const resp = await fetch('/api/types/list');
      const data = await resp.json();
      this._types = data.types || {};
    } catch (e) {
      console.warn('Failed to load types from server, using defaults', e);
    }
  }

  getTypes() {
    return this._types;
  }

  getType(name) {
    return this._types[name] || null;
  }

  addType(name, definition) {
    this._types[name] = definition;
  }

  removeType(name) {
    delete this._types[name];
  }

  areCompatible(typeA, typeB) {
    if (!typeA || !typeB) return true;
    if (typeA === typeB) return true;

    // Parse bus types like logic[7:0]
    const parse = (t) => {
      const m = t.match(/^(\w+)(?:\[(\d+):(\d+)\])?$/);
      if (!m) return { base: t };
      return { base: m[1], width: Math.abs(parseInt(m[2]) - parseInt(m[3])) + 1 };
    };

    const pa = parse(typeA);
    const pb = parse(typeB);
    if (pa.base !== pb.base) return false;
    if (pa.width && pb.width && pa.width !== pb.width) return false;
    return true;
  }
}

export { TypeSystem };
```

- [ ] **Step 2: Verify import**

```bash
cd frontend && node -e "
// Can't test full import without browser, but check syntax
const fs = require('fs');
const code = fs.readFileSync('src/core/type-system.js', 'utf-8');
console.log('Type system: syntax OK,', code.length, 'bytes');
"
```
Expected: "Type system: syntax OK"

- [ ] **Step 3: Commit**

```bash
git add frontend/src/core/type-system.js && git commit -m "feat: add frontend type system"
```

---

### Task 12: Connection Validator

**Files:**
- Create: `frontend/src/core/connection-validator.js`

**Interfaces:**
- Produces: `ConnectionValidator` class
  - `validate(outputNode, outputSlot, inputNode, inputSlot) -> {allowed: bool, reason: string}`

- [ ] **Step 1: Create connection-validator.js**

Create `frontend/src/core/connection-validator.js`:
```js
class ConnectionValidator {
  constructor(typeSystem) {
    this._typeSystem = typeSystem;
  }

  validate(outputNode, outputSlotIdx, inputNode, inputSlotIdx) {
    const outSlot = outputNode.outputs[outputSlotIdx];
    const inSlot = inputNode.inputs[inputSlotIdx];

    if (!outSlot || !inSlot) {
      return { allowed: false, reason: 'Invalid slot' };
    }

    const outPort = outSlot._port_data || {};
    const inPort = inSlot._port_data || {};

    const outCat = outPort.category || 'data';
    const inCat = inPort.category || 'data';

    // Rule: data → clock/reset is blocked
    if (outCat === 'data' && (inCat === 'clock' || inCat === 'reset')) {
      return { allowed: false, reason: `Cannot connect data output to ${inCat} input` };
    }

    // Rule: type compatibility
    const outType = outPort.type || outCat;
    const inType = inPort.type || inCat;
    if (outCat === 'data' && inCat === 'data') {
      if (!this._typeSystem.areCompatible(outType, inType)) {
        return { allowed: false, reason: `Type mismatch: ${outType} vs ${inType}` };
      }
    }

    // Rule: cross-domain check
    const outDomain = outPort.clock_domain || '';
    const inDomain = inPort.clock_domain || '';
    if (outCat === 'data' && inCat === 'data' && outDomain && inDomain && outDomain !== inDomain) {
      return { allowed: false, reason: `Cross-domain connection blocked (${outDomain} → ${inDomain}). Set allow_cross_domain to override.` };
    }

    return { allowed: true, reason: '' };
  }
}

export { ConnectionValidator };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/core/connection-validator.js && git commit -m "feat: add connection validator with category/type/domain rules"
```

---

### Task 13: Graph Manager

**Files:**
- Create: `frontend/src/core/graph-manager.js`

**Interfaces:**
- Produces: `GraphManager` class
  - `newGraph(name) -> LGraph` — creates empty graph
  - `loadGraph(path) -> Promise<LGraph>` — loads from API, populates canvas
  - `saveGraph(path) -> Promise` — serializes canvas → API
  - `addSubgraphNode(refPath, moduleData, pos) -> node` — adds a module instance node
  - `toYAML() -> object` — serializes current graph state to YAML format

- [ ] **Step 1: Create graph-manager.js**

Create `frontend/src/core/graph-manager.js`:
```js
class GraphManager {
  constructor(typeSystem) {
    this._typeSystem = typeSystem;
    this._graph = null;
    this._canvas = null;
  }

  setCanvas(canvas) {
    this._canvas = canvas;
    this._graph = canvas.graph;
  }

  newGraph(name) {
    this._graph.clear();
    this._graph.extra = { name: name };
    if (this._canvas) {
      this._canvas.draw(true, true);
    }
    return this._graph;
  }

  async loadGraph(path) {
    const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(path)}`);
    if (!resp.ok) throw new Error('Failed to load graph');
    const { data } = await resp.json();

    this._graph.clear();

    // Add module instance nodes
    const nodes = data.nodes || [];
    const nodeMap = {};
    for (const n of nodes) {
      const node = this._createNodeFromData(n);
      nodeMap[n.id] = node;
    }

    // Add connections
    const connections = data.connections || [];
    for (const conn of connections) {
      this._addConnection(conn, nodeMap);
    }

    this._graph.extra = {
      path: path,
      meta: data.meta || {},
      properties: data.properties || {},
      ports: data.ports || []
    };

    if (this._canvas) {
      this._canvas.draw(true, true);
    }

    return this._graph;
  }

  _createNodeFromData(nodeData) {
    const node = LiteGraph.createNode('rtl/module');
    node.title = nodeData.id;
    node._module_ref = nodeData.ref || '';
    node._module_data = nodeData;
    node.properties = nodeData.properties || {};

    // Load ref module's port list if available (async, but we do best-effort)
    if (nodeData.ref) {
      this._loadRefPorts(node, nodeData.ref);
    }

    this._graph.add(node);
    return node;
  }

  async _loadRefPorts(node, refPath) {
    try {
      const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(refPath)}`);
      if (!resp.ok) return;
      const { data } = await resp.json();
      node._subgraph_data = data;
      node.setPortsFromData(data);
      if (this._canvas) {
        this._canvas.draw(true, true);
      }
    } catch (e) {
      console.warn('Failed to load ref ports for', refPath, e);
    }
  }

  _addConnection(conn, nodeMap) {
    const fromNode = nodeMap[conn.from.node];
    const fromPort = this._findPortIndex(fromNode, 'outputs', conn.from.port);
    if (fromNode && fromPort >= 0) {
      for (const to of conn.to) {
        const toNode = nodeMap[to.node];
        const toPort = this._findPortIndex(toNode, 'inputs', to.port);
        if (toNode && toPort >= 0) {
          fromNode.connect(fromPort, toNode, toPort);
        }
      }
    }
  }

  _findPortIndex(node, slotType, portName) {
    const slots = node[slotType] || [];
    for (let i = 0; i < slots.length; i++) {
      if (slots[i].name === portName) return i;
    }
    return -1;
  }

  async saveGraph(path) {
    const yaml = this.toYAML();
    const resp = await fetch('/api/graph/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path, data: yaml })
    });
    if (!resp.ok) throw new Error('Failed to save graph');
    this._graph.extra.path = path;
    return true;
  }

  toYAML() {
    const data = {
      meta: this._graph.extra.meta || { name: '', description: '', test_method: '' },
      properties: this._graph.extra.properties || {},
      ports: this._graph.extra.ports || [],
      nodes: [],
      connections: []
    };

    // Serialize nodes
    for (const node of this._graph._nodes) {
      if (node.type === 'rtl/module') {
        data.nodes.push({
          id: node.title,
          ref: node._module_ref || '',
          description: node._module_data ? node._module_data.description : '',
          properties: node.properties || {}
        });
      }
    }

    // Serialize connections
    const linkMap = {};
    for (const node of this._graph._nodes) {
      for (const input of (node.inputs || [])) {
        if (input.link !== undefined && input.link !== null) {
          const link = this._graph.links[input.link];
          if (link) {
            const key = `${link.origin_id}:${link.origin_slot}`;
            if (!linkMap[key]) linkMap[key] = [];
            linkMap[key].push({ node: node.title || String(node.id), port: input.name });
          }
        }
      }
    }
    for (const [fromKey, toList] of Object.entries(linkMap)) {
      const [fromId, fromSlot] = fromKey.split(':');
      const fromNode = this._graph._nodes.find(n => String(n.id) === fromId);
      data.connections.push({
        from: { node: fromNode ? fromNode.title : fromId, port: fromNode ? fromNode.outputs[parseInt(fromSlot)].name : fromSlot },
        to: toList
      });
    }

    return data;
  }
}

export { GraphManager };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/core/graph-manager.js && git commit -m "feat: add graph manager for load/save and YAML serialization"
```

---

### Task 14: Project (Frontend)

**Files:**
- Create: `frontend/src/core/project.js`

**Interfaces:**
- Produces: `Project` class
  - `create(path, name) -> Promise`
  - `open(path) -> Promise`
  - `save() -> Promise`
  - `getTrees() -> array`
  - `getConfig() -> object`

- [ ] **Step 1: Create project.js**

Create `frontend/src/core/project.js`:
```js
class Project {
  constructor() {
    this._config = null;
    this._trees = [];
    this._projectPath = '';
  }

  async create(path, name) {
    const resp = await fetch('/api/project/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, name })
    });
    if (!resp.ok) throw new Error('Failed to create project');
    const data = await resp.json();
    this._config = data.project;
    this._trees = data.trees;
    this._projectPath = path;
  }

  async open(path) {
    const resp = await fetch('/api/project/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path })
    });
    if (!resp.ok) throw new Error('Failed to open project');
    const data = await resp.json();
    this._config = data.project;
    this._trees = data.trees;
    this._projectPath = path;
  }

  async save() {
    if (!this._config) throw new Error('No project open');
    const resp = await fetch('/api/project/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: this._config })
    });
    if (!resp.ok) throw new Error('Failed to save project');
  }

  getTrees() { return this._trees; }
  getConfig() { return this._config; }
  getPath() { return this._projectPath; }
  isOpen() { return !!this._config; }
}

export { Project };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/core/project.js && git commit -m "feat: add frontend project class"
```

---

### Task 15: API Client Service

**Files:**
- Create: `frontend/src/services/api.js`

**Interfaces:**
- Produces: API wrapper object with typed methods for all backend endpoints

- [ ] **Step 1: Create api.js**

Create `frontend/src/services/api.js`:
```js
const API = {
  // Project
  createProject(path, name) {
    return this._post('/api/project/create', { path, name });
  },
  openProject(path) {
    return this._post('/api/project/open', { path });
  },
  saveProject(config) {
    return this._post('/api/project/save', { config });
  },
  getTrees() {
    return this._get('/api/project/trees');
  },
  createTree(name) {
    return this._post('/api/project/tree/create', { name });
  },

  // Graph
  loadGraph(path) {
    return this._get(`/api/graph/load?path=${encodeURIComponent(path)}`);
  },
  saveGraph(path, data) {
    return this._post('/api/graph/save', { path, data });
  },
  validateGraph(path) {
    return this._post('/api/graph/validate', { path });
  },
  deleteGraph(path) {
    return this._del(`/api/graph/delete?path=${encodeURIComponent(path)}`);
  },

  // Types
  listTypes() {
    return this._get('/api/types/list');
  },
  saveTypes(types) {
    return this._post('/api/types/save', { types });
  },
  checkTypes(from, to) {
    return this._get(`/api/types/check?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`);
  },

  // Build
  startBuild(targetNode, scope, mode, includeTestbench) {
    return this._post('/api/build', { target_node: targetNode, scope, mode, include_testbench: includeTestbench });
  },
  getBuildStatus(taskId) {
    return this._get(`/api/build/status/${taskId}`);
  },
  getBuildOutput(taskId) {
    return this._get(`/api/build/output/${taskId}`);
  },

  // Git
  commit(message) {
    return this._post('/api/git/commit', { message });
  },
  getGitLog(count) {
    return this._get(`/api/git/log?count=${count || 50}`);
  },
  checkoutGit(hash) {
    return this._post('/api/git/checkout', { hash });
  },

  // LLM Config
  getLLMConfig() {
    return this._get('/api/llm/config');
  },
  updateLLMConfig(config) {
    return this._post('/api/llm/config', config);
  },

  // Helpers
  async _get(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`GET ${url} failed: ${resp.status}`);
    return resp.json();
  },
  async _post(url, body) {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    if (!resp.ok) throw new Error(`POST ${url} failed: ${resp.status}`);
    return resp.json();
  },
  async _del(url) {
    const resp = await fetch(url, { method: 'DELETE' });
    if (!resp.ok) throw new Error(`DELETE ${url} failed: ${resp.status}`);
    return resp.json();
  }
};

export { API };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/api.js && git commit -m "feat: add API client service"
```

---

## Phase 4: Frontend UI

### Task 16: IDE Layout & Global Helpers

**Files:**
- Create: `frontend/src/ui/toast.js`
- Modify: `frontend/src/main.js` (register globals before App)

- [ ] **Step 1: Create toast utility**

Create `frontend/src/ui/toast.js`:
```js
function showToast(message, type) {
  type = type || 'info';
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = message;
  document.body.appendChild(el);
  setTimeout(function() {
    el.remove();
  }, 3000);
}

window.__showToast = showToast;
export { showToast };
```

- [ ] **Step 2: Update main.js**

Modify `frontend/src/main.js`:
```js
import 'litegraph.js';
import './nodes/rtl-module.js';
import './ui/toast.js';
import { App } from './app.js';

document.addEventListener('DOMContentLoaded', () => {
  window.__app = new App();
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/ui/toast.js frontend/src/main.js && git commit -m "feat: add toast notification utility"
```

---

### Task 17: Toolbar

**Files:**
- Create: `frontend/src/ui/toolbar.js`

**Interfaces:**
- Produces: `Toolbar` class with `init(container)` method
  - Buttons: New Project, Open Project, Save, Add Subgraph, Delete Selected, Build, Type Editor
  - Separators between groups

- [ ] **Step 1: Create toolbar.js**

Create `frontend/src/ui/toolbar.js`:
```js
class Toolbar {
  constructor(app) {
    this._app = app;
  }

  init(container) {
    this._el = container;

    this._addButton('New', () => this._app.showNewProjectDialog());
    this._addButton('Open', () => this._app.showOpenProjectDialog());
    this._addButton('Save', () => this._app.saveCurrentGraph());
    this._addSeparator();
    this._addButton('Add Subgraph', () => this._app.addSubgraphNode());
    this._addButton('Delete', () => this._app.deleteSelectedNodes());
    this._addSeparator();
    this._addButton('Zoom In', () => this._app.zoomIn());
    this._addButton('Zoom Out', () => this._app.zoomOut());
    this._addButton('Fit', () => this._app.zoomToFit());
    this._addSeparator();
    this._addButton('Build', () => this._app.showBuildDialog());
    this._addButton('Types', () => this._app.showTypeEditor());
  }

  _addButton(label, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    this._el.appendChild(btn);
    return btn;
  }

  _addSeparator() {
    const sep = document.createElement('span');
    sep.className = 'separator';
    this._el.appendChild(sep);
  }
}

export { Toolbar };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/ui/toolbar.js && git commit -m "feat: add toolbar component"
```

---

### Task 18: Project Panel (Left Panel)

**Files:**
- Create: `frontend/src/ui/project-panel.js`

**Interfaces:**
- Produces: `ProjectPanel` class with `init(container)` and `refresh(treeData)` methods

- [ ] **Step 1: Create project-panel.js**

Create `frontend/src/ui/project-panel.js`:
```js
class ProjectPanel {
  constructor(app) {
    this._app = app;
    this._el = null;
    this._selectedPath = null;
  }

  init(container) {
    this._el = container;
  }

  refresh(trees) {
    if (!this._el) return;
    this._el.innerHTML = '';

    const treesList = trees || [];
    for (const treeName of treesList) {
      const treeHeader = document.createElement('div');
      treeHeader.className = 'tree-item';
      treeHeader.style.fontWeight = 'bold';
      treeHeader.textContent = treeName + '/';
      treeHeader.addEventListener('click', () => this._toggleTree(treeName, treeHeader));
      this._el.appendChild(treeHeader);
    }
  }

  _toggleTree(treeName, header) {
    // Remove existing children
    let next = header.nextSibling;
    while (next && next.classList && next.classList.contains('tree-child')) {
      const toRemove = next;
      next = next.nextSibling;
      toRemove.remove();
    }

    // Load and display children
    const container = document.createElement('div');
    container.className = 'tree-child';
    container.style.paddingLeft = '16px';
    header.parentNode.insertBefore(container, header.nextSibling);

    this._loadDirectory(treeName, container);
  }

  async _loadDirectory(dirPath, container) {
    try {
      const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(dirPath)}`);
      // For directories, we'll try listing via project API
    } catch (e) {
      // Fallback: show placeholder
      container.textContent = 'Loading...';
    }

    // Manual tree structure: scan known files
    const projectPath = this._app.getProjectPath();
    if (projectPath) {
      // Show top-level yaml files from trees
      try {
        const treesResp = await fetch('/api/project/trees');
        const treesData = await treesResp.json();
        container.innerHTML = '';
        for (const tree of (treesData.trees || [])) {
          // We show a simplified tree from known data
          const item = document.createElement('div');
          item.className = 'tree-item';
          item.textContent = tree + '.yaml';
          item.draggable = true;
          item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('text/plain', tree + '/' + tree + '.yaml');
          });
          item.addEventListener('click', () => this._app.openGraph(tree + '/' + tree + '.yaml'));
          container.appendChild(item);
        }
      } catch (e) {
        container.textContent = 'Failed to load tree';
      }
    }
  }
}

export { ProjectPanel };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/ui/project-panel.js && git commit -m "feat: add project panel component"
```

---

### Task 19: Property Panel (Right Panel)

**Files:**
- Create: `frontend/src/ui/property-panel.js`

**Interfaces:**
- Produces: `PropertyPanel` class with `init(container)` and `showNodeProperties(node)` / `showPortProperties(slot, direction)` / `clear()` methods

- [ ] **Step 1: Create property-panel.js**

Create `frontend/src/ui/property-panel.js`:
```js
class PropertyPanel {
  constructor(app) {
    this._app = app;
    this._el = null;
  }

  init(container) {
    this._el = container;
  }

  clear() {
    this._el.innerHTML = '<div style="color:var(--text-dim); padding:16px; text-align:center;">Select a node or port</div>';
  }

  showNodeProperties(node) {
    this._el.innerHTML = '';

    this._addHeading('Module Instance');
    this._addField('Name', node.title || '', (v) => { node.title = v; });

    const data = node._module_data || {};
    this._addTextarea('Description', data.description || '', (v) => {
      data.description = v;
      node._module_data = data;
    });
    this._addTextarea('Test Method', data.test_method || '', (v) => {
      data.test_method = v;
      node._module_data = data;
    });

    this._addHeading('Ref');
    this._addField('Ref Path', node._module_ref || '', (v) => { node._module_ref = v; });

    this._addHeading('Properties');
    const props = node.properties || {};
    for (const [k, v] of Object.entries(props)) {
      this._addField(k, String(v), (newV) => { node.properties[k] = newV; });
    }
    this._addButton('+ Add Property', () => {
      const key = prompt('Property name:');
      if (key) {
        node.properties[key] = '';
        this.showNodeProperties(node);
        this._app.redraw();
      }
    });

    this._addHeading('Ports');
    const ports = [];
    for (let i = 0; i < (node.inputs || []).length; i++) {
      const p = node.inputs[i];
      ports.push({ dir: 'input', idx: i, name: p.name, data: p._port_data || {} });
    }
    for (let i = 0; i < (node.outputs || []).length; i++) {
      const p = node.outputs[i];
      ports.push({ dir: 'output', idx: i, name: p.name, data: p._port_data || {} });
    }
    for (const p of ports) {
      const row = document.createElement('div');
      row.className = 'tree-item';
      const cat = p.data.category || 'data';
      row.textContent = `${p.dir === 'input' ? '←' : '→'} ${p.name} [${cat}]`;
      row.addEventListener('click', () => this.showPortProperties(node, p.dir, p.idx));
      this._el.appendChild(row);
    }
  }

  showPortProperties(node, direction, slotIdx) {
    this._el.innerHTML = '';
    this._addHeading('Port Properties');

    const slots = direction === 'input' ? node.inputs : node.outputs;
    const slot = slots[slotIdx];
    const portData = slot._port_data || {};

    this._addField('Name', slot.name, (v) => { slot.name = v; });
    this._addSelect('Category', ['clock', 'reset', 'data'], portData.category || 'data', (v) => {
      portData.category = v;
      slot._port_data = portData;
      const color = node.getPortColor(v);
      slot.color_on = color;
      this._app.redraw();
    });
    this._addSelect('Direction', ['input', 'output'], direction, () => {});
    this._addField('Type', portData.type || '', (v) => { portData.type = v; slot._port_data = portData; });
    this._addField('Clock Domain', portData.clock_domain || '', (v) => { portData.clock_domain = v; slot._port_data = portData; });
    this._addField('Reset Domain', portData.reset_domain || '', (v) => { portData.reset_domain = v; slot._port_data = portData; });

    const resetType = portData.reset_type || 'async';
    this._addSelect('Reset Type', ['async', 'sync'], resetType, (v) => { portData.reset_type = v; slot._port_data = portData; });

    this._addButton('← Back to Node', () => this.showNodeProperties(node));
  }

  _addHeading(text) {
    const h = document.createElement('div');
    h.style.cssText = 'color:var(--text-dim); font-size:10px; text-transform:uppercase; margin: 12px 0 4px; border-top:1px solid #333; padding-top:8px;';
    h.textContent = text;
    this._el.appendChild(h);
  }

  _addField(label, value, onChange) {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const input = document.createElement('input');
    input.value = value;
    input.addEventListener('change', () => onChange(input.value));
    g.appendChild(lbl);
    g.appendChild(input);
    this._el.appendChild(g);
  }

  _addTextarea(label, value, onChange) {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const ta = document.createElement('textarea');
    ta.value = value;
    ta.addEventListener('change', () => onChange(ta.value));
    g.appendChild(lbl);
    g.appendChild(ta);
    this._el.appendChild(g);
  }

  _addSelect(label, options, selected, onChange) {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const sel = document.createElement('select');
    for (const opt of options) {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (opt === selected) o.selected = true;
      sel.appendChild(o);
    }
    sel.addEventListener('change', () => onChange(sel.value));
    g.appendChild(lbl);
    g.appendChild(sel);
    this._el.appendChild(g);
  }

  _addButton(label, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.style.cssText = 'margin-top:8px; width:100%;';
    btn.addEventListener('click', onClick);
    this._el.appendChild(btn);
  }
}

export { PropertyPanel };
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/ui/property-panel.js && git commit -m "feat: add property panel component"
```

---

### Task 20: Editor Dialogs (Type Editor, Build, Project)

**Files:**
- Create: `frontend/src/ui/type-editor.js`
- Create: `frontend/src/ui/dialogs.js`

- [ ] **Step 1: Create type-editor.js**

Create `frontend/src/ui/type-editor.js`:
```js
class TypeEditor {
  constructor(typeSystem, onClose) {
    this._ts = typeSystem;
    this._onClose = onClose;
  }

  show() {
    this._overlay = document.createElement('div');
    this._overlay.className = 'dialog-overlay';

    const dialog = document.createElement('div');
    dialog.className = 'dialog';
    dialog.style.width = '500px';
    dialog.innerHTML = '<h3>Type Definitions</h3>';

    const list = document.createElement('div');
    list.style.cssText = 'max-height:300px; overflow-y:auto; margin:8px 0;';

    const types = this._ts.getTypes();
    for (const [name, def] of Object.entries(types)) {
      const row = document.createElement('div');
      row.style.cssText = 'display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid #333;';
      row.innerHTML = `<span><strong>${name}</strong> — ${def.description || ''}</span>`;
      const delBtn = document.createElement('button');
      delBtn.textContent = '×';
      delBtn.style.cssText = 'background:#a33; border:none; color:#fff; padding:2px 6px; cursor:pointer; border-radius:2px;';
      delBtn.addEventListener('click', () => {
        this._ts.removeType(name);
        dialog.remove();
        this.show();
      });
      row.appendChild(delBtn);
      list.appendChild(row);
    }
    dialog.appendChild(list);

    // Add new type form
    const addForm = document.createElement('div');
    addForm.style.cssText = 'margin-top:8px; display:flex; gap:4px;';
    const nameInput = document.createElement('input');
    nameInput.placeholder = 'Type name';
    nameInput.style.cssText = 'flex:1; background:#2d2d2d; border:1px solid #444; color:#ccc; padding:4px;';
    const descInput = document.createElement('input');
    descInput.placeholder = 'Description';
    descInput.style.cssText = 'flex:1; background:#2d2d2d; border:1px solid #444; color:#ccc; padding:4px;';
    const addBtn = document.createElement('button');
    addBtn.textContent = 'Add';
    addBtn.addEventListener('click', () => {
      if (nameInput.value) {
        this._ts.addType(nameInput.value, { description: descInput.value, category: 'user' });
        dialog.remove();
        this.show();
      }
    });
    addForm.appendChild(nameInput);
    addForm.appendChild(descInput);
    addForm.appendChild(addBtn);
    dialog.appendChild(addForm);

    const actions = document.createElement('div');
    actions.className = 'dialog-actions';
    const saveBtn = document.createElement('button');
    saveBtn.textContent = 'Save';
    saveBtn.addEventListener('click', async () => {
      await this._save();
      this._close();
    });
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.addEventListener('click', () => this._close());
    actions.appendChild(saveBtn);
    actions.appendChild(closeBtn);
    dialog.appendChild(actions);

    this._overlay.appendChild(dialog);
    document.body.appendChild(this._overlay);
  }

  async _save() {
    try {
      await fetch('/api/types/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ types: this._ts.getTypes() })
      });
      showToast('Types saved');
    } catch (e) {
      showToast('Failed to save types: ' + e.message, 'error');
    }
  }

  _close() {
    if (this._overlay) this._overlay.remove();
    if (this._onClose) this._onClose();
  }
}

export { TypeEditor };
```

- [ ] **Step 2: Create dialogs.js**

Create `frontend/src/ui/dialogs.js`:
```js
function showDialog(title, contentHtml, buttons) {
  const overlay = document.createElement('div');
  overlay.className = 'dialog-overlay';

  const dialog = document.createElement('div');
  dialog.className = 'dialog';
  dialog.innerHTML = `<h3>${title}</h3>`;

  const body = document.createElement('div');
  body.innerHTML = contentHtml;
  dialog.appendChild(body);

  const actions = document.createElement('div');
  actions.className = 'dialog-actions';

  for (const btn of (buttons || [])) {
    const b = document.createElement('button');
    b.textContent = btn.label;
    b.addEventListener('click', () => {
      const result = btn.onClick(body);
      if (result !== false) {
        overlay.remove();
      }
    });
    actions.appendChild(b);
  }
  dialog.appendChild(actions);
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  return { overlay, body };
}

function showNewProjectDialog(onCreate) {
  showDialog('New Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path" placeholder="path/to/project"/></div>' +
    '<div class="property-group"><label>Project Name</label><input id="proj-name" placeholder="my_project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Create',
      onClick: (body) => {
        const path = body.querySelector('#proj-path').value;
        const name = body.querySelector('#proj-name').value;
        if (path && name && onCreate) onCreate(path, name);
      }
    }]
  );
}

function showOpenProjectDialog(onOpen) {
  showDialog('Open Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path-open" placeholder="path/to/project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Open',
      onClick: (body) => {
        const path = body.querySelector('#proj-path-open').value;
        if (path && onOpen) onOpen(path);
      }
    }]
  );
}

function showBuildDialog(onBuild) {
  showDialog('Build Configuration',
    '<div class="property-group"><label>Scope</label><select id="build-scope">' +
      '<option value="this">This module only</option>' +
      '<option value="descendants">This + descendants</option>' +
      '<option value="ancestors">This + ancestors</option>' +
      '<option value="all">Entire graph</option>' +
    '</select></div>' +
    '<div class="property-group"><label>Mode</label><select id="build-mode">' +
      '<option value="fresh">Fresh (no prior code)</option>' +
      '<option value="incremental">Incremental (with prior code)</option>' +
    '</select></div>' +
    '<div class="property-group"><label><input type="checkbox" id="build-tb" checked/> Include testbench</label></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Build',
      onClick: (body) => {
        if (onBuild) {
          onBuild({
            scope: body.querySelector('#build-scope').value,
            mode: body.querySelector('#build-mode').value,
            includeTestbench: body.querySelector('#build-tb').checked
          });
        }
      }
    }]
  );
}

export { showDialog, showNewProjectDialog, showOpenProjectDialog, showBuildDialog };
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/ui/type-editor.js frontend/src/ui/dialogs.js && git commit -m "feat: add type editor and dialog components"
```

---

## Phase 5: App Integration

### Task 21: App Controller

**Files:**
- Create: `frontend/src/app.js`

**Interfaces:**
- Produces: `App` class — wires together all frontend components
  - Creates IDE layout, initializes LGraph and LGraphCanvas
  - Instantiates TypeSystem, ConnectionValidator, GraphManager, Project
  - Wires Toolbar, ProjectPanel, PropertyPanel
  - Handles drag-and-drop from project panel to canvas
  - Handles node selection → property panel updates

- [ ] **Step 1: Create app.js**

Create `frontend/src/app.js`:
```js
import { TypeSystem } from './core/type-system.js';
import { ConnectionValidator } from './core/connection-validator.js';
import { GraphManager } from './core/graph-manager.js';
import { Project } from './core/project.js';
import { Toolbar } from './ui/toolbar.js';
import { ProjectPanel } from './ui/project-panel.js';
import { PropertyPanel } from './ui/property-panel.js';
import { TypeEditor } from './ui/type-editor.js';
import { showNewProjectDialog, showOpenProjectDialog, showBuildDialog } from './ui/dialogs.js';
import { API } from './services/api.js';

class App {
  constructor() {
    this._typeSystem = new TypeSystem();
    this._connectionValidator = new ConnectionValidator(this._typeSystem);
    window.__connectionValidator = this._connectionValidator;

    this._project = new Project();
    this._graphManager = new GraphManager(this._typeSystem);

    this._initLayout();
    this._initLiteGraph();
    this._initComponents();
  }

  _initLayout() {
    const app = document.getElementById('app');
    app.innerHTML = `
      <div id="toolbar"></div>
      <div id="main-area">
        <div id="project-panel"></div>
        <div id="canvas-container"></div>
        <div id="property-panel"></div>
      </div>
      <div id="statusbar">
        <span id="status-text">Ready</span>
        <span id="status-project">No project</span>
      </div>`;
  }

  _initLiteGraph() {
    const canvasEl = document.createElement('canvas');
    canvasEl.id = 'graph-canvas';
    canvasEl.width = 2000;
    canvasEl.height = 2000;
    document.getElementById('canvas-container').appendChild(canvasEl);

    const graph = new LiteGraph.LGraph();
    this._canvas = new LiteGraph.LGraphCanvas(canvasEl, graph);
    this._canvas.background_image = '';

    // Use spline links for cleaner look
    this._canvas.render_links_border = true;
    this._canvas.links_render_mode = LiteGraph.SPLINE_LINK;

    this._graphManager.setCanvas(this._canvas);

    // Node selection → property panel
    this._canvas.onNodeSelected = (node) => {
      this._propertyPanel.showNodeProperties(node);
    };
    this._canvas.onNodeDeselected = () => {
      this._propertyPanel.clear();
    };

    // Handle window resize
    const resizeCanvas = () => {
      const container = document.getElementById('canvas-container');
      canvasEl.width = container.clientWidth;
      canvasEl.height = container.clientHeight;
      if (this._canvas) this._canvas.draw(true, true);
    };
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    this._canvas.draw(true, true);
  }

  _initComponents() {
    this._toolbar = new Toolbar(this);
    this._toolbar.init(document.getElementById('toolbar'));

    this._projectPanel = new ProjectPanel(this);
    this._projectPanel.init(document.getElementById('project-panel'));

    this._propertyPanel = new PropertyPanel(this);
    this._propertyPanel.init(document.getElementById('property-panel'));
    this._propertyPanel.clear();

    // Load type system
    this._typeSystem.loadFromServer();
  }

  // === Toolbar actions ===

  async showNewProjectDialog() {
    showNewProjectDialog(async (path, name) => {
      try {
        await this._project.create(path, name);
        this._updateStatus();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project created: ' + name);
      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async showOpenProjectDialog() {
    showOpenProjectDialog(async (path) => {
      try {
        await this._project.open(path);
        this._updateStatus();
        this._projectPanel.refresh(this._project.getTrees());
        await this._typeSystem.loadFromServer();
        showToast('Project opened');
      } catch (e) {
        showToast('Error: ' + e.message, 'error');
      }
    });
  }

  async saveCurrentGraph() {
    if (!this._project.isOpen()) {
      showToast('No project open', 'error');
      return;
    }
    const path = this._graphManager._graph.extra.path;
    if (!path) {
      showToast('No graph loaded', 'error');
      return;
    }
    try {
      await this._graphManager.saveGraph(path);
      this._updateStatus();
      showToast('Graph saved');
    } catch (e) {
      showToast('Save failed: ' + e.message, 'error');
    }
  }

  async openGraph(path) {
    try {
      await this._graphManager.loadGraph(path);
      this._updateStatus();
      this._propertyPanel.clear();
      showToast('Opened: ' + path);
    } catch (e) {
      showToast('Open failed: ' + e.message, 'error');
    }
  }

  addSubgraphNode() {
    const node = LiteGraph.createNode('rtl/module');
    node.title = 'new_module';
    node.pos = [200, 200];
    this._graphManager._graph.add(node);
    if (this._canvas) this._canvas.draw(true, true);
  }

  deleteSelectedNodes() {
    if (!this._canvas) return;
    const selected = this._canvas.selected_nodes || {};
    for (const id of Object.keys(selected)) {
      const node = selected[id];
      node.graph.remove(node);
    }
    this._canvas.deselectAllNodes();
    this._canvas.draw(true, true);
  }

  zoomIn() {
    if (this._canvas) {
      this._canvas.zoom(1.2, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
    }
  }

  zoomOut() {
    if (this._canvas) {
      this._canvas.zoom(0.8, [this._canvas.canvas.width / 2, this._canvas.canvas.height / 2]);
      this._canvas.draw(true, true);
    }
  }

  zoomToFit() {
    if (this._canvas) this._canvas.zoomToFit();
  }

  showBuildDialog() {
    const currentPath = this._graphManager._graph.extra.path || 'top/top.yaml';
    showBuildDialog(async (opts) => {
      try {
        const resp = await API.startBuild(currentPath, opts.scope, opts.mode, opts.includeTestbench);
        showToast('Build started: ' + resp.task_id);
        this._pollBuild(resp.task_id);
      } catch (e) {
        showToast('Build failed: ' + e.message, 'error');
      }
    });
  }

  async _pollBuild(taskId) {
    const self = this;
    const interval = setInterval(async () => {
      try {
        const status = await API.getBuildStatus(taskId);
        if (status.status === 'done') {
          clearInterval(interval);
          showToast('Build complete!');
          self._updateStatus();
        } else if (status.status === 'failed') {
          clearInterval(interval);
          showToast('Build failed: ' + status.error, 'error');
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 2000);
  }

  showTypeEditor() {
    const editor = new TypeEditor(this._typeSystem, () => {});
    editor.show();
  }

  redraw() {
    if (this._canvas) this._canvas.draw(true, true);
  }

  getProjectPath() {
    return this._project.getPath();
  }

  _updateStatus() {
    const statusEl = document.getElementById('status-text');
    const projEl = document.getElementById('status-project');
    if (this._project.isOpen()) {
      projEl.textContent = 'Project: ' + this._project.getConfig().name;
    }
    if (this._graphManager._graph.extra.path) {
      statusEl.textContent = 'Graph: ' + this._graphManager._graph.extra.path;
    }
  }
}

export { App };
```

- [ ] **Step 2: Verify build**

```bash
cd frontend && npx vite build 2>&1
```
Expected: Build completes successfully.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app.js && git commit -m "feat: add app controller wiring all components together"
```

---

### Task 22: Integration Test & Final Assembly

**Files:**
- Modify: `backend/app.py` (ensure all blueprints registered)

- [ ] **Step 1: Verify all backend blueprints are registered**

Read `backend/app.py` and ensure these lines exist:
```python
from api.types import types_bp
app.register_blueprint(types_bp, url_prefix='/api/types')

from api.graph import graph_bp
app.register_blueprint(graph_bp, url_prefix='/api/graph')

from api.project import project_bp
app.register_blueprint(project_bp, url_prefix='/api/project')

from api.git import git_bp
app.register_blueprint(git_bp, url_prefix='/api/git')

from api.build import build_bp
app.register_blueprint(build_bp, url_prefix='/api/build')
```

- [ ] **Step 2: End-to-end test with Flask test client**

```bash
cd backend && python -c "
import tempfile, os, json
from app import app
from services.file_manager import FileManager

d = tempfile.mkdtemp()
app.config['PROJECT_ROOT'] = d
app.config['FILE_MANAGER'] = FileManager(d)

with app.test_client() as c:
    # Create project
    r = c.post('/api/project/create', json={'path': 'test_proj', 'name': 'test'})
    assert r.status_code == 200, f'create failed: {r.json}'

    # List types
    r = c.get('/api/types/list')
    assert r.status_code == 200 and 'logic' in r.json.get('types', {})

    # Load default graph
    r = c.get('/api/graph/load?path=top/test.yaml')
    assert r.status_code == 200
    data = r.json['data']
    assert data['meta']['name'] == 'test'

    # Add a node to the graph
    data['nodes'].append({
        'id': 'adder_inst',
        'ref': 'library/adder/adder.yaml',
        'description': 'adder module',
        'properties': {}
    })

    # Create the referenced graph
    adder_graph = {
        'meta': {'name': 'adder', 'description': '32-bit adder', 'test_method': ''},
        'properties': {},
        'ports': [
            {'name': 'a', 'direction': 'input', 'category': 'data', 'type': 'logic[31:0]', 'clock_domain': 'clk'},
            {'name': 'b', 'direction': 'input', 'category': 'data', 'type': 'logic[31:0]', 'clock_domain': 'clk'},
            {'name': 'sum', 'direction': 'output', 'category': 'data', 'type': 'logic[31:0]', 'clock_domain': 'clk'}
        ],
        'nodes': [],
        'connections': []
    }
    c.post('/api/graph/save', json={'path': 'library/adder/adder.yaml', 'data': adder_graph})

    # Save graph
    r = c.post('/api/graph/save', json={'path': 'top/test.yaml', 'data': data})
    assert r.status_code == 200

    # Validate
    r = c.post('/api/graph/validate', json={'path': 'top/test.yaml'})
    assert r.json['valid'] == True, f'validation failed: {r.json[\"errors\"]}'

    # Git commit
    r = c.post('/api/git/commit', json={'message': 'e2e test'})
    assert r.status_code == 200

print('All integration tests passed')
"
```
Expected: "All integration tests passed"

- [ ] **Step 3: Verify frontend build**

```bash
cd frontend && npx vite build 2>&1
```
Expected: Build completes, output in `dist/`.

- [ ] **Step 4: Commit**

```bash
git add backend/app.py frontend/dist/ 2>/dev/null; git commit -m "feat: final integration and verification"
```

---
