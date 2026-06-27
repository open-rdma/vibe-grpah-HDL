import os
import subprocess
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=None)
CORS(app)

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'frontend')
FRONTEND_DIST = os.path.join(FRONTEND_DIR, 'dist')

# Snapshot the original working directory as the projects base before any
# project open replaces PROJECT_ROOT.  Used by open_project to resolve
# relative paths consistently regardless of which project is currently open.
PROJECTS_BASE = os.getcwd()
app.config['PROJECTS_BASE'] = PROJECTS_BASE


def build_frontend():
    """Run `npm run build` to produce frontend/dist. Skip if node is unavailable."""
    npm = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    try:
        subprocess.run([npm, 'run', 'build'], cwd=FRONTEND_DIR, check=True, timeout=120)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f'[warn] Frontend build skipped: {e}', flush=True)
    except subprocess.TimeoutExpired:
        print('[warn] Frontend build timed out', flush=True)


build_frontend()

from services.file_manager import FileManager

@app.before_request
def setup_fm():
    project_root = app.config.get('PROJECT_ROOT', os.getcwd())
    if 'FILE_MANAGER' not in app.config:
        app.config['FILE_MANAGER'] = FileManager(project_root)

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

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIST, 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'assets'), filename)

@app.route('/vendor/<path:filename>')
def serve_vendor(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'vendor'), filename)

@app.route('/src/<path:filename>')
def serve_src(filename):
    return send_from_directory(os.path.join(FRONTEND_DIST, 'src'), filename)

@app.route('/health')
def health():
    return {"status": "ok"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
