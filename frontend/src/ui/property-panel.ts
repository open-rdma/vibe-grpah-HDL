import type { App } from '../app';
import type { PortData } from '../types/graph-types';
import { showToast } from './toast';
import { createDefaultPort } from '../constants';

class PropertyPanel {
  _app: App;
  _el: HTMLElement | null;

  constructor(app: App) {
    this._app = app;
    this._el = null;
  }

  init(container: HTMLElement): void {
    this._el = container;
  }

  clear(): void {
    if (!this._app._project.isOpen()) {
      this._el!.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:var(--text-dim);text-align:center;padding:24px;">
        <div style="font-size:14px;margin-bottom:4px;">No project open.</div>
        <div style="font-size:11px;">Use New or Open to get started.</div>
      </div>`;
      return;
    }
    const graph = this._app._graphManager && this._app._graphManager._graph;
    if (graph) {
      this._showGraphProperties(graph);
    } else {
      this._el!.innerHTML = '<div style="color:var(--text-dim); padding:16px; text-align:center;">Select a node or port</div>';
    }
  }

  _showGraphProperties(graph: LGraph): void {
    this._el!.innerHTML = '';

    // Ports section first — most prominent, always visible
    this._renderPortsSection(graph);

    this._addHeading('Graph Info');
    const extra = graph.extra || {};
    const meta = extra.meta || {};
    this._addField('Name', meta.name || '', (v: string) => { meta.name = v; });
    this._addTextarea('Description', meta.description || '', (v: string) => { meta.description = v; });
    this._addTextarea('Test Method', meta.test_method || '', (v: string) => { meta.test_method = v; });
  }

  _renderPortsSection(graph: LGraph): void {
    this._addHeading('Ports');
    const ports = graph.extra.ports || [];

    if (ports.length === 0) {
      const emptyMsg = document.createElement('div');
      emptyMsg.style.cssText = 'color:#888; font-size:12px; text-align:center; padding:12px 8px; border:1px dashed #444; border-radius:4px; margin:4px 0;';
      emptyMsg.textContent = 'No ports defined. Ports are the graph\'s external interface — signals that cross the module boundary.';
      this._el!.appendChild(emptyMsg);
    }

    for (let i = 0; i < ports.length; i++) {
      const p = ports[i];
      const row = document.createElement('div');
      row.style.cssText = 'display:flex; gap:4px; align-items:center; padding:2px 0;';
      const info = document.createElement('span');
      info.style.cssText = 'flex:1; font-size:12px; cursor:pointer;';
      const dir = p.direction === 'input' ? '\u2190' : '\u2192';
      const cat = p.category || 'data';
      const typeStr = p.type || '';
      info.textContent = `${dir} ${p.name}  [${cat}${typeStr ? ' ' + typeStr : ''}]`;
      info.addEventListener('click', () => {
        this._showPortEditor(graph, i, p);
      });
      const delBtn = document.createElement('button');
      delBtn.textContent = '\u2715';
      delBtn.title = 'Delete port';
      delBtn.style.cssText = 'flex:0 0 auto; padding:1px 5px; font-size:10px; line-height:1;';
      delBtn.addEventListener('click', (e: MouseEvent) => {
        e.stopPropagation();
        if (!confirm(`Delete port "${p.name}"? This will remove any connections to it.`)) return;
        graph.extra.ports.splice(i, 1);
        this._app._graphManager.markDirty();
        this._app._graphManager.syncBoundaryNodes();
        this._app.redraw();
        this._showGraphProperties(graph);
      });
      row.appendChild(info);
      row.appendChild(delBtn);
      this._el!.appendChild(row);
    }

    const addBtn = document.createElement('button');
    addBtn.textContent = '+ Add Port';
    addBtn.style.cssText = 'margin-top:8px; width:100%; padding:5px; font-size:12px; background:#2a6; color:#fff; border:none; border-radius:3px; cursor:pointer;';
    addBtn.addEventListener('click', () => {
      if (!graph.extra.ports) graph.extra.ports = [];
      graph.extra.ports.push(createDefaultPort('input'));
      this._app._graphManager.markDirty();
      this._app._graphManager.syncBoundaryNodes();
      this._app.redraw();
      this._showGraphProperties(graph);
    });
    this._el!.appendChild(addBtn);
  }

  _showPortEditor(graph: LGraph, index: number, port: PortData): void {
    this._el!.innerHTML = '';
    this._addHeading('Edit Port');
    this._addField('Name', port.name || '', (v: string) => { port.name = v; });
    this._addSelect('Direction', ['input', 'output'], port.direction || 'input', (v: string) => {
      port.direction = v as PortData['direction'];
      this._app._graphManager.syncBoundaryNodes();
      this._app.redraw();
      this._showPortEditor(graph, index, port);
    });
    this._addSelect('Category', ['clock', 'reset', 'data'], port.category || 'data', (v: string) => {
      port.category = v as PortData['category'];
      this._app._graphManager.syncBoundaryNodes();
      this._app.redraw();
      this._showPortEditor(graph, index, port);
    });
    if (port.category !== 'clock' && port.category !== 'reset') {
      this._addTypeSelect('Type', port.type || '', (v: string) => { port.type = v; });
    }
    if (port.category !== 'clock') {
      this._addField('Clock Domain', port.clock_domain || '', (v: string) => { port.clock_domain = v; });
    }
    if (port.category !== 'reset') {
      this._addField('Reset Domain', port.reset_domain || '', (v: string) => { port.reset_domain = v; });
    }
    if (port.category === 'reset') {
      this._addSelect('Reset Type', ['async', 'sync'], port.reset_type || 'async', (v: string) => { port.reset_type = v as PortData['reset_type']; });
    }
    if (port.category === 'data' && port.clock_domain) {
      this._addCheckbox('Allow Cross-Domain Connection', !!port.allow_cross_domain, (v: boolean) => { port.allow_cross_domain = v; });
    }
    this._addButton('\u2190 Back to Graph Properties', () => {
      this._app._graphManager.syncBoundaryNodes();
      this._showGraphProperties(graph);
      this._app.redraw();
    });
  }

  showNodeProperties(node: LGraphNode): void {
    this._el!.innerHTML = '';

    this._addHeading('Module Instance');
    this._addValidatedNameField(node);

    const data = node._module_data || {};
    this._addTextarea('Description', data.description || '', (v: string) => {
      data.description = v;
      node._module_data = data;
    });
    this._addTextarea('Test Method', data.test_method || '', (v: string) => {
      data.test_method = v;
      node._module_data = data;
    });

    this._addHeading('Ref');
    this._addField('Ref Path', node._module_ref || '', (v: string) => { node._module_ref = v; });

    this._addHeading('Properties');
    const props: Record<string, any> = node.properties || {};
    for (const [k, v] of Object.entries(props)) {
      this._addPropertyRow(k, String(v),
        (newV: string) => { node.properties[k] = newV; },
        () => {
          delete node.properties[k];
          this.showNodeProperties(node);
          this._app.redraw();
        }
      );
    }
    this._addButton('+ Add Property', () => {
      const key = prompt('Property name:');
      if (key) {
        node.properties[key] = '';
        this._app._graphManager.markDirty();
        this.showNodeProperties(node);
        this._app.redraw();
      }
    });

    this._addHeading('Ports');
    const ports: { dir: string; idx: number; name: string; data: PortData }[] = [];
    for (let i = 0; i < (node.inputs || []).length; i++) {
      const p = node.inputs[i];
      ports.push({ dir: 'input', idx: i, name: p.name, data: p._port_data || {} });
    }
    for (let i = 0; i < (node.outputs || []).length; i++) {
      const p = node.outputs[i];
      ports.push({ dir: 'output', idx: i, name: p.name, data: p._port_data || {} });
    }
    for (const p of ports) {
      const row = document.createElement('div');
      row.className = 'tree-item';
      const cat = p.data.category || 'data';
      row.textContent = `${p.dir === 'input' ? '\u2190' : '\u2192'} ${p.name} [${cat}]`;
      row.addEventListener('click', () => this.showPortProperties(node, p.dir, p.idx));
      this._el!.appendChild(row);
    }
  }

  showPortProperties(node: LGraphNode, direction: string, slotIdx: number): void {
    this._el!.innerHTML = '';
    this._addHeading('Port Properties');

    const slots: LGraphNodePort[] = direction === 'input' ? node.inputs : node.outputs;
    const slot = slots[slotIdx];
    const portData = slot._port_data || {};

    this._addField('Name', slot.name, (v: string) => { slot.name = v; });
    this._addSelect('Category', ['clock', 'reset', 'data'], portData.category || 'data', (v: string) => {
      portData.category = v;
      slot._port_data = portData;
      const color = node.getPortColor(v);
      slot.color_on = color;
      this._app.redraw();
      this.showPortProperties(node, direction, slotIdx);
    });
    this._addReadonly('Direction', direction);

    const cat = portData.category || 'data';
    if (cat !== 'clock' && cat !== 'reset') {
      this._addTypeSelect('Type', portData.type || '', (v: string) => { portData.type = v; slot._port_data = portData; });
    }
    if (cat !== 'clock') {
      this._addField('Clock Domain', portData.clock_domain || '', (v: string) => { portData.clock_domain = v; slot._port_data = portData; });
    }
    if (cat !== 'reset') {
      this._addField('Reset Domain', portData.reset_domain || '', (v: string) => { portData.reset_domain = v; slot._port_data = portData; });
    }
    if (cat === 'reset') {
      this._addSelect('Reset Type', ['async', 'sync'], portData.reset_type || 'async', (v: string) => { portData.reset_type = v; slot._port_data = portData; });
    }
    if (cat === 'data' && portData.clock_domain) {
      this._addCheckbox('Allow Cross-Domain Connection', !!(portData as PortData).allow_cross_domain, (v: boolean) => { (portData as PortData).allow_cross_domain = v; slot._port_data = portData; });
    }

    this._addButton('\u2190 Back to Node', () => this.showNodeProperties(node));
  }

  _addHeading(text: string): void {
    const h = document.createElement('div');
    h.style.cssText = 'color:var(--text-dim); font-size:10px; text-transform:uppercase; margin: 12px 0 4px; border-top:1px solid #333; padding-top:8px;';
    h.textContent = text;
    this._el!.appendChild(h);
  }

  _addReadonly(label: string, value: string): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const span = document.createElement('span');
    span.textContent = value;
    span.style.cssText = 'color:var(--text-dim); padding:4px 0;';
    g.appendChild(lbl);
    g.appendChild(span);
    this._el!.appendChild(g);
  }

  _addField(label: string, value: string, onChange: (v: string) => void): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const input = document.createElement('input');
    input.value = value;
    input.addEventListener('input', () => {
      onChange(input.value);
      this._app._graphManager.markDirty();
    });
    g.appendChild(lbl);
    g.appendChild(input);
    this._el!.appendChild(g);
  }

  _addValidatedNameField(node: LGraphNode): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = 'Name';
    const input = document.createElement('input');
    input.value = node.title || '';
    const gm = this._app._graphManager;
    let lastValid: string = node.title || '';
    input.addEventListener('change', () => {
      const newName = input.value.trim();
      if (!newName) {
        input.value = lastValid;
        showToast('Name cannot be empty', 'error');
        return;
      }
      if (!gm.isNodeNameUnique(newName, node)) {
        input.value = lastValid;
        showToast(`Name "${newName}" already exists at this level`, 'error');
        return;
      }
      lastValid = newName;
      node.title = newName;
      this._app._graphManager.markDirty();
      this._app.redraw();
    });
    g.appendChild(lbl);
    g.appendChild(input);
    this._el!.appendChild(g);
  }

  _addPropertyRow(label: string, value: string, onChange: (v: string) => void, onDelete: () => void): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    g.style.cssText = 'display:flex; gap:4px; align-items:center;';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    lbl.style.cssText = 'flex:0 0 auto; min-width:60px;';
    const input = document.createElement('input');
    input.value = value;
    input.style.cssText = 'flex:1; min-width:0;';
    input.addEventListener('input', () => {
      onChange(input.value);
      this._app._graphManager.markDirty();
    });
    const delBtn = document.createElement('button');
    delBtn.textContent = '\u2715';
    delBtn.title = 'Delete property';
    delBtn.style.cssText = 'flex:0 0 auto; padding:2px 6px; font-size:11px; line-height:1;';
    delBtn.addEventListener('click', () => {
      onDelete();
      this._app._graphManager.markDirty();
    });
    g.appendChild(lbl);
    g.appendChild(input);
    g.appendChild(delBtn);
    this._el!.appendChild(g);
  }

  _addTextarea(label: string, value: string, onChange: (v: string) => void): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const ta = document.createElement('textarea');
    ta.value = value;
    ta.addEventListener('input', () => {
      onChange(ta.value);
      this._app._graphManager.markDirty();
    });
    g.appendChild(lbl);
    g.appendChild(ta);
    this._el!.appendChild(g);
  }

  _addSelect(label: string, options: string[], selected: string, onChange: (v: string) => void): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const sel = document.createElement('select');
    for (const opt of options) {
      const o = document.createElement('option');
      o.value = opt; o.textContent = opt;
      if (opt === selected) o.selected = true;
      sel.appendChild(o);
    }
    sel.addEventListener('change', () => {
      onChange(sel.value);
      this._app._graphManager.markDirty();
    });
    g.appendChild(lbl);
    g.appendChild(sel);
    this._el!.appendChild(g);
  }

  _addCheckbox(label: string, checked: boolean, onChange: (v: boolean) => void): void {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.style.cssText = 'display:flex; align-items:center; gap:6px; cursor:pointer; text-transform:none; font-size:12px;';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.checked = checked;
    cb.addEventListener('change', () => {
      onChange(cb.checked);
      this._app._graphManager.markDirty();
    });
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(label));
    g.appendChild(lbl);
    this._el!.appendChild(g);
  }

  _addTypeSelect(label: string, value: string, onChange: (v: string) => void): void {
    const DATALIST_ID = '_type-datalist';
    // Remove any stale datalist from a previous render
    const old = document.getElementById(DATALIST_ID);
    if (old) old.remove();

    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const input = document.createElement('input');
    input.value = value;
    input.setAttribute('list', DATALIST_ID);
    input.addEventListener('input', () => {
      onChange(input.value);
      this._app._graphManager.markDirty();
    });
    const datalist = document.createElement('datalist');
    datalist.id = DATALIST_ID;
    const types = this._app._typeSystem.getTypes();
    for (const typeName of Object.keys(types)) {
      const opt = document.createElement('option');
      opt.value = typeName;
      datalist.appendChild(opt);
    }
    g.appendChild(lbl);
    g.appendChild(input);
    g.appendChild(datalist);
    this._el!.appendChild(g);
  }

  _addButton(label: string, onClick: () => void): void {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.style.cssText = 'margin-top:8px; width:100%;';
    btn.addEventListener('click', onClick);
    this._el!.appendChild(btn);
  }
}

export { PropertyPanel };
