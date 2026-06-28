import uuid
import time
import threading
from flask import Blueprint, request, jsonify, current_app

build_bp = Blueprint('build', __name__)

_tasks = {}
_TASK_TTL_SECONDS = 3600  # 1 hour


def _cleanup_old_tasks():
    """Remove completed/failed tasks older than TTL."""
    now = time.time()
    stale = [tid for tid, t in _tasks.items()
             if t['status'] in ('done', 'failed')
             and now - t.get('_created', 0) > _TASK_TTL_SECONDS]
    for tid in stale:
        del _tasks[tid]

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
    _cleanup_old_tasks()
    task_id = str(uuid.uuid4())[:8]
    _tasks[task_id] = {
        'id': task_id,
        'status': 'pending',
        'target_node': body.get('target_node', ''),
        'scope': body.get('scope', 'this'),
        'mode': body.get('mode', 'fresh'),
        'include_testbench': body.get('include_testbench', False),
        'progress': {},
        '_created': time.time()
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
