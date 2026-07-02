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


Generate BSV functions for: WorkCompGen

Types already defined (import them): WorkCompGen

function ? unknown();
  // Reference implementation:
  // function Maybe#(WorkComp) genWorkComp4WorkReq(
    CntrlStatus cntrlStatus, WorkCompGenReqSQ wcGenReqSQ
);
    let wr = wcGenReqSQ.wr;
    let maybeWorkCompOpCode = workReqOpCode2WorkCompOpCode4SQ(wr.opcode);
    // TODO: how to set WC flags in SQ?
    // let wcFlags = workReqOpCode2WorkCompFlags(wr.opcode);
    let wcFlags = IBV_WC_NO_FLAGS;

    if (maybeWorkCompOpCode matches tagged Valid .opcode) begin
        let workComp = WorkComp {
            id      : wr.id,
            opcode  : opcod

function ? unknown();
  // Reference implementation:
  // function Maybe#(WorkComp) genWorkComp4RecvReq(
    CntrlStatus cntrlStatus, WorkCompGenReqRQ wcGenReqRQ
);
    let maybeWorkCompOpCode = rdmaOpCode2WorkCompOpCode4RQ(wcGenReqRQ.reqOpCode);
    let wcFlags = rdmaOpCode2WorkCompFlagsRQ(wcGenReqRQ.reqOpCode);
    if (
        maybeWorkCompOpCode matches tagged Valid .opcode &&&
        wcGenReqRQ.rrID matches tagged Valid .rrID
    ) begin
        let workComp = WorkComp {
            id      : rrID,
            opcode  : opcode,
            flags 

Output in ```bsv block. Include imports referencing existing types. Generate now: