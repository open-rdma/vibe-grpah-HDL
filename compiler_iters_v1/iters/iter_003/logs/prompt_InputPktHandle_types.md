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


Generate BSV types for: InputPktHandle


Enums:
  typedef enum {
    RDMA_PKT_BUT_ST_PRE_CHECK_FRAG,
    RDMA_PKT_BUF_ST_DISCARD_FRAG,
  } RdmaPktBufState deriving(Bits, Eq);

Structs:
  typedef struct {
    Maybe#(HandlerPD) maybePdHandler;
    QPN dqpn;
    QKEY qkeyDETH;
    Bool isCNP;
    Bool isRespPkt;
    Bool isLastPkt;
    Bool isFirstOrMidPkt;
    Bool isLastOrOnlyPkt;
  } HeaderValidateInfo deriving(Bits);
  typedef SizeOf#(HeaderValidateInfo) HeaderValidateInfo_WIDTH;
  typedef TDiv#(HeaderValidateInfo_WIDTH, 8) HeaderValidateInfo_BYTE_WIDTH;
  typedef struct {
    HandlerPD pdHandler;
    QPN dqpn;
    PMTU pmtu;
    Bool isValidHeader;
    Bool isCNP;
    Bool isRespPkt;
    Bool isLastPkt;
    Bool isFirstOrMidPkt;
    Bool isLastOrOnlyPkt;
  } ValidHeaderInfo deriving(Bits);
  typedef SizeOf#(ValidHeaderInfo) ValidHeaderInfo_WIDTH;
  typedef TDiv#(ValidHeaderInfo_WIDTH, 8) ValidHeaderInfo_BYTE_WIDTH;
  typedef struct {
    TransType trans;
    RdmaOpCode opcode;
    PAD padCnt;
    PSN psn;
    QPN dqpn;
    HeaderRDMA rdmaHeader;
    HandlerPD pdHandler;
    PktFragNum pktFragNum;
    PktLen pktLen;
    PMTU pmtu;
    Bool pktValid;
    Bool isFirstOrMidPkt;
    Bool isLastOrOnlyPkt;
  } PktLenCheckInfo deriving(Bits);
  typedef SizeOf#(PktLenCheckInfo) PktLenCheckInfo_WIDTH;
  typedef TDiv#(PktLenCheckInfo_WIDTH, 8) PktLenCheckInfo_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: