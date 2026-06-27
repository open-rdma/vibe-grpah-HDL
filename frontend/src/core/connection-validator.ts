import type { ValidationResult } from '../types/graph-types';
import { TypeSystem } from './type-system';

class ConnectionValidator {
  private _typeSystem: TypeSystem;

  constructor(typeSystem: TypeSystem) {
    this._typeSystem = typeSystem;
  }

  validate(outputNode: LGraphNode, outputSlotIdx: number, inputNode: LGraphNode, inputSlotIdx: number): ValidationResult {
    const outSlot = outputNode.outputs[outputSlotIdx];
    const inSlot = inputNode.inputs[inputSlotIdx];

    if (!outSlot || !inSlot) {
      return { allowed: false, reason: 'Invalid slot' };
    }

    const outPort = (outSlot._port_data || {}) as import('../types/graph-types').PortData;
    const inPort = (inSlot._port_data || {}) as import('../types/graph-types').PortData;

    const outCat = outPort.category || 'data';
    const inCat = inPort.category || 'data';

    // Rule: data → clock/reset is blocked
    if (outCat === 'data' && (inCat === 'clock' || inCat === 'reset')) {
      return { allowed: false, reason: `Cannot connect data output to ${inCat} input` };
    }

    // Rule: type compatibility
    const outType = outPort.type || outCat;
    const inType = inPort.type || inCat;
    if (outCat === 'data' && inCat === 'data') {
      if (!this._typeSystem.areCompatible(outType, inType)) {
        return { allowed: false, reason: `Type mismatch: ${outType} vs ${inType}` };
      }
    }

    // Rule: cross-domain check
    const outDomain = outPort.clock_domain || '';
    const inDomain = inPort.clock_domain || '';
    if (outCat === 'data' && inCat === 'data' && outDomain && inDomain && outDomain !== inDomain) {
      if (!outPort.allow_cross_domain && !inPort.allow_cross_domain) {
        return { allowed: false, reason: `Cross-domain connection blocked (${outDomain} → ${inDomain}). Enable "Allow Cross-Domain" on either port to override.` };
      }
    }

    return { allowed: true, reason: '' };
  }
}

export { ConnectionValidator };
