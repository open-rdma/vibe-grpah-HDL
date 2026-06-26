function showDialog(title, contentHtml, buttons) {
  const overlay = document.createElement('div');
  overlay.className = 'dialog-overlay';

  const dialog = document.createElement('div');
  dialog.className = 'dialog';
  dialog.innerHTML = `<h3>${title}</h3>`;

  const body = document.createElement('div');
  body.innerHTML = contentHtml;
  dialog.appendChild(body);

  const actions = document.createElement('div');
  actions.className = 'dialog-actions';

  for (const btn of (buttons || [])) {
    const b = document.createElement('button');
    b.textContent = btn.label;
    b.addEventListener('click', () => {
      const result = btn.onClick(body);
      if (result !== false) {
        overlay.remove();
      }
    });
    actions.appendChild(b);
  }
  dialog.appendChild(actions);
  overlay.appendChild(dialog);
  document.body.appendChild(overlay);
  return { overlay, body };
}

function showNewProjectDialog(onCreate) {
  showDialog('New Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path" placeholder="path/to/project"/></div>' +
    '<div class="property-group"><label>Project Name</label><input id="proj-name" placeholder="my_project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Create',
      onClick: (body) => {
        const path = body.querySelector('#proj-path').value;
        const name = body.querySelector('#proj-name').value;
        if (path && name && onCreate) onCreate(path, name);
      }
    }]
  );
}

function showOpenProjectDialog(onOpen) {
  showDialog('Open Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path-open" placeholder="path/to/project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Open',
      onClick: (body) => {
        const path = body.querySelector('#proj-path-open').value;
        if (path && onOpen) onOpen(path);
      }
    }]
  );
}

function showBuildDialog(onBuild) {
  showDialog('Build Configuration',
    '<div class="property-group"><label>Scope</label><select id="build-scope">' +
      '<option value="this">This module only</option>' +
      '<option value="descendants">This + descendants</option>' +
      '<option value="ancestors">This + ancestors</option>' +
      '<option value="all">Entire graph</option>' +
    '</select></div>' +
    '<div class="property-group"><label>Mode</label><select id="build-mode">' +
      '<option value="fresh">Fresh (no prior code)</option>' +
      '<option value="incremental">Incremental (with prior code)</option>' +
    '</select></div>' +
    '<div class="property-group"><label><input type="checkbox" id="build-tb" checked/> Include testbench</label></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Build',
      onClick: (body) => {
        if (onBuild) {
          onBuild({
            scope: body.querySelector('#build-scope').value,
            mode: body.querySelector('#build-mode').value,
            includeTestbench: body.querySelector('#build-tb').checked
          });
        }
      }
    }]
  );
}

export { showDialog, showNewProjectDialog, showOpenProjectDialog, showBuildDialog };
