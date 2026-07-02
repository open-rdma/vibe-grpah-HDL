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


Generate BSV functions for: RespHandleSQ

Types already defined (import them): RespHandleSQ

function Bool rdmaRespMatchWorkReq(RdmaOpCode opcode, WorkReqOpCode wrOpCode);
  // Reference implementation:
  // function Bool rdmaRespMatchWorkReq(RdmaOpCode opcode, WorkReqOpCode wrOpCode);
    return case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  : (wrOpCode == IBV_WR_RDMA_READ);
        ATOMIC_ACKNOWLEDGE       : (wrOpCode == IBV_WR_ATOMIC_CMP_AND_SWP || wrOpCode == IBV_WR_ATOMIC_FETCH_AND_ADD);
        ACKNOWLEDGE              : True;
        default                  : False;
    endcase;
endfuncti

function ? unknown();
  // Reference implementation:
  // function RespActionSQ pktStatus2RespActionSQ(
    PktVeriStatus pktStatus
);
    return case (pktStatus)
        PKT_ST_VALID  : SQ_ACT_EXPLICIT_NORMAL_RESP;
        PKT_ST_LEN_ERR: SQ_ACT_ILLEGAL_RESP;
        // PKT_ST_DISCARD: SQ_ACT_DISCARD_RESP;
        default       : SQ_ACT_UNKNOWN;
    endcase;
endfunction

Output in ```bsv block. Include imports referencing existing types. Generate now: