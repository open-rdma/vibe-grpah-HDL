import { showToast } from './toast';

function showDialog(title: string, contentHtml: string, buttons?: { label: string; onClick: (body: HTMLDivElement) => boolean | void }[]): { overlay: HTMLDivElement; body: HTMLDivElement } {
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

function showNewProjectDialog(onCreate: (path: string, name: string) => void): void {
  showDialog('New Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path" placeholder="path/to/project"/></div>' +
    '<div class="property-group"><label>Project Name</label><input id="proj-name" placeholder="my_project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Create',
      onClick: (body) => {
        const path = (body.querySelector('#proj-path') as HTMLInputElement).value.trim();
        const name = (body.querySelector('#proj-name') as HTMLInputElement).value.trim();
        if (!path) { showToast('Project path is required', 'error'); return; }
        if (!name) { showToast('Project name is required', 'error'); return; }
        onCreate(path, name);
      }
    }]
  );
}

function showOpenProjectDialog(onOpen: (path: string) => void): void {
  showDialog('Open Project',
    '<div class="property-group"><label>Project Path</label><input id="proj-path-open" placeholder="path/to/project"/></div>',
    [{
      label: 'Cancel',
      onClick: () => {}
    }, {
      label: 'Open',
      onClick: (body) => {
        const path = (body.querySelector('#proj-path-open') as HTMLInputElement).value.trim();
        if (!path) { showToast('Project path is required', 'error'); return; }
        onOpen(path);
      }
    }]
  );
}

interface BuildDialogOptions {
  scope: string;
  mode: string;
  includeTestbench: boolean;
}

function showBuildDialog(onBuild: (opts: BuildDialogOptions) => void): void {
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
            scope: (body.querySelector('#build-scope') as HTMLSelectElement).value,
            mode: (body.querySelector('#build-mode') as HTMLSelectElement).value,
            includeTestbench: (body.querySelector('#build-tb') as HTMLInputElement).checked
          });
        }
      }
    }]
  );
}

export { showNewProjectDialog, showOpenProjectDialog, showBuildDialog };
export type { BuildDialogOptions };
