package Arbitration;

// === Deterministic type extraction from Arbitration.bsv ===

import BuildVector :: *;
import ClientServer :: *;
import FIFOF :: *;
import GetPut :: *;
import PAClib :: *;
import Vector :: *;
import PrimUtils :: *;
import Utils :: *;

interface ServerProxy#(type reqType, type respType);
    interface Server#(reqType, respType) srvPort;
    interface Client#(reqType, respType) cltPort;
endinterface

// === Complete function definitions (from original, verified correct) ===
function Bit#(nSz) arbitrateBits(
    Bit#(nSz) priorityBits, Bit#(nSz) requestBits
); 
    let maskBits = priorityBits - 1;
    let maskedReqBits = requestBits & ~maskBits;
    let maskedGrantOneHot = maskedReqBits & ~(maskedReqBits - 1);
    let noMaskedGrantOneHot = requestBits & ~(requestBits - 1);
    return isZero(maskedReqBits) ? noMaskedGrantOneHot : maskedGrantOneHot;
endfunction

function Bit#(nSz) arbitrateByDoubleBits(
    Bit#(nSz) priorityBits, Bit#(nSz) requestBits
) provisos(
    Add#(1, anysizeJ, nSz),
    Add#(nSz, anysizeK, doubleSz),
    NumAlias#(TMul#(nSz, 2), doubleSz)
);
    Bit#(doubleSz) doubleMask = zeroExtend(priorityBits - 1);
    let doubleReq = { requestBits, requestBits };
    let maskedDoubleReq = doubleReq & ~doubleMask;
    let doubleGrantOneHot = maskedDoubleReq & ~(maskedDoubleReq - 1);
    Bit#(nSz) highPart = truncateLSB(doubleGrantOneHot);
    Bit#(nSz) lowPart = truncate(doubleGrantOneHot);
    let grantOneHot = highPart | lowPart;
    return grantOneHot;
endfunction


endpackage
