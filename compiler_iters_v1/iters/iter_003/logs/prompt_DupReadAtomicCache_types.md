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


Generate BSV types for: DupReadAtomicCache

Typedefs:
  typedef Bit#(PKT_NUM_WIDTH) ReadRespLastPktAddrPart;
  typedef TDiv#(ADDR_WIDTH, 2) HALF_ADDR_WIDTH;

Enums:
  typedef enum {
    DUP_READ_REQ_START_FROM_FIRST,
    DUP_READ_REQ_START_FROM_MIDDLE,
  } DupReadReqStartState deriving(Bits, Eq, FShow);

Structs:
  typedef struct {
    PSN startPSN;
    PSN endPSN;
    RETH reth;
  } ReadCacheItem deriving(Bits);
  typedef SizeOf#(ReadCacheItem) ReadCacheItem_WIDTH;
  typedef TDiv#(ReadCacheItem_WIDTH, 8) ReadCacheItem_BYTE_WIDTH;
  typedef struct {
    PSN atomicPSN;
    RdmaOpCode atomicOpCode;
    AtomicEth atomicEth;
    AtomicAckEth atomicAckEth;
  } AtomicCacheItem deriving(Bits);
  typedef SizeOf#(AtomicCacheItem) AtomicCacheItem_WIDTH;
  typedef TDiv#(AtomicCacheItem_WIDTH, 8) AtomicCacheItem_BYTE_WIDTH;
  typedef struct {
    Bool addrHighHalfMatch;
    Bool addrLowHalfMatch;
    Bool keyMatch;
    Bool psnStartExactMatch;
    Bool psnStartRangeMatch;
    Bool psnEndExactMatch;
    Bool psnEndRangeMatch;
    Bool readLenMatch;
  } DupReadCmpParts deriving(Bits);
  typedef SizeOf#(DupReadCmpParts) DupReadCmpParts_WIDTH;
  typedef TDiv#(DupReadCmpParts_WIDTH, 8) DupReadCmpParts_BYTE_WIDTH;
  typedef struct {
    Bool addrHighPartMatch;
    Bool addrLowPartMatch;
    Bool compMatch;
    Bool keyMatch;
    Bool opCodeMatch;
    Bool psnMatch;
    Bool swapMatch;
  } DupAtomicCmpParts deriving(Bits);
  typedef SizeOf#(DupAtomicCmpParts) DupAtomicCmpParts_WIDTH;
  typedef TDiv#(DupAtomicCmpParts_WIDTH, 8) DupAtomicCmpParts_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: