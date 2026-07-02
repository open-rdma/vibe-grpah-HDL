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


Generate BSV functions for: DupReadAtomicCache

Types already defined (import them): DupReadAtomicCache

function ? unknown();
  // Reference implementation:
  // function Tuple5#(
    Bool, Bool, Bool, ReadRespLastPktAddrPart, ReadRespLastPktAddrPart
) computeReadEndAddrAndCompare(PMTU pmtu, RETH dupReadReth, RETH origReadReth) provisos(
    Add#(RDMA_MAX_LEN_WIDTH, RDMA_MAX_LEN_WIDTH, ADDR_WIDTH)
);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) dAddrHighHalf = truncateLSB(dupReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) oAddrHighHalf = truncateLSB(origReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) dAddrLowHalf  = truncat

function ADDR getVerifiedDupReadAddr(RETH dupReadReth, RETH origReadReth);
  // Reference implementation:
  // function ADDR getVerifiedDupReadAddr(RETH dupReadReth, RETH origReadReth) provisos(
    Add#(RDMA_MAX_LEN_WIDTH, RDMA_MAX_LEN_WIDTH, ADDR_WIDTH)
);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) oAddrHighHalf = truncateLSB(origReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) dAddrLowHalf  = truncate(dupReadReth.va);

    return { oAddrHighHalf, dAddrLowHalf };
endfunction

function ? unknown();
  // Reference implementation:
  // function Bool compareDupReadAddr(
    PMTU pmtu, RETH dupReadReth, RETH origReadReth
) provisos(
    Add#(RDMA_MAX_LEN_WIDTH, RDMA_MAX_LEN_WIDTH, ADDR_WIDTH)
);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) dAddrHighHalf = truncateLSB(dupReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) oAddrHighHalf = truncateLSB(origReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) dAddrLowHalf  = truncate(dupReadReth.va);
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) oAddrLowHalf  

function ? unknown();
  // Reference implementation:
  // function Tuple2#(Bool, Bool) cmpHalfAddr(ADDR addrA, ADDR addrB);
    Bit#(HALF_ADDR_WIDTH) aAddrHighPart = truncateLSB(addrA);
    Bit#(HALF_ADDR_WIDTH) aAddrLowPart  = truncate(addrB);
    Bit#(HALF_ADDR_WIDTH) bAddrHighPart = truncateLSB(addrB);
    Bit#(HALF_ADDR_WIDTH) bAddrLowPart  = truncate(addrB);

    let addrHighPartMatch = aAddrHighPart == bAddrHighPart;
    let addrLowPartMatch  = aAddrLowPart  == bAddrLowPart;

    return tuple2(addrHighPartMatch, addrLowPartMatch);
endfunction

function ? unknown();
  // Reference implementation:
  //     function searchType firstStageFunc(anytype item4Search, anytype itemInQ),
    function cmpResultType secondStageFunc(searchType searchData),
    function Maybe#(anytype) thirdStageFunc(cmpResultType searchResult)
)(CacheFIFO#(qSz, anytype)) provisos(
    Bits#(anytype, tSz),
    Bits#(searchType, searchTypeSz),
    Bits#(cmpResultType, cmpResultTypeSz),
    NumAlias#(TLog#(qSz), cntSz),
    Add#(TLog#(qSz), 1, TLog#(TAdd#(1, qSz))) // qSz must be power of 2
);
    Vector#(qSz, Reg#(anytype))

