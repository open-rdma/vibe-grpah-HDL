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


Generate BSV types for: ReqHandleRQ


Enums:
  typedef enum {
    RDMA_REQ_ST_NORMAL,
    RDMA_REQ_ST_SEQ_ERR,
    RDMA_REQ_ST_RNR,
    RDMA_REQ_ST_INV_REQ,
    RDMA_REQ_ST_INV_RD,
    RDMA_REQ_ST_RMT_ACC,
    RDMA_REQ_ST_RMT_OP,
    RDMA_REQ_ST_DUP,
    RDMA_REQ_ST_ERR_FLUSH_RR,
    RDMA_REQ_ST_DISCARD,
    RDMA_REQ_ST_UNKNOWN,
  } RdmaReqStatus deriving(Bits, Eq, FShow);
  typedef enum {
    RQ_PRE_BUILD_STAGE,
    RQ_PRE_CALC_STAGE,
    RQ_PRE_STAGE_DONE,
    RQ_PRE_RETRY_FLUSH,
  } PreStageStateRQ deriving(Bits, Eq, FShow);
  typedef enum {
    RQ_SEQ_RETRY_FLUSH,
    RQ_RNR_RETRY_FLUSH,
    RQ_RNR_WAIT,
    RQ_RNR_WAIT_DONE,
    RQ_NOT_RETRY,
  } RetryStateRQ deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    BTH bth;
    Epoch epoch;
    PktNum respPktNum;
    PSN endPSN;
    Bool isSendReq;
    Bool isWriteReq;
    Bool isWriteImmReq;
    Bool isReadReq;
    Bool isAtomicReq;
    Bool isOnlyPkt;
    Bool isFirstPkt;
    Bool isMidPkt;
    Bool isLastPkt;
    Bool isFirstOrOnlyPkt;
    Bool isLastOrOnlyPkt;
    Bool isOnlyRespPkt;
    Bool isExpected;
    Bool isDuplicated;
    Bool isAccCheckPass;
  } RdmaReqPktInfo deriving(Bits);
  typedef SizeOf#(RdmaReqPktInfo) RdmaReqPktInfo_WIDTH;
  typedef TDiv#(RdmaReqPktInfo_WIDTH, 8) RdmaReqPktInfo_BYTE_WIDTH;
  typedef struct {
    Bool hasReqStatusErr;
    Bool hasDmaReadRespErr;
    Bool hasErrRespGen;
    Bool shouldGenResp;
    Bool expectReadRespPayload;
    Bool expectAtomicRespOrig;
    Bool expectDupAtomicCheckResp;
    Maybe#(Long) atomicAckOrig;
    DupReadReqStartState dupReadReqStartState;
  } RespPktGenInfo deriving(Bits, FShow);
  typedef SizeOf#(RespPktGenInfo) RespPktGenInfo_WIDTH;
  typedef TDiv#(RespPktGenInfo_WIDTH, 8) RespPktGenInfo_BYTE_WIDTH;
  typedef struct {
    Bool isFirstOrOnlyRespPkt;
    Bool isLastOrOnlyRespPkt;
  } RespPktSeqInfo deriving(Bits, FShow);
  typedef SizeOf#(RespPktSeqInfo) RespPktSeqInfo_WIDTH;
  typedef TDiv#(RespPktSeqInfo_WIDTH, 8) RespPktSeqInfo_BYTE_WIDTH;
  typedef struct {
    PSN psn;
    MSN msn;
    Bool isFirstOrOnlyRespPkt;
    Bool isLastOrOnlyRespPkt;
  } RespPktHeaderInfo deriving(Bits, FShow);
  typedef SizeOf#(RespPktHeaderInfo) RespPktHeaderInfo_WIDTH;
  typedef TDiv#(RespPktHeaderInfo_WIDTH, 8) RespPktHeaderInfo_BYTE_WIDTH;
  typedef struct {
    Bool enoughDmaSpace;
    Bool isLastPayloadLenZero;
    ADDR curDmaWriteAddr;
    Length remainingDmaWriteLen;
    Length totalDmaWriteLen;
  } ReqLenCheckResult deriving(Bits);
  typedef SizeOf#(ReqLenCheckResult) ReqLenCheckResult_WIDTH;
  typedef TDiv#(ReqLenCheckResult_WIDTH, 8) ReqLenCheckResult_BYTE_WIDTH;
  typedef struct {
    Bool onlyPktCase;
    Bool firstPktCase;
    Bool midPktCase;
    Bool lastPktCase;
  } EnoughDmaSpaceCheck deriving(Bits);
  typedef SizeOf#(EnoughDmaSpaceCheck) EnoughDmaSpaceCheck_WIDTH;
  typedef TDiv#(EnoughDmaSpaceCheck_WIDTH, 8) EnoughDmaSpaceCheck_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: