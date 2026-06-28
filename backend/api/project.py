import os
from flask import Blueprint, request, jsonify, current_app
from services.file_manager import FileManager

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

    base = current_app.config['PROJECTS_BASE']
    project_root = os.path.abspath(os.path.join(base, project_path))
    os.makedirs(project_root, exist_ok=True)

    app = current_app
    app.config['PROJECT_ROOT'] = project_root
    app.config['FILE_MANAGER'] = FileManager(project_root)
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

    base = current_app.config['PROJECTS_BASE']
    project_root = os.path.abspath(os.path.join(base, project_path))
    if not os.path.exists(os.path.join(project_root, 'project.yaml')):
        return jsonify({'error': 'Not a valid project'}), 400

    current_app.config['PROJECT_ROOT'] = project_root
    current_app.config['FILE_MANAGER'] = FileManager(project_root)
    fm = current_app.config['FILE_MANAGER']

    config = fm.read_yaml('project.yaml')
    return jsonify({'ok': True, 'project': config, 'trees': config.get('trees', [])})

@project_bp.route('/close', methods=['POST'])
def close_project():
    """Reset project state to base (no project open)."""
    base = current_app.config['PROJECTS_BASE']
    current_app.config['PROJECT_ROOT'] = base
    current_app.config['FILE_MANAGER'] = FileManager(base)
    return jsonify({'ok': True})

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
