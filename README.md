# RTL Blueprint

Visual digital circuit design tool — create multi-level module blueprints on a graph canvas, then compile them via LLM into synthesizable Bluespec SystemVerilog.

## Architecture

- **Frontend:** Vite-bundled vanilla JS (ES modules) with litegraph.js for graph editing
- **Backend:** Flask REST API for graph CRUD, project management, Git versioning, and LLM orchestration
- **Persistence:** YAML files (one per graph), directory hierarchy mirrors module hierarchy
- **LLM:** Claude Code CLI (primary) or OpenAI API (fallback) for RTL generation

## Prerequisites

- [Python](https://www.python.org/downloads/) 3.12+ with pip
- [Node.js](https://nodejs.org/) 18+ with npm

## Quick Start

### Backend

```bash
# From project root
cd backend
python -m pip install -r requirements.txt
python app.py
```

The API server starts at `http://localhost:5000`.

### Frontend

```bash
# From project root
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`.

### One-Click

**Windows:** Double-click `start-server.bat` in File Explorer, or run from terminal:

```bash
start-server.bat
```

This installs dependencies and starts both backend and frontend.

## Project Structure

```
.
├── 3rd/                    # Third-party libraries (litegraph.js submodule)
├── backend/
│   ├── api/                # Flask blueprints (graph, project, git, build, types)
│   ├── services/           # Business logic (FileManager, LLMAgent, RTLCompiler)
│   └── app.py              # Flask application entry point
├── frontend/
│   ├── src/
│   │   ├── core/           # Core logic (TypeSystem, etc.)
│   │   ├── nodes/          # litegraph.js custom nodes
│   │   ├── services/       # API client
│   │   ├── ui/             # UI components
│   │   └── main.js         # Frontend entry point
│   └── vite.config.js
└── docs/                   # Design docs and specs
```

## License

MIT
