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


Generate BSV types for: Controller

Typedefs:
  typedef Bit#(1) Epoch;
  typedef Server#(ReqQP, RespQP) SrvPortQP;

Enums:
  typedef enum {
    REQ_QP_CREATE,
    REQ_QP_DESTROY,
    REQ_QP_MODIFY,
    REQ_QP_QUERY,
  } QpReqType deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    QpReqType qpReqType;
    HandlerPD pdHandler;
    QPN qpn;
    FlagsType#(QpAttrMaskFlag) qpAttrMask;
    AttrQP qpAttr;
    QpInitAttr qpInitAttr;
  } ReqQP deriving(Bits, FShow);
  typedef SizeOf#(ReqQP) ReqQP_WIDTH;
  typedef TDiv#(ReqQP_WIDTH, 8) ReqQP_BYTE_WIDTH;
  typedef struct {
    Bool successOrNot;
    QPN qpn;
    HandlerPD pdHandler;
    AttrQP qpAttr;
    QpInitAttr qpInitAttr;
  } RespQP deriving(Bits, FShow);
  typedef SizeOf#(RespQP) RespQP_WIDTH;
  typedef TDiv#(RespQP_WIDTH, 8) RespQP_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: