import type { App } from '../app';
import { API } from '../services/api';
import { showToast } from './toast';
import { createEmptyGraphData } from '../core/graph-manager';

class ProjectPanel {
  _app: App;
  _el: HTMLElement | null;
  _selectedPath: string | null;
  _contextMenu: HTMLElement | null;

  constructor(app: App) {
    this._app = app;
    this._el = null;
    this._selectedPath = null;
    this._contextMenu = null;
  }

  init(container: HTMLElement): void {
    this._el = container;
    document.addEventListener('click', () => this._hideContextMenu());
    document.addEventListener('keydown', (e: KeyboardEvent) => {
      if (e.key === 'Escape') this._hideContextMenu();
    });
  }

  refresh(trees: string[]): void {
    if (!this._el) return;
    this._el.innerHTML = '';

    if (!this._app._project.isOpen()) {
      this._el.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-dim);text-align:center;padding:24px;">
        <div style="font-size:14px;margin-bottom:4px;">No project open.</div>
        <div style="font-size:11px;">Use New or Open to get started.</div>
      </div>`;
      return;
    }

    const treesList = trees || [];
    for (const treeName of treesList) {
      const treeHeader = document.createElement('div');
      treeHeader.className = 'tree-item';
      treeHeader.style.fontWeight = 'bold';
      treeHeader.textContent = treeName + '/';
      treeHeader.addEventListener('click', () => this._toggleTree(treeName, treeHeader));
      treeHeader.addEventListener('contextmenu', (e: MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        this._showContextMenu(e, treeName, 'tree');
      });
      this._el.appendChild(treeHeader);
    }
  }

  _isElement(node: Node | null): node is HTMLElement {
    return node !== null && node.nodeType === 1;
  }

  _removeChildSiblings(parent: HTMLElement): void {
    let next = parent.nextSibling;
    while (this._isElement(next) && next.classList.contains('tree-child')) {
      const toRemove = next;
      next = next.nextSibling;
      toRemove.remove();
    }
  }

  _toggleTree(treeName: string, header: HTMLElement): void {
    this._removeChildSiblings(header);

    const container = document.createElement('div');
    container.className = 'tree-child';
    container.style.paddingLeft = '16px';
    header.parentNode!.insertBefore(container, header.nextSibling);

    this._loadDirectory(treeName, container);
  }

  async _loadDirectory(dirPath: string, container: HTMLElement): Promise<void> {
    container.innerHTML = '<span style="color:var(--text-dim)">Loading...</span>';

    try {
      const resp = await fetch(`/api/graph/dir?path=${encodeURIComponent(dirPath)}`);
      if (!resp.ok) throw new Error('Failed to load directory');
      const data = await resp.json();
      const entries = data.entries || [];

      container.innerHTML = '';
      if (entries.length === 0) {
        container.innerHTML = '<span style="color:var(--text-dim)">(empty)</span>';
        return;
      }

      for (const entry of entries) {
        if (entry.is_graph || entry.name.endsWith('.yaml')) {
          const item = document.createElement('div');
          item.className = 'tree-item';
          item.textContent = entry.name;
          item.draggable = true;
          item.addEventListener('dragstart', (e: DragEvent) => {
            e.dataTransfer!.setData('text/plain', entry.path);
          });
          item.addEventListener('click', () => this._app.openGraph(entry.path));
          item.addEventListener('contextmenu', (e: MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            this._showContextMenu(e, entry.path, 'graph');
          });
          container.appendChild(item);
        } else if (entry.type === 'dir') {
          const item = document.createElement('div');
          item.className = 'tree-item';
          item.style.color = 'var(--text-dim)';
          item.textContent = entry.name + '/';
          item.addEventListener('click', () => {
            item.classList.toggle('expanded');
            this._removeChildSiblings(item);
            if (item.classList.contains('expanded')) {
              const subContainer = document.createElement('div');
              subContainer.className = 'tree-child';
              subContainer.style.paddingLeft = '16px';
              item.parentNode!.insertBefore(subContainer, item.nextSibling);
              this._loadDirectory(entry.path, subContainer);
            }
          });
          item.addEventListener('contextmenu', (e: MouseEvent) => {
            e.preventDefault();
            e.stopPropagation();
            this._showContextMenu(e, entry.path, 'dir');
          });
          container.appendChild(item);
        }
      }
    } catch (e) {
      container.innerHTML = '<span style="color:var(--error)">Failed to load</span>';
    }
  }

  _showContextMenu(e: MouseEvent, path: string, type: 'tree' | 'dir' | 'graph'): void {
    this._hideContextMenu();

    const menu = document.createElement('div');
    menu.className = 'context-menu';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';

    if (type === 'graph') {
      this._addContextItem(menu, 'Delete Graph', () => this._deleteGraph(path));
    } else {
      this._addContextItem(menu, 'New Graph', () => this._newGraph(path));
      if (type === 'tree') {
        this._addContextItem(menu, 'New Tree', () => this._newTree());
      }
    }

    document.body.appendChild(menu);
    this._contextMenu = menu;

    // Position correction if menu extends beyond viewport
    const rect = menu.getBoundingClientRect();
    if (rect.right > window.innerWidth) {
      menu.style.left = (e.clientX - rect.width) + 'px';
    }
    if (rect.bottom > window.innerHeight) {
      menu.style.top = (e.clientY - rect.height) + 'px';
    }
  }

  _addContextItem(menu: HTMLElement, label: string, action: () => void): void {
    const item = document.createElement('div');
    item.className = 'context-menu-item';
    item.textContent = label;
    item.addEventListener('click', () => {
      this._hideContextMenu();
      action();
    });
    menu.appendChild(item);
  }

  _hideContextMenu(): void {
    if (this._contextMenu) {
      this._contextMenu.remove();
      this._contextMenu = null;
    }
  }

  async _newGraph(parentPath: string): Promise<void> {
    const name = prompt('Graph name (without .yaml):');
    if (!name) return;
    const graphPath = parentPath.replace(/\/$/, '') + '/' + name + '.yaml';
    try {
      const emptyGraph = createEmptyGraphData(name);
      await API.saveGraph(graphPath, emptyGraph);
      this._app._projectPanel.refresh(this._app._project.getTrees());
      showToast('Graph created: ' + name);
    } catch (e: any) {
      showToast('Failed to create graph: ' + e.message, 'error');
    }
  }

  async _deleteGraph(path: string): Promise<void> {
    if (!confirm('Delete graph "' + path + '"?')) return;
    try {
      await API.deleteGraph(path);
      this._app._projectPanel.refresh(this._app._project.getTrees());
      showToast('Graph deleted: ' + path);
    } catch (e: any) {
      showToast('Failed to delete graph: ' + e.message, 'error');
    }
  }

  async _newTree(): Promise<void> {
    const name = prompt('New tree name:');
    if (!name) return;
    try {
      await API.createTree(name);
      this._app._projectPanel.refresh(this._app._project.getTrees());
      showToast('Tree created: ' + name);
    } catch (e: any) {
      showToast('Failed to create tree: ' + e.message, 'error');
    }
  }
}

export { ProjectPanel };
