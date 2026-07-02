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


Generate BSV functions for: Controller

Types already defined (import them): Controller

function FlagsType#(QpAttrMaskFlag) getReset2InitRequiredAttr();
  // Reference implementation:
  // function FlagsType#(QpAttrMaskFlag) getReset2InitRequiredAttr();
    FlagsType#(QpAttrMaskFlag) requiredFlags =
        enum2Flag(IBV_QP_STATE)      |
        enum2Flag(IBV_QP_PKEY_INDEX) |
        // enum2Flag(IBV_QP_PORT)       |
        enum2Flag(IBV_QP_ACCESS_FLAGS);

    return requiredFlags;
endfunction

function FlagsType#(QpAttrMaskFlag) getInit2RtrRequiredAttr();
  // Reference implementation:
  // function FlagsType#(QpAttrMaskFlag) getInit2RtrRequiredAttr();
    FlagsType#(QpAttrMaskFlag) requiredFlags =
        enum2Flag(IBV_QP_STATE)              |
        // enum2Flag(IBV_QP_AV)                 |
        enum2Flag(IBV_QP_PATH_MTU)           |
        enum2Flag(IBV_QP_DEST_QPN)           |
        enum2Flag(IBV_QP_RQ_PSN)             |
        enum2Flag(IBV_QP_MAX_DEST_RD_ATOMIC) |
        enum2Flag(IBV_QP_MIN_RNR_TIMER);

    return requiredFlags;
endfunction

function FlagsType#(QpAttrMaskFlag) getRtr2RtsRequiredAttr();
  // Reference implementation:
  // function FlagsType#(QpAttrMaskFlag) getRtr2RtsRequiredAttr();
    FlagsType#(QpAttrMaskFlag) requiredFlags =
        enum2Flag(IBV_QP_STATE)     |
        enum2Flag(IBV_QP_SQ_PSN)    |
        enum2Flag(IBV_QP_TIMEOUT)   |
        enum2Flag(IBV_QP_RETRY_CNT) |
        enum2Flag(IBV_QP_RNR_RETRY) |
        enum2Flag(IBV_QP_MAX_QP_RD_ATOMIC);

    return requiredFlags;
endfunction

function FlagsType#(QpAttrMaskFlag) getOnlyStateRequiredAttr();
  // Reference implementation:
  // function FlagsType#(QpAttrMaskFlag) getOnlyStateRequiredAttr();
    return enum2Flag(IBV_QP_STATE);
endfunction

function ? unknown();
  // Reference implementation:
  //     function Action debugShowRegs();
        action
            $display(
                "time=%0t: mkCntrlQP internal registers", $time,
                ", preStateReg=", fshow(preStateReg),
                ", stateReg=", fshow(stateReg),
                ", sqTypeReg=", fshow(sqTypeReg),
                ", rqTypeReg=", fshow(rqTypeReg),
                ", maxRnrCntReg=", fshow(maxRnrCntReg),
                ", maxRetryCntReg=", fshow(maxRetryCntReg),
                ", maxTimeOutReg=", fshow(m

function ? unknown();
  // Reference implementation:
  //     function AttrQP queryReset2InitAttr(AttrQP qpAttr);
        qpAttr.curQpState    = stateReg;
        qpAttr.qpAccessFlags = qpAccessFlagsReg;
        qpAttr.pkeyIndex     = pkeyReg;

        return qpAttr;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function AttrQP queryInit2RtrAttr(AttrQP qpAttr);
        qpAttr.pmtu              = pmtuReg;
        qpAttr.dqpn              = dqpnReg;
        qpAttr.rqPSN             = epsnReg[0];
        qpAttr.maxDestReadAtomic = pendingDestReadAtomicReqNumReg;
        qpAttr.minRnrTimer       = minRnrTimerReg;

        return qpAttr;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function AttrQP queryRtr2RtsAttr(AttrQP qpAttr);
        qpAttr.sqPSN         = npsnReg;
        qpAttr.timeout       = maxTimeOutReg;
        qpAttr.retryCnt      = maxRetryCntReg;
        qpAttr.rnrRetry      = maxRnrCntReg;
        qpAttr.maxReadAtomic = pendingReadAtomicReqNumReg;

        return qpAttr;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function getCntrlCommStatus();
        // interface cntrlCommStatus = interface CntrlCommStatus;
        // method StateQP getQPS() = stateReg;
        let ret = interface CntrlCommStatus;
            method Bool isCreate()  = stateReg == IBV_QPS_CREATE;
            method Bool isERR()     = stateReg == IBV_QPS_ERR;
            method Bool isInit()    = stateReg == IBV_QPS_INIT;
            method Bool isNonErr()  = stateReg == IBV_QPS_RTR || stateReg == IBV_QPS_RTS || stateReg == IBV_QPS_SQ

Output in ```bsv block. Include imports referencing existing types. Generate now: