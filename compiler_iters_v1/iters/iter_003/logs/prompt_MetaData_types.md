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


Generate BSV types for: MetaData

Typedefs:
  typedef Server#(ReqMR, RespMR) SrvPortMR;
  typedef TLog#(MAX_PD) PD_INDEX_WIDTH;
  typedef TSub#(PD_HANDLE_WIDTH, PD_INDEX_WIDTH) PD_KEY_WIDTH;
  typedef Bit#(PD_KEY_WIDTH) KeyPD;
  typedef UInt#(PD_INDEX_WIDTH) IndexPD;
  typedef Server#(ReqPD, RespPD) SrvPortPD;
  typedef TLog#(MAX_QP) QP_INDEX_WIDTH;
  typedef UInt#(QP_INDEX_WIDTH) IndexQP;
  typedef Server#(MetaDataReq, MetaDataResp) MetaDataSrv;
  typedef TExp#(11) BRAM_CACHE_SIZE;
  typedef BYTE_WIDTH BRAM_CACHE_DATA_WIDTH;
  typedef Bit#(TLog#(BRAM_CACHE_SIZE)) BramCacheAddr;
  typedef Bit#(BRAM_CACHE_DATA_WIDTH) BramCacheData;
  typedef Server#(BramCacheAddr, BramCacheData) BramRead;
  typedef Tuple2#(Bool, ADDR) FindRespTLB;
  typedef Server#(ADDR, FindRespTLB) FindInTLB;

Enums:
  typedef enum {
    TAG_VEC_RECV_REQ,
    TAG_VEC_RESP_INSERT,
    TAG_VEC_RESP_REMOVE,
  } TagVecState deriving(Bits, Eq);
  typedef enum {
    META_DATA_RECV_REQ,
    META_DATA_MR_REQ,
    META_DATA_PD_REQ,
    META_DATA_QP_REQ,
    META_DATA_MR_RESP,
    META_DATA_PD_RESP,
    META_DATA_QP_RESP,
  } MetaDataSrvState deriving(Bits, Eq);

Structs:
  typedef struct {
    ADDR laddr;
    Length len;
    FlagsType#(MemAccessTypeFlag) accFlags;
    HandlerPD pdHandler;
    KeyPartMR lkeyPart;
    KeyPartMR rkeyPart;
  } MemRegion deriving(Bits, FShow);
  typedef SizeOf#(MemRegion) MemRegion_WIDTH;
  typedef TDiv#(MemRegion_WIDTH, 8) MemRegion_BYTE_WIDTH;
  typedef struct {
    Bool allocOrNot;
    MemRegion mr;
    Bool lkeyOrNot;
    LKEY lkey;
    RKEY rkey;
  } ReqMR deriving(Bits, FShow);
  typedef SizeOf#(ReqMR) ReqMR_WIDTH;
  typedef TDiv#(ReqMR_WIDTH, 8) ReqMR_BYTE_WIDTH;
  typedef struct {
    Bool successOrNot;
    MemRegion mr;
    LKEY lkey;
    RKEY rkey;
  } RespMR deriving(Bits, FShow);
  typedef SizeOf#(RespMR) RespMR_WIDTH;
  typedef TDiv#(RespMR_WIDTH, 8) RespMR_BYTE_WIDTH;
  typedef struct {
    Bool allocOrNot;
    KeyPD pdKey;
    HandlerPD pdHandler;
  } ReqPD deriving(Bits, FShow);
  typedef SizeOf#(ReqPD) ReqPD_WIDTH;
  typedef TDiv#(ReqPD_WIDTH, 8) ReqPD_BYTE_WIDTH;
  typedef struct {
    Bool successOrNot;
    HandlerPD pdHandler;
    KeyPD pdKey;
  } RespPD deriving(Bits, FShow);
  typedef SizeOf#(RespPD) RespPD_WIDTH;
  typedef TDiv#(RespPD_WIDTH, 8) RespPD_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: