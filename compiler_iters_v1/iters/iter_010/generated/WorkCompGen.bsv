package WorkCompGen;

// === Deterministic type extraction from WorkCompGen.bsv ===

import FIFOF :: *;
import GetPut :: *;
import PAClib :: *;
import Controller :: *;
import DataTypes :: *;
import Headers :: *;
import PrimUtils :: *;
import SpecialFIFOF :: *;
import Settings :: *;
import Utils :: *;

typedef enum {
    WC_GEN_ST_STOP,
    WC_GEN_ST_NORMAL,
    WC_GEN_ST_ERR_FLUSH
} WorkCompGenState deriving(Bits, Eq);

typedef struct {
    WorkCompGenReqSQ wcGenReqSQ;
    WorkComp         workComp;
    Bool             isWorkCompSuccess;
    Bool             needWorkCompWhenNormal;
} PendingWorkCompSQ deriving(Bits);
typedef struct {
    WorkCompGenReqRQ wcGenReqRQ;
    Maybe#(WorkComp) maybeWorkComp;
    Bool             isSendReq;
    Bool             isWriteReq;
    Bool             isWriteImmReq;
    Bool             isFirstOrOnlyReq;
    Bool             isLastOrOnlyReq;
    Bool             isWorkCompSuccess;
    Bool             needWaitDmaWriteResp;
} PendingWorkCompRQ deriving(Bits);

interface WorkCompGen;
    interface PipeOut#(WorkComp) workCompPipeOut;
    method Bool hasErr();
endinterface

// === Complete function definitions (from original, verified correct) ===
function Maybe#(WorkComp) genWorkComp4WorkReq(
    CntrlStatus cntrlStatus, WorkCompGenReqSQ wcGenReqSQ
);
    let wr = wcGenReqSQ.wr;
    let maybeWorkCompOpCode = workReqOpCode2WorkCompOpCode4SQ(wr.opcode);
    
    
    let wcFlags = IBV_WC_NO_FLAGS;

    if (maybeWorkCompOpCode matches tagged Valid .opcode) begin
        let workComp = WorkComp {
            id      : wr.id,
            opcode  : opcode,
            flags   : wcFlags,
            status  : wcGenReqSQ.wcStatus,
            len     : wr.len,
            pkey    : cntrlStatus.comm.getPKEY,
            qpn    : cntrlStatus.comm.getSQPN,
            
            
            immDt   : tagged Invalid,
            rkey2Inv: tagged Invalid
        };
        return tagged Valid workComp;
    end
    else begin
        return tagged Invalid;
    end
endfunction

function Maybe#(WorkComp) genWorkComp4RecvReq(
    CntrlStatus cntrlStatus, WorkCompGenReqRQ wcGenReqRQ
);
    let maybeWorkCompOpCode = rdmaOpCode2WorkCompOpCode4RQ(wcGenReqRQ.reqOpCode);
    let wcFlags = rdmaOpCode2WorkCompFlagsRQ(wcGenReqRQ.reqOpCode);
    if (
        maybeWorkCompOpCode matches tagged Valid .opcode &&&
        wcGenReqRQ.rrID matches tagged Valid .rrID
    ) begin
        let workComp = WorkComp {
            id      : rrID,
            opcode  : opcode,
            flags   : wcFlags,
            status  : wcGenReqRQ.wcStatus,
            len     : wcGenReqRQ.len,
            pkey    : cntrlStatus.comm.getPKEY,
            qpn     : cntrlStatus.comm.getSQPN,
            
            
            immDt   : wcGenReqRQ.immDt,
            rkey2Inv: wcGenReqRQ.rkey2Inv
        };
        return tagged Valid workComp;
    end
    else begin
        return tagged Invalid;
    end
endfunction


endpackage
