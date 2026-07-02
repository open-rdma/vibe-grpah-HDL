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


Generate BSV functions for: SpecialFIFOF

Types already defined (import them): SpecialFIFOF

function ? unknown();
  // Reference implementation:
  //     function Bit#(ptrSz) getNextDeqPtr();
        return popReg[1] ? (deqPtrReg + 1) : deqPtrReg;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Bool isEmpty() = emptyReg;
    function Bool  isFull() = fullReg;

    function Bool  isAlmostFull() = isAllOnesR(removeMSB(itemCnt));
    function Bool isAlmostEmpty() = isOne(itemCnt);

    (* no_implicit_conditions, fire_when_enabled *)
    rule clearAll if (clearReg[1]);
        scanOutQ.clear;

        enqPtrReg     <= 0;
        deqPtrReg     <= 0;
        itemCnt       <= 0;
        // scanCnt       <= 0; // No need to init scanCnt
        fullReg       <= False;
        empt

function ? unknown();
  // Reference implementation:
  //     function Bool isFull(
        Bit#(cntSz) nextEnqPtr, Bit#(cntSz) nextDeqPtr
    ) provisos(Add#(1, anysize, cntSz));
        return (msb(nextEnqPtr) != msb(nextDeqPtr)) &&
            (removeMSB(nextEnqPtr) == removeMSB(nextDeqPtr));
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action clearTag(Array#(Reg#(Bool)) tagReg);
        action
            tagReg[2] <= False;
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function cmpResultType compareFunc(anytype item4Search, anytype itemInQ),
    function Bool checkCompareResult(cmpResultType searchResult),
    function anytype compareResult2SearchResp(cmpResultType searchResult)
)(CacheFIFO#(qSz, anytype)) provisos(
    Bits#(anytype, tSz),
    Bits#(cmpResultType, cmpResultTypeSz),
    NumAlias#(TLog#(qSz), cntSz),
    Add#(TLog#(qSz), 1, TLog#(TAdd#(1, qSz))) // qSz must be power of 2
);
    Vector#(qSz, Reg#(anytype)) dataVec <- replicateM(mkRegU);
    

function ? unknown();
  // Reference implementation:
  //     function Bool findFunc(
        function Bool checkCompareResult(cmpResultType searchResult),
        Tuple2#(Bool, cmpResultType) zipItem
    );
        let { tag, searchResult } = zipItem;
        return tag && checkCompareResult(searchResult);
    endfunction

Output in ```bsv block. Include imports referencing existing types. Generate now: