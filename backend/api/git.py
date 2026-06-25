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
