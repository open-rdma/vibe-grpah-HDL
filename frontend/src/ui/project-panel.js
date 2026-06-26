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
    let next = header.nextSibling;
    while (next && next.classList && next.classList.contains('tree-child')) {
      const toRemove = next;
      next = next.nextSibling;
      toRemove.remove();
    }

    const container = document.createElement('div');
    container.className = 'tree-child';
    container.style.paddingLeft = '16px';
    header.parentNode.insertBefore(container, header.nextSibling);

    this._loadDirectory(treeName, container);
  }

  async _loadDirectory(dirPath, container) {
    try {
      const resp = await fetch(`/api/graph/load?path=${encodeURIComponent(dirPath)}`);
    } catch (e) {
      container.textContent = 'Loading...';
    }

    const projectPath = this._app.getProjectPath();
    if (projectPath) {
      try {
        const treesResp = await fetch('/api/project/trees');
        const treesData = await treesResp.json();
        container.innerHTML = '';
        for (const tree of (treesData.trees || [])) {
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
