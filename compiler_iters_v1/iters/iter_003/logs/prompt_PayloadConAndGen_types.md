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


Generate BSV types for: PayloadConAndGen

Typedefs:
  typedef Server#(AddrChunkReq, AddrChunkResp) AddrChunkSrv;
  typedef Server#(DmaReadCntrlReq, DmaReadCntrlResp) DmaCntrlReadSrv;
  typedef Server#(PayloadConReq, PayloadConResp) PayloadConsumer;
  typedef Server#(AtomicOpReq, AtomicOpResp) AtomicSrv;

Enums:
  typedef enum {
    DMA_WRITE_CNTRL_IDLE,
    DMA_WRITE_CNTRL_SEND_REQ,
    DMA_WRITE_CNTRL_WAIT_RESP,
  } DmaWriteCntrlState deriving(Bits, Eq);
  typedef enum {
    PAYLOAD_GEN_NORMAL,
    PAYLOAD_GEN_WAIT_LAST_FRAG,
    PAYLOAD_GEN_WAIT_GRACEFUL_STOP,
  } PayloadGenState deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    ADDR startAddr;
    Length totalLen;
    PMTU pmtu;
  } AddrChunkReq deriving(Bits, FShow);
  typedef SizeOf#(AddrChunkReq) AddrChunkReq_WIDTH;
  typedef TDiv#(AddrChunkReq_WIDTH, 8) AddrChunkReq_BYTE_WIDTH;
  typedef struct {
    ADDR chunkAddr;
    PktLen chunkLen;
    Bool isFirst;
    Bool isLast;
  } AddrChunkResp deriving(Bits, FShow);
  typedef SizeOf#(AddrChunkResp) AddrChunkResp_WIDTH;
  typedef TDiv#(AddrChunkResp_WIDTH, 8) AddrChunkResp_BYTE_WIDTH;
  typedef struct {
    DmaReadMetaData dmaReadMetaData;
    PMTU pmtu;
  } DmaReadCntrlReq deriving(Bits, FShow);
  typedef SizeOf#(DmaReadCntrlReq) DmaReadCntrlReq_WIDTH;
  typedef TDiv#(DmaReadCntrlReq_WIDTH, 8) DmaReadCntrlReq_BYTE_WIDTH;
  typedef struct {
    DmaReadResp dmaReadResp;
    Bool isOrigFirst;
    Bool isOrigLast;
  } DmaReadCntrlResp deriving(Bits, FShow);
  typedef SizeOf#(DmaReadCntrlResp) DmaReadCntrlResp_WIDTH;
  typedef TDiv#(DmaReadCntrlResp_WIDTH, 8) DmaReadCntrlResp_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: