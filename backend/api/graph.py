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
