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


Generate BSV types for: ReqGenSQ


Structs:
  typedef struct {
    PSN curPSN;
    PendingWorkReq pendingWR;
    Bool isFirstReqPkt;
    Bool isLastReqPkt;
  } ReqPktHeaderInfo deriving(Bits);
  typedef SizeOf#(ReqPktHeaderInfo) ReqPktHeaderInfo_WIDTH;
  typedef TDiv#(ReqPktHeaderInfo_WIDTH, 8) ReqPktHeaderInfo_BYTE_WIDTH;
  typedef struct {
    Bool isNewWorkReq;
    Bool isZeroPmtuResidue;
    Bool isReliableConnection;
    Bool isUnreliableDatagram;
    Bool needDmaRead;
  } WorkReqInfo deriving(Bits, FShow);
  typedef SizeOf#(WorkReqInfo) WorkReqInfo_WIDTH;
  typedef TDiv#(WorkReqInfo_WIDTH, 8) WorkReqInfo_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: