BSV syntax:
- typedef VALUE NAME; — numeric constant
- typedef Bit#(W) NAME; — bit vector alias
- typedef enum {A=3'h0,B=3'h1} T deriving(Bits,Eq,FShow);
- typedef struct { T1 f; T2 g; } S deriving(Bits,FShow);
- SizeOf#(T); TDiv#(a,b); TExp#(n); TAdd#(a,b); TMul#(a,b)
- import Reserved :: *; for ReservedZero#(n)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method T m(args); endinterface
- module mkM(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;


Generate BSV functions for: ReqHandleRQ

Types already defined (import them): ReqHandleRQ

function Bool isErrReqStatus(RdmaReqStatus reqStatus);
  // Reference implementation:
  // function Bool isErrReqStatus(RdmaReqStatus reqStatus);
    return case (reqStatus)
        RDMA_REQ_ST_INV_REQ,
        RDMA_REQ_ST_INV_RD ,
        RDMA_REQ_ST_RMT_ACC,
        RDMA_REQ_ST_RMT_OP : True;
        default            : False;
    endcase;
endfunction

function Bool isNormalOrErrorReqStatus(RdmaReqStatus reqStatus);
  // Reference implementation:
  // function Bool isNormalOrErrorReqStatus(RdmaReqStatus reqStatus);
    return case (reqStatus)
        RDMA_REQ_ST_NORMAL ,
        RDMA_REQ_ST_INV_REQ,
        RDMA_REQ_ST_INV_RD ,
        RDMA_REQ_ST_RMT_ACC,
        RDMA_REQ_ST_RMT_OP : True;
        default            : False;
    endcase;
endfunction

function Maybe#(QPN) getMaybeDestQpnRQ(CntrlStatus cntrlStatus);
  // Reference implementation:
  // function Maybe#(QPN) getMaybeDestQpnRQ(CntrlStatus cntrlStatus);
    return case (cntrlStatus.getTypeQP)
        IBV_QPT_RC      ,
        IBV_QPT_UC      ,
        IBV_QPT_XRC_RECV: tagged Valid cntrlStatus.comm.getDQPN;
        // IBV_QPT_XRC_SEND
        // IBV_QPT_UD
        default: tagged Invalid;
    endcase;
endfunction

function Maybe#(WorkCompStatus) genWorkCompStatusFromReqStatusRQ(RdmaReqStatus reqStatus);
  // Reference implementation:
  // function Maybe#(WorkCompStatus) genWorkCompStatusFromReqStatusRQ(RdmaReqStatus reqStatus);
    return case (reqStatus)
        RDMA_REQ_ST_NORMAL      : tagged Valid IBV_WC_SUCCESS;
        RDMA_REQ_ST_INV_REQ     : tagged Valid IBV_WC_REM_INV_REQ_ERR;
        RDMA_REQ_ST_INV_RD      : tagged Valid IBV_WC_REM_INV_RD_REQ_ERR;
        RDMA_REQ_ST_RMT_ACC     : tagged Valid IBV_WC_REM_ACCESS_ERR;
        RDMA_REQ_ST_RMT_OP      : tagged Valid IBV_WC_REM_OP_ERR;
        RDMA_REQ_ST_ERR_FLUSH_RR: tag

function ? unknown();
  // Reference implementation:
  // function Maybe#(RdmaOpCode) genFirstOrOnlyRespRdmaOpCode(
    RdmaOpCode reqOpCode, RdmaReqStatus reqStatus, Bool isOnlyReadRespPkt
);
    case (reqStatus)
        RDMA_REQ_ST_NORMAL,
        RDMA_REQ_ST_DUP   : begin
            return case (reqOpCode)
                SEND_FIRST                    ,
                SEND_MIDDLE                   ,
                SEND_LAST                     ,
                SEND_LAST_WITH_IMMEDIATE      ,
                SEND_ONLY                     ,
      

function Maybe#(RdmaOpCode) genMiddleOrLastRespRdmaOpCode(RdmaReqStatus reqStatus, Bool isLastRespPkt);
  // Reference implementation:
  // function Maybe#(RdmaOpCode) genMiddleOrLastRespRdmaOpCode(RdmaReqStatus reqStatus, Bool isLastRespPkt);
    return case (reqStatus)
        RDMA_REQ_ST_NORMAL,
        RDMA_REQ_ST_DUP   : tagged Valid (isLastRespPkt ? RDMA_READ_RESPONSE_LAST : RDMA_READ_RESPONSE_MIDDLE);
        RDMA_REQ_ST_RMT_OP: tagged Valid ACKNOWLEDGE;
        default           : tagged Invalid;
    endcase;
endfunction

function Maybe#(AETH) genAethByReqStatus(RdmaReqStatus reqStatus, CntrlStatus cntrlStatus, MSN msn);
  // Reference implementation:
  // function Maybe#(AETH) genAethByReqStatus(RdmaReqStatus reqStatus, CntrlStatus cntrlStatus, MSN msn);
    return case (reqStatus)
        RDMA_REQ_ST_NORMAL,
        RDMA_REQ_ST_DUP   : begin
            tagged Valid AETH {
                rsvd : unpack(0),
                code : AETH_CODE_ACK,
                value: pack(AETH_ACK_VALUE_INVALID_CREDIT_CNT),
                msn  : msn
            };
        end
        RDMA_REQ_ST_RNR: begin
            tagged Valid AETH {
                rsvd : u

function ? unknown();
  // Reference implementation:
  // function Maybe#(HeaderRDMA) genFirstOrOnlyRespHeader(
    RdmaOpCode reqOpCode, RdmaReqStatus reqStatus,
    Length payloadLen, Maybe#(Long) atomicOrigData,
    CntrlStatus cntrlStatus, PSN psn, MSN msn, Bool isOnlyReadRespPkt
);
    let maybeTrans  = qpType2TransType(cntrlStatus.getTypeQP);
    let maybeOpCode = genFirstOrOnlyRespRdmaOpCode(reqOpCode, reqStatus, isOnlyReadRespPkt);
    let maybeDQPN   = getMaybeDestQpnRQ(cntrlStatus);
    let maybeAETH   = genAethByReqStatus(reqStatus, cntrlSta

function ? unknown();
  // Reference implementation:
  // function Maybe#(HeaderRDMA) genMiddleOrLastRespHeader(
    RdmaOpCode reqOpCode, RdmaReqStatus reqStatus, Length payloadLen,
    CntrlStatus cntrlStatus, PSN psn, MSN msn, Bool isLastRespPkt
);
    let maybeTrans  = qpType2TransType(cntrlStatus.getTypeQP);
    let maybeOpCode = genMiddleOrLastRespRdmaOpCode(reqStatus, isLastRespPkt);
    let maybeDQPN   = getMaybeDestQpnRQ(cntrlStatus);
    let maybeAETH   = genAethByReqStatus(reqStatus, cntrlStatus, msn);

    if (
        maybeTrans  matches t

function RdmaReqStatus getInvReqStatusByTransType(TransType transType);
  // Reference implementation:
  // function RdmaReqStatus getInvReqStatusByTransType(TransType transType);
    return case (transType)
        TRANS_TYPE_RC : RDMA_REQ_ST_INV_REQ;
        TRANS_TYPE_UC : RDMA_REQ_ST_DISCARD;
        TRANS_TYPE_RD : RDMA_REQ_ST_INV_RD ;
        TRANS_TYPE_UD : RDMA_REQ_ST_DISCARD;
        TRANS_TYPE_CNP: RDMA_REQ_ST_DISCARD;
        TRANS_TYPE_XRC: RDMA_REQ_ST_INV_RD ;
        default       : RDMA_REQ_ST_UNKNOWN;
    endcase;
endfunction

function ? unknown();
  // Reference implementation:
  // function RdmaReqStatus pktStatus2ReqStatusRQ(
    PktVeriStatus pktStatus, TransType transType
);
    return case (pktStatus)
        PKT_ST_VALID  : RDMA_REQ_ST_NORMAL;
        PKT_ST_LEN_ERR: getInvReqStatusByTransType(transType);
        // PKT_ST_DISCARD: RDMA_REQ_ST_DISCARD;
        default       : RDMA_REQ_ST_UNKNOWN;
    endcase;
endfunction

function ? unknown();
  // Reference implementation:
  //     function Epoch  getEpoch() = contextRQ.getEpoch;
    function Action incEpoch() = contextRQ.incEpoch;

    (* no_implicit_conditions, fire_when_enabled *)
    rule resetAndClear if (cntrlStatus.comm.isReset);
        // payloadConReqOutQ.clear;
        // payloadGenReqOutQ.clear;
        workCompGenReqOutQ.clear;
        respHeaderOutQ.clear;
        psnRespOutQ.clear;

        // clearRetryRelatedPipelineQ;
        supportedReqOpCodeCheckQ.clear;
        reqOpCodeSeqCheckQ.clear;
        rn

Output in ```bsv block. Include imports referencing existing types. Generate now: