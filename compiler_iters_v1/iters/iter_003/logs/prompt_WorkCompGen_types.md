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


Generate BSV types for: WorkCompGen


Enums:
  typedef enum {
    WC_GEN_ST_STOP,
    WC_GEN_ST_NORMAL,
    WC_GEN_ST_ERR_FLUSH,
  } WorkCompGenState deriving(Bits, Eq);

Structs:
  typedef struct {
    WorkCompGenReqSQ wcGenReqSQ;
    WorkComp workComp;
    Bool isWorkCompSuccess;
    Bool needWorkCompWhenNormal;
  } PendingWorkCompSQ deriving(Bits);
  typedef SizeOf#(PendingWorkCompSQ) PendingWorkCompSQ_WIDTH;
  typedef TDiv#(PendingWorkCompSQ_WIDTH, 8) PendingWorkCompSQ_BYTE_WIDTH;
  typedef struct {
    WorkCompGenReqRQ wcGenReqRQ;
    Maybe#(WorkComp) maybeWorkComp;
    Bool isSendReq;
    Bool isWriteReq;
    Bool isWriteImmReq;
    Bool isFirstOrOnlyReq;
    Bool isLastOrOnlyReq;
    Bool isWorkCompSuccess;
    Bool needWaitDmaWriteResp;
  } PendingWorkCompRQ deriving(Bits);
  typedef SizeOf#(PendingWorkCompRQ) PendingWorkCompRQ_WIDTH;
  typedef TDiv#(PendingWorkCompRQ_WIDTH, 8) PendingWorkCompRQ_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: