const PORT_COLORS = {
  clock: '#0af',
  reset: '#f80',
  data: '#aaa'
};

/**
 * RTL Module Node — represents a module instance on the canvas.
 * Subclassed via litegraph.js prototype copying system.
 */
function RTLModuleNode() {
  // Ports will be added by the graph manager after construction
  this.properties = {};
  this._module_ref = null;
  this._module_data = null;
}

RTLModuleNode.title = 'RTL Module';
RTLModuleNode.desc = 'An RTL module instance';

RTLModuleNode.prototype.getPortColor = function(category) {
  return PORT_COLORS[category] || PORT_COLORS.data;
};

RTLModuleNode.prototype.onConnectInput = function(target_slot, type, output_slot, output_node) {
  // Delegate to global connection validator if registered
  if (window.__connectionValidator) {
    var result = window.__connectionValidator.validate(
      output_node, output_slot,
      this, target_slot
    );
    if (!result.allowed) {
      window.__showToast('Connection blocked: ' + result.reason, 'error');
      return false;
    }
  }
  return true;
};

RTLModuleNode.prototype.onConnectOutput = function(output_slot, type, input_slot, input_node) {
  if (window.__connectionValidator) {
    var result = window.__connectionValidator.validate(
      this, output_slot,
      input_node, input_slot
    );
    if (!result.allowed) {
      window.__showToast('Connection blocked: ' + result.reason, 'error');
      return false;
    }
  }
  return true;
};

RTLModuleNode.prototype.onDblClick = function(e, pos, graphcanvas) {
  if (this._subgraph) {
    graphcanvas.openSubgraph(this._subgraph);
    return true;
  }
  return false;
};

RTLModuleNode.prototype.setPortsFromData = function(moduleData) {
  // Clear existing ports
  this.inputs.length = 0;
  this.outputs.length = 0;

  var ports = moduleData.ports || [];
  for (var i = 0; i < ports.length; i++) {
    var p = ports[i];
    var color = this.getPortColor(p.category);
    if (p.direction === 'input') {
      this.addInput(p.name, p.type || p.category || 'data');
      var idx = this.inputs.length - 1;
      this.inputs[idx].color_on = color;
      this.inputs[idx]._port_data = p;
    } else {
      this.addOutput(p.name, p.type || p.category || 'data');
      var idx2 = this.outputs.length - 1;
      this.outputs[idx2].color_on = color;
      this.outputs[idx2]._port_data = p;
    }
  }
};

LiteGraph.registerNodeType('rtl/module', RTLModuleNode);
