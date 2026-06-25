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
