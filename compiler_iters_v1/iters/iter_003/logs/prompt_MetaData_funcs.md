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


Generate BSV functions for: MetaData

Types already defined (import them): MetaData

function ? unknown();
  // Reference implementation:
  //     function Tuple2#(LKEY, RKEY) genLocalAndRmtKey(IndexMR mrIndex, MemRegion mr);
        LKEY lkey = { pack(mrIndex), mr.lkeyPart };
        RKEY rkey = { pack(mrIndex), mr.rkeyPart };
        return tuple2(lkey, rkey);
    endfunction

function IndexPD getIndexPD(HandlerPD pdHandler);
  // Reference implementation:
  // function IndexPD getIndexPD(HandlerPD pdHandler) = unpack(truncateLSB(pdHandler));

module mkMetaDataPDs(MetaDataPDs);
    TagVecSrv#(MAX_PD, KeyPD) pdTagVec <- mkTagVecSrv;
    Vector#(MAX_PD, MetaDataMRs) pdMrVec <- replicateM(mkMetaDataMRs);

    function Action clearAllMRs(MetaDataMRs mrMetaData);
        action
            mrMetaData.clear;
        endaction
    endfunction

function IndexQP getIndexQP(QPN qpn);
  // Reference implementation:
  // function IndexQP getIndexQP(QPN qpn) = unpack(truncateLSB(qpn));

function QPN genQPN(IndexQP qpIndex, HandlerPD pdHandler);
    return { pack(qpIndex), truncate(pdHandler) };
endfunction

function ? unknown();
  // Reference implementation:
  //     function Bool checkPermByMR(PermCheckReq permCheckReq, MemRegion mr);
        let keyMatch = case (permCheckReq.localOrRmtKey)
            True : (truncate(permCheckReq.lkey) == mr.lkeyPart);
            False: (truncate(permCheckReq.rkey) == mr.rkeyPart);
        endcase;

        let accTypeMatch = compareAccessTypeFlags(mr.accFlags, permCheckReq.accFlags);

        let addrLenMatch = checkAddrAndLenWithinRange(
            permCheckReq.reqAddr, permCheckReq.totalLen, mr.laddr, mr.len
    

function ? unknown();
  // Reference implementation:
  //     function Maybe#(MemRegion) mrSearchByLKey(
        MetaDataPDs pdMetaData, HandlerPD pdHandler, LKEY lkey
    );
        let maybeMR = tagged Invalid;
        let maybeMRs = pdMetaData.getMRs4PD(pdHandler);
        if (maybeMRs matches tagged Valid .mrMetaData) begin
            maybeMR = mrMetaData.getMemRegionByLKey(lkey);
        end
        return maybeMR;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Maybe#(MemRegion) mrSearchByRKey(
        MetaDataPDs pdMetaData, HandlerPD pdHandler, RKEY rkey
    );
        let maybeMR = tagged Invalid;
        let maybeMRs = pdMetaData.getMRs4PD(pdHandler);
        if (maybeMRs matches tagged Valid .mrMetaData) begin
            maybeMR = mrMetaData.getMemRegionByRKey(rkey);
        end
        return maybeMR;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function BramCacheAddr getBramCacheIndex(Bit#(addrWidth) cacheAddr);
        return truncate(cacheAddr); // [valueOf(bramCacheIndexWidth) - 1 : 0];
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Bit#(cascadeCacheIndexWidth) getCascadeCacheIndex(Bit#(addrWidth) cacheAddr);
        return truncateLSB(cacheAddr); // [valueOf(addrWidth) - 1 : valueOf(bramCacheIndexWidth)];
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action readReqHelper(BramCacheAddr bramCacheIndex, BramCache bramCache);
        action
            bramCache.read.request.put(bramCacheIndex);
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function ActionValue#(BramCacheData) readRespHelper(BramCache bramCache);
        actionvalue
            let bramCacheReadRespData <- bramCache.read.response.get;
            return bramCacheReadRespData;
        endactionvalue
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action writeHelper(
        BramCacheAddr bramCacheIndex, Tuple2#(BramCache, BramCacheData) tupleInput
    );
        action
            let { bramCache, writeData } = tupleInput;
            bramCache.write(bramCacheIndex, writeData);
        endaction
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Bit#(payloadWidth) concatBitVec(BramCacheData bramCacheData, Bit#(payloadWidth) concatResult);
        return truncate({ concatResult, bramCacheData });
    endfunction

function Bit#(PAGE_OFFSET_WIDTH) getPageOffset(ADDR addr);
  // Reference implementation:
  // function Bit#(PAGE_OFFSET_WIDTH) getPageOffset(ADDR addr);
    return truncate(addr);
endfunction

function ? unknown();
  // Reference implementation:
  // function ADDR restorePA(
    Bit#(TLB_CACHE_PA_DATA_WIDTH) paData, Bit#(PAGE_OFFSET_WIDTH) pageOffset
);
    return signExtend({ paData, pageOffset });
endfunction

function Bit#(TLB_CACHE_PA_DATA_WIDTH) getData4PA(ADDR pa);
  // Reference implementation:
  // function Bit#(TLB_CACHE_PA_DATA_WIDTH) getData4PA(ADDR pa);
    return truncate(pa >> valueOf(PAGE_OFFSET_WIDTH));
endfunction

function ? unknown();
  // Reference implementation:
  //     function Bit#(TLB_CACHE_INDEX_WIDTH) getIndex4TLB(ADDR va);
        return truncate(va >> valueOf(PAGE_OFFSET_WIDTH));
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Bit#(TLB_CACHE_TAG_WIDTH) getTag4TLB(ADDR va);
        return truncate(va >> valueOf(TAdd#(TLB_CACHE_INDEX_WIDTH, PAGE_OFFSET_WIDTH)));
    endfunction

Output in ```bsv block. Include imports referencing existing types. Generate now: