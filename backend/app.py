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

from api.graph import graph_bp
app.register_blueprint(graph_bp, url_prefix='/api/graph')

from api.project import project_bp
app.register_blueprint(project_bp, url_prefix='/api/project')

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