function ? unknown();
  // Reference implementation:
  //     function Action clearCmpResultQ(FIFOF#(Maybe#(cmpResultType)) cmpResultQ);
        action
            cmpResultQ.clear;
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action clearSearchResultQ(FIFOF#(Maybe#(anytype)) searchResultQ);
        action
            searchResultQ.clear;
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action firstMapFunc(
        function searchType mapFunc(anytype item4Cmp),
        Tuple3#(Bool, anytype, FIFOF#(Tuple2#(Bool, searchType))) zip3Item
    );
        action
            let { tag, itemInQ, searchDataQ } = zip3Item;
            let searchData = mapFunc(itemInQ);
            searchDataQ.enq(tuple2(tag, searchData));
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action duplicateSearchReq(anytype item4Cmp, FIFOF#(anytype) dupSearchReqQ);
        action
            dupSearchReqQ.enq(item4Cmp);
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Tuple6#(
        PMTU, Bool, Bool, Bool, ReadCacheItem, ReadCacheItem
    ) buildDupReadSearchData(
        PMTU pmtu, ReadCacheItem dupReadCacheItem, ReadCacheItem origReadCacheItem
    );
        let dupReadReth  = dupReadCacheItem.reth;
        let origReadReth = origReadCacheItem.reth;
        let dupStartPSN  = dupReadCacheItem.startPSN;
        let dupEndPSN    = dupReadCacheItem.endPSN;
        let origStartPSN = origReadCacheItem.startPSN;
        let origEndPSN   = origRead

function ? unknown();
  // Reference implementation:
  //     function Tuple4#(
        DupReadCmpParts, ReadRespLastPktAddrPart, ReadRespLastPktAddrPart, ReadCacheItem
    ) compareReadCacheItem(
        Tuple6#(PMTU, Bool, Bool, Bool, ReadCacheItem, ReadCacheItem) searchData
    );
        let {
            pmtu, psnStartExactMatch, psnEndExactMatch,
            keyMatch, dupReadCacheItem, origReadCacheItem
        } = searchData;

        let dupReadReth  = dupReadCacheItem.reth;
        let origReadReth = origReadCacheItem.reth;
        let dupStar

function ? unknown();
  // Reference implementation:
  //     function Maybe#(ReadCacheItem) checkReadCacheItemCmpResult(
        Tuple4#(
            DupReadCmpParts, ReadRespLastPktAddrPart, ReadRespLastPktAddrPart, ReadCacheItem
        ) cmpResult
    );
        let {
            dupReadCmpParts, dupReadLastPktAddrPart, origReadLastPktAddrPart, origReadCacheItem
        } = cmpResult;

        let addrHighHalfMatch  = dupReadCmpParts.addrHighHalfMatch;
        let addrLowHalfMatch   = dupReadCmpParts.addrLowHalfMatch;
        let keyMatch          

function ? unknown();
  // Reference implementation:
  //     function Tuple5#(Bool, Bool, Bool, AtomicCacheItem, AtomicCacheItem) buildAtomicSearchData(
        AtomicCacheItem dupAtomicCacheItem, AtomicCacheItem origAtomicCacheItem
    );
        let dupAtomicOpCode  = dupAtomicCacheItem.atomicOpCode;
        let origAtomicOpCode = origAtomicCacheItem.atomicOpCode;
        let dupAtomicEth     = dupAtomicCacheItem.atomicEth;
        let origAtomicEth    = origAtomicCacheItem.atomicEth;


        let keyMatch    = dupAtomicEth.rkey == origAtomicEth.rk

function ? unknown();
  // Reference implementation:
  //     function Tuple2#(DupAtomicCmpParts, AtomicCacheItem) compareAtomicCacheItem(
        Tuple5#(Bool, Bool, Bool, AtomicCacheItem, AtomicCacheItem) searchData
    );
        let {
            keyMatch, opCodeMatch, psnMatch, dupAtomicCacheItem, origAtomicCacheItem
        } = searchData;

        let dupAtomicEth  = dupAtomicCacheItem.atomicEth;
        let origAtomicEth = origAtomicCacheItem.atomicEth;

        let { addrHighPartMatch, addrLowPartMatch } = cmpHalfAddr(
            dupAtomicEth

function ? unknown();
  // Reference implementation:
  //     function Maybe#(AtomicCacheItem) checkAtomicCacheItemCmpResult(
        Tuple2#(DupAtomicCmpParts, AtomicCacheItem) cmpResult
    );
        let { dupAtomicCmpParts, origAtomicCacheItem } = cmpResult;
        let origAtomicOpCode = origAtomicCacheItem.atomicOpCode;

        let addrHighPartMatch = dupAtomicCmpParts.addrHighPartMatch;
        let addrLowPartMatch  = dupAtomicCmpParts.addrLowPartMatch;
        let keyMatch          = dupAtomicCmpParts.keyMatch;
        let opCodeMatch       = 

Output in ```bsv block. Include imports referencing existing types. Generate now: