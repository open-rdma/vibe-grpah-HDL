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


Generate BSV functions for: Arbitration

Types already defined (import them): Arbitration

function ? unknown();
  // Reference implementation:
  // function Tuple3#(Bool, Bit#(TLog#(portSz)), Vector#(portSz, Bool)) arbitrate(
    Vector#(portSz, Bool) priorityVec, Vector#(portSz, Bool) requestVec
);
    function Bool isTrue(Bool inputVal) = inputVal;

    let portNum = valueOf(portSz);

    Vector#(portSz, Bool) grantVec = replicate(False);
    Bit#(TLog#(portSz))   grantIdx = 0;

    Bool found   = True;
    Bool granted = False;
    for (Integer x = 0; x < (2 * portNum); x = x + 1) begin
        Integer y = (x % portNum);

        let has

function ? unknown();
  // Reference implementation:
  //     function Bool isReqFinished(reqType request),
    function Bool isRespFinished(respType response)
)(Vector#(portSz, Server#(reqType, respType))) provisos(
    // FShow#(reqType), FShow#(respType),
    Bits#(reqType, reqSz),
    Bits#(respType, respSz),
    Add#(1, anysize, portSz),
    Add#(TLog#(portSz), 1, TLog#(TAdd#(1, portSz))) // portSz must be power of 2
);
    function Bool isPipePayloadFinished(Tuple2#(Bit#(TLog#(portSz)), reqType) reqWithIdx);
        let { reqIdx, inputReq } = req

function ? unknown();
  // Reference implementation:
  //     function Bool isReqFinished(reqType request),
    function Bool isRespFinished(respType response)
)(Client#(reqType, respType)) provisos(
    // FShow#(reqType), FShow#(respType),
    Bits#(reqType, reqSz),
    Bits#(respType, respSz),
    Add#(1, anysize, portSz),
    Add#(TLog#(portSz), 1, TLog#(TAdd#(1, portSz))) // portSz must be power of 2
);
    FIFOF#(reqType)   reqQ <- mkFIFOF;
    FIFOF#(respType) respQ <- mkFIFOF;

    function Bool isPipePayloadFinished(Tuple2#(Bit#(TLog#(portSz))

function ? unknown();
  // Reference implementation:
  // function Bit#(nSz) arbitrateBits(
    Bit#(nSz) priorityBits, Bit#(nSz) requestBits
); // provisos(Add#(1, anysize, nSz));
    let maskBits = priorityBits - 1;
    let maskedReqBits = requestBits & ~maskBits;
    let maskedGrantOneHot = maskedReqBits & ~(maskedReqBits - 1);
    let noMaskedGrantOneHot = requestBits & ~(requestBits - 1);
    return isZero(maskedReqBits) ? noMaskedGrantOneHot : maskedGrantOneHot;
endfunction

function ? unknown();
  // Reference implementation:
  // function Bit#(nSz) arbitrateByDoubleBits(
    Bit#(nSz) priorityBits, Bit#(nSz) requestBits
) provisos(
    Add#(1, anysizeJ, nSz),
    Add#(nSz, anysizeK, doubleSz),
    NumAlias#(TMul#(nSz, 2), doubleSz)
);
    Bit#(doubleSz) doubleMask = zeroExtend(priorityBits - 1);
    let doubleReq = { requestBits, requestBits };
    let maskedDoubleReq = doubleReq & ~doubleMask;
    let doubleGrantOneHot = maskedDoubleReq & ~(maskedDoubleReq - 1);
    Bit#(nSz) highPart = truncateLSB(doubleGrantOneHot);
 

function ? unknown();
  // Reference implementation:
  //     function Bool isPipePayloadFinished(anytype pipePayload)
)(PipeOut#(anytype)) provisos(Bits#(anytype, tSz));
    Vector#(TWO, PipeOut#(anytype)) inputPipeOutVec = vec(pipeIn1, pipeIn2);
    FIFOF#(anytype) pipeOutQ <- mkFIFOF;
    Reg#(Bool) needArbitrationReg <- mkReg(True);
    // Initial grant to LSB
    Reg#(Bool) priorityReg <- mkReg(False);
    Reg#(Bool)    grantReg <- mkReg(False);

    let shouldGrantPipeIn2 = (priorityReg && pipeIn2.notEmpty) || (!pipeIn1.notEmpty && pipeIn2.notEmp

Output in ```bsv block. Include imports referencing existing types. Generate now: