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


Generate BSV types for: RetryHandleSQ


Enums:
  typedef enum {
    RETRY_HANDLER_RESET_TIMEOUT,
    RETRY_HANDLER_RESET_RETRY_CNT_AND_TIMEOUT,
  } ResetRetryCntAndTimeOutReq deriving(Bits, Eq, FShow);
  typedef enum {
    RETRY_HANDLER_TIMEOUT_RETRY,
    RETRY_HANDLER_TIMEOUT_ERR,
  } TimeOutNotification deriving(Bits, Eq, FShow);
  typedef enum {
    RETRY_HANDLER_RECV_RETRY_REQ,
    RETRY_HANDLER_RETRY_LIMIT_EXC,
  } RetryResp deriving(Bits, Eq, FShow);
  typedef enum {
    RETRY_HANDLE_ST_NOT_RETRY,
    RETRY_HANDLE_ST_START_PRE_RETRY,
    RETRY_HANDLE_ST_RNR_CHECK,
    RETRY_HANDLE_ST_RNR_WAIT,
    RETRY_HANDLE_ST_CHECK_PARTIAL_RETRY_WR,
    RETRY_HANDLE_ST_MODIFY_PARTIAL_RETRY_WR,
    RETRY_HANDLE_ST_START_RETRY,
    RETRY_HANDLE_ST_WAIT_RETRY_DONE,
  } RetryHandleState deriving(Bits, Eq, FShow);
  typedef enum {
    RETRY_CNTRL_ST_NOT_RETRY,
    RETRY_CNTRL_ST_RETRY_LIMIT_EXC,
    RETRY_CNTRL_ST_INIT_RETRY,
    RETRY_CNTRL_ST_WAIT_RETRY_DONE,
  } RetryCntrlState deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    WorkReqID wrID;
    PSN retryStartPSN;
    RetryReason retryReason;
    Maybe#(RnrTimer) retryRnrTimer;
  } RetryReq deriving(Bits, FShow);
  typedef SizeOf#(RetryReq) RetryReq_WIDTH;
  typedef TDiv#(RetryReq_WIDTH, 8) RetryReq_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: