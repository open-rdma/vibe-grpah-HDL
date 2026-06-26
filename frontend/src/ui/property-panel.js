class PropertyPanel {
  constructor(app) {
    this._app = app;
    this._el = null;
  }

  init(container) {
    this._el = container;
  }

  clear() {
    this._el.innerHTML = '<div style="color:var(--text-dim); padding:16px; text-align:center;">Select a node or port</div>';
  }

  showNodeProperties(node) {
    this._el.innerHTML = '';

    this._addHeading('Module Instance');
    this._addField('Name', node.title || '', (v) => { node.title = v; });

    const data = node._module_data || {};
    this._addTextarea('Description', data.description || '', (v) => {
      data.description = v;
      node._module_data = data;
    });
    this._addTextarea('Test Method', data.test_method || '', (v) => {
      data.test_method = v;
      node._module_data = data;
    });

    this._addHeading('Ref');
    this._addField('Ref Path', node._module_ref || '', (v) => { node._module_ref = v; });

    this._addHeading('Properties');
    const props = node.properties || {};
    for (const [k, v] of Object.entries(props)) {
      this._addField(k, String(v), (newV) => { node.properties[k] = newV; });
    }
    this._addButton('+ Add Property', () => {
      const key = prompt('Property name:');
      if (key) {
        node.properties[key] = '';
        this.showNodeProperties(node);
        this._app.redraw();
      }
    });

    this._addHeading('Ports');
    const ports = [];
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
      row.textContent = `${p.dir === 'input' ? '←' : '→'} ${p.name} [${cat}]`;
      row.addEventListener('click', () => this.showPortProperties(node, p.dir, p.idx));
      this._el.appendChild(row);
    }
  }

  showPortProperties(node, direction, slotIdx) {
    this._el.innerHTML = '';
    this._addHeading('Port Properties');

    const slots = direction === 'input' ? node.inputs : node.outputs;
    const slot = slots[slotIdx];
    const portData = slot._port_data || {};

    this._addField('Name', slot.name, (v) => { slot.name = v; });
    this._addSelect('Category', ['clock', 'reset', 'data'], portData.category || 'data', (v) => {
      portData.category = v;
      slot._port_data = portData;
      const color = node.getPortColor(v);
      slot.color_on = color;
      this._app.redraw();
    });
    this._addSelect('Direction', ['input', 'output'], direction, () => {});
    this._addField('Type', portData.type || '', (v) => { portData.type = v; slot._port_data = portData; });
    this._addField('Clock Domain', portData.clock_domain || '', (v) => { portData.clock_domain = v; slot._port_data = portData; });
    this._addField('Reset Domain', portData.reset_domain || '', (v) => { portData.reset_domain = v; slot._port_data = portData; });

    const resetType = portData.reset_type || 'async';
    this._addSelect('Reset Type', ['async', 'sync'], resetType, (v) => { portData.reset_type = v; slot._port_data = portData; });

    this._addButton('← Back to Node', () => this.showNodeProperties(node));
  }

  _addHeading(text) {
    const h = document.createElement('div');
    h.style.cssText = 'color:var(--text-dim); font-size:10px; text-transform:uppercase; margin: 12px 0 4px; border-top:1px solid #333; padding-top:8px;';
    h.textContent = text;
    this._el.appendChild(h);
  }

  _addField(label, value, onChange) {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const input = document.createElement('input');
    input.value = value;
    input.addEventListener('change', () => onChange(input.value));
    g.appendChild(lbl);
    g.appendChild(input);
    this._el.appendChild(g);
  }

  _addTextarea(label, value, onChange) {
    const g = document.createElement('div');
    g.className = 'property-group';
    const lbl = document.createElement('label');
    lbl.textContent = label;
    const ta = document.createElement('textarea');
    ta.value = value;
    ta.addEventListener('change', () => onChange(ta.value));
    g.appendChild(lbl);
    g.appendChild(ta);
    this._el.appendChild(g);
  }

  _addSelect(label, options, selected, onChange) {
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
    sel.addEventListener('change', () => onChange(sel.value));
    g.appendChild(lbl);
    g.appendChild(sel);
    this._el.appendChild(g);
  }

  _addButton(label, onClick) {
    const btn = document.createElement('button');
    btn.textContent = label;
    btn.style.cssText = 'margin-top:8px; width:100%;';
    btn.addEventListener('click', onClick);
    this._el.appendChild(btn);
  }
}

export { PropertyPanel };
