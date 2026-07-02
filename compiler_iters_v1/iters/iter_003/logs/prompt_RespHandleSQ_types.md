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


Generate BSV types for: RespHandleSQ


Enums:
  typedef enum {
    SQ_HANDLE_RESP_HEADER,
    SQ_RETRY_FLUSH,
    SQ_ERROR_FLUSH,
  } RespHandleState deriving(Bits, Eq, FShow);
  typedef enum {
    WR_ACK_EXPLICIT_WHOLE_NORMAL,
    WR_ACK_EXPLICIT_WHOLE_RETRY,
    WR_ACK_EXPLICIT_WHOLE_ERROR,
    WR_ACK_EXPLICIT_PARTIAL_NORMAL,
    WR_ACK_EXPLICIT_PARTIAL_RETRY,
    WR_ACK_EXPLICIT_PARTIAL_ERROR,
    WR_ACK_COALESCE_NORMAL,
    WR_ACK_COALESCE_RETRY,
    WR_ACK_DUPLICATE,
    WR_ACK_GHOST,
    WR_ACK_ILLEGAL,
    WR_ACK_DISCARD,
    WR_ACK_ERR_FLUSH_WR,
    WR_ACK_TIMOUT_ERR,
    WR_ACK_UNKNOWN,
  } WorkReqAckType deriving(Bits, Eq, FShow);
  typedef enum {
    SQ_ACT_BAD_RESP,
    SQ_ACT_COALESCE_RESP,
    SQ_ACT_ERROR_RESP,
    SQ_ACT_EXPLICIT_NORMAL_RESP,
    SQ_ACT_DISCARD_RESP,
    SQ_ACT_DUPLICATE_RESP,
    SQ_ACT_ILLEGAL_RESP,
    SQ_ACT_FLUSH_WR,
    SQ_ACT_TIMEOUT_ERR,
    SQ_ACT_EXPLICIT_RETRY,
    SQ_ACT_IMPLICIT_RETRY,
    SQ_ACT_LOCAL_ACC_ERR,
    SQ_ACT_LOCAL_LEN_ERR,
    SQ_ACT_UNKNOWN,
  } RespActionSQ deriving(Bits, Eq, FShow);
  typedef enum {
    SQ_PRE_BUILD_STAGE,
    SQ_PRE_PROC_STAGE,
    SQ_PRE_STAGE_DONE,
  } PreStageStateSQ deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    BTH bth;
    AETH aeth;
    Bool isFirstOrOnlyPkt;
    Bool isLastOrOnlyPkt;
    Bool isReadResp;
    Bool isAtomicResp;
    Bool hasLocalErr;
    Bool shouldDiscard;
    Bool genWorkComp;
  } RespPktInfo deriving(Bits);
  typedef SizeOf#(RespPktInfo) RespPktInfo_WIDTH;
  typedef TDiv#(RespPktInfo_WIDTH, 8) RespPktInfo_BYTE_WIDTH;
  typedef struct {
    Bool isReadAtomicWR;
    Bool isMatchEndPSN;
    Bool isCoalesceResp;
    Bool isMatchStartPSN;
    Bool isPartialResp;
  } RespAndWorkReqRelation deriving(Bits);
  typedef SizeOf#(RespAndWorkReqRelation) RespAndWorkReqRelation_WIDTH;
  typedef TDiv#(RespAndWorkReqRelation_WIDTH, 8) RespAndWorkReqRelation_BYTE_WIDTH;
  typedef struct {
    Bool enoughDmaSpace;
    Bool isLastPayloadLenZero;
    ADDR nextReadRespWriteAddr;
    Length remainingReadRespLen;
  } RespLenCheckResult deriving(Bits);
  typedef SizeOf#(RespLenCheckResult) RespLenCheckResult_WIDTH;
  typedef TDiv#(RespLenCheckResult_WIDTH, 8) RespLenCheckResult_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: