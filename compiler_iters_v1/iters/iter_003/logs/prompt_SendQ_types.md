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


Generate BSV types for: SendQ

Typedefs:
  typedef TMul#(32, 1024) WQE_SLICE_MAX_SIZE;

Structs:
  typedef struct {
    MAC macAddr;
    IP ipAddr;
    PktLen pktLen;
    Bool isRawPkt;
  } PktInfo4UDP deriving(Bits, FShow);
  typedef SizeOf#(PktInfo4UDP) PktInfo4UDP_WIDTH;
  typedef TDiv#(PktInfo4UDP_WIDTH, 8) PktInfo4UDP_BYTE_WIDTH;
  typedef struct {
    HeaderData headerData;
    HeaderByteNum headerLen;
    Bool hasPayload;
    Bool hasHeader;
  } PktHeaderInfo deriving(Bits, FShow);
  typedef SizeOf#(PktHeaderInfo) PktHeaderInfo_WIDTH;
  typedef TDiv#(PktHeaderInfo_WIDTH, 8) PktHeaderInfo_BYTE_WIDTH;
  typedef struct {
    ADDR remoteAddr;
    Length totalLen;
    PSN curPSN;
    PktLen pktLen;
    PAD padCnt;
    Bool hasPayload;
    Bool ackReq;
    Bool solicited;
    Bool isFirstPkt;
    Bool isLastPkt;
    Bool isOnlyPkt;
    Bool isRawPkt;
  } HeaderGenInfo deriving(Bits, FShow);
  typedef SizeOf#(HeaderGenInfo) HeaderGenInfo_WIDTH;
  typedef TDiv#(HeaderGenInfo_WIDTH, 8) HeaderGenInfo_BYTE_WIDTH;
  typedef struct {
    ReservedZero#(0) rsvd;
  } SendResp deriving(Bits, FShow);
  typedef SizeOf#(SendResp) SendResp_WIDTH;
  typedef TDiv#(SendResp_WIDTH, 8) SendResp_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: