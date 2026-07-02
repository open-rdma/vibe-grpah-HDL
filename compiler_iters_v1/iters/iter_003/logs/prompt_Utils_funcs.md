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


Generate BSV functions for: Utils

Types already defined (import them): Utils

function Integer getRnrTimeOutValue(RnrTimer rnrTimer);
  // Reference implementation:
  // function Integer getRnrTimeOutValue(RnrTimer rnrTimer);
    // RNR timeout value in microseconds
    Integer rnrTimeOutValues[32] = {
        valueOf(TDiv#(TMul#(655360, 1000), TARGET_CYCLE_NS)),
        valueOf(TDiv#(TMul#(10,     1000), TARGET_CYCLE_NS)),
        valueOf(TDiv#(TMul#(20,     1000), TARGET_CYCLE_NS)),
        valueOf(TDiv#(TMul#(30,     1000), TARGET_CYCLE_NS)),
        valueOf(TDiv#(TMul#(40,     1000), TARGET_CYCLE_NS)),
        valueOf(TDiv#(TMul#(60,     1000), TARGET_CYCLE_

function Integer getTimeOutValue(TimeOutTimer timeOutTimer);
  // Reference implementation:
  // function Integer getTimeOutValue(TimeOutTimer timeOutTimer);
    // Timeout value in nanoseconds
    return case (timeOutTimer)
         1     : valueOf(TDiv#(TMul#(8192, TExp#( 0)), TARGET_CYCLE_NS));
         2     : valueOf(TDiv#(TMul#(8192, TExp#( 1)), TARGET_CYCLE_NS));
         3     : valueOf(TDiv#(TMul#(8192, TExp#( 2)), TARGET_CYCLE_NS));
         4     : valueOf(TDiv#(TMul#(8192, TExp#( 3)), TARGET_CYCLE_NS));
         5     : valueOf(TDiv#(TMul#(8192, TExp#( 4)), TARGET_CYCLE_NS));
  

function ByteEn genByteEn(ByteEnBitNum fragValidByteNum);
  // Reference implementation:
  // function ByteEn genByteEn(ByteEnBitNum fragValidByteNum);
    return reverseBits((1 << fragValidByteNum) - 1);
endfunction

function ByteEnBitNum calcLastFragValidByteNum(Bit#(nSz);
  // Reference implementation:
  // function ByteEnBitNum calcLastFragValidByteNum(Bit#(nSz) len) provisos(
    Add#(TAdd#(1, DATA_BUS_BYTE_NUM_WIDTH), anysizeK, nSz),
    Add#(DATA_BUS_BYTE_NUM_WIDTH, anysizeJ, nSz)
);
    BusByteWidthMask lastFragByteNumResidue = truncate(len);
    Bit#(TSub#(nSz, DATA_BUS_BYTE_NUM_WIDTH)) truncatedLen = truncateLSB(len);

    ByteEnBitNum lastFragValidByteNum = zeroExtend(lastFragByteNumResidue);
    if (isZeroR(lastFragByteNumResidue) && !isZeroR(truncatedLen)) begin
    // BusByteWidthMask bu

function ? unknown();
  // Reference implementation:
  // function Tuple3#(BusBitNum, ByteEnBitNum, BusBitNum) calcFragBitNumAndByteNum(
    ByteEnBitNum fragValidByteNum
);
    BusBitNum fragValidBitNum = zeroExtend(fragValidByteNum) << 3;
    ByteEnBitNum fragInvalidByteNum =
        fromInteger(valueOf(DATA_BUS_BYTE_WIDTH)) - fragValidByteNum;
    BusBitNum fragInvalidBitNum = zeroExtend(fragInvalidByteNum) << 3;

    return tuple3(fragValidBitNum, fragInvalidByteNum, fragInvalidBitNum);
endfunction

function Maybe#(ByteEnBitNum) calcFragByteNumFromByteEn(ByteEn fragByteEn);
  // Reference implementation:
  // function Maybe#(ByteEnBitNum) calcFragByteNumFromByteEn(ByteEn fragByteEn);
    let rightAlignedByteEn = reverseBits(fragByteEn);
    Maybe#(ByteEnBitNum) byteEnBitNum = tagged Invalid;
    let step = valueOf(FRAG_MIN_VALID_BYTE_NUM);
    // Bool matched = False;
    for (
        Integer idx = 0;
        idx <= valueOf(DATA_BUS_BYTE_WIDTH);
        idx = idx + step
    ) begin
        if (rightAlignedByteEn == (fromInteger(1) << idx) - 1) begin
            byteEnBitNum = tagged Valid fromIntege

function Integer getPmtuLogValue(PMTU pmtu);
  // Reference implementation:
  // function Integer getPmtuLogValue(PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 :  8; // log2(256)
        IBV_MTU_512 :  9; // log2(512)
        IBV_MTU_1024: 10; // log2(1024)
        IBV_MTU_2048: 11; // log2(2048)
        IBV_MTU_4096: 12; // log2(4096)
    endcase;
endfunction

function PktLen calcPmtuLen(PMTU pmtu);
  // Reference implementation:
  // function PktLen calcPmtuLen(PMTU pmtu);
    return fromInteger(case (pmtu)
        IBV_MTU_256 :  256;
        IBV_MTU_512 :  512;
        IBV_MTU_1024: 1024;
        IBV_MTU_2048: 2048;
        IBV_MTU_4096: 4096;
    endcase);
endfunction

function Bool pktLenEqPMTU(PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Bool pktLenEqPMTU(PktLen pktLen, PMTU pmtu);
    let tmpPktLen = pktLen;
    let idx = getPmtuLogValue(pmtu);
    tmpPktLen[idx] = 0;
    return isZero(tmpPktLen);
endfunction

function Bool pktLenGtPMTU(PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Bool pktLenGtPMTU(PktLen pktLen, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            (pktLen[8] == 1 && !isZero(pktLen[7: 0]));
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            (pktLen[9] == 1 && !isZero(pktLen[8: 0]));
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            (pktLen[10] == 1 && !isZero(pktLen[9: 0]));
        end
        IBV_MTU_2048: begin
            // 11 = 

function PktFragNum calcFragNumByPMTU(PMTU pmtu);
  // Reference implementation:
  // function PktFragNum calcFragNumByPMTU(PMTU pmtu) provisos(
    // Check DATA_BUS_BYTE_WIDTH must be power of 2
    Add#(TLog#(DATA_BUS_BYTE_WIDTH), 1, TLog#(TAdd#(1, DATA_BUS_BYTE_WIDTH)))
);
    let busByteWidth = valueOf(TLog#(DATA_BUS_BYTE_WIDTH));
    let pmtuWidth = getPmtuLogValue(pmtu);
    let shiftAmt = pmtuWidth - busByteWidth;
    return 1 << shiftAmt;
endfunction

function HeaderByteEn genHeaderByteEn(HeaderByteNum headerLen);
  // Reference implementation:
  // function HeaderByteEn genHeaderByteEn(HeaderByteNum headerLen);
    return reverseBits((1 << headerLen) - 1);
endfunction

function ? unknown();
  // Reference implementation:
  // function Tuple2#(HeaderFragNum, ByteEnBitNum) calcHeaderFragNumAndLastFragValidByeNum(
    HeaderByteNum headerLen
) provisos(
    Add#(HEADER_FRAG_NUM_WIDTH, DATA_BUS_BYTE_NUM_WIDTH, HEADER_MAX_BYTE_NUM_WIDTH)
);
    let headerLastFragValidByteNum = calcLastFragValidByteNum(headerLen);
    // BusByteWidthMask busByteWidthMask = maxBound;
    // let headerLastFragByteEnBitNum = truncate(headerLen) & busByteWidthMask;
    // HeaderFragNum headerFragNum =
    //     truncate(headerLen >> valueOf(D

function ? unknown();
  // Reference implementation:
  // function HeaderMetaData genHeaderMetaData(
    HeaderByteNum headerLen,
    Bool hasPayload
);
    let { headerFragNum, lastFragValidByteNum } =
        calcHeaderFragNumAndLastFragValidByeNum(headerLen);
    let headerMetaData = HeaderMetaData {
        headerLen: headerLen,
        headerFragNum: headerFragNum,
        lastFragValidByteNum: lastFragValidByteNum,
        hasPayload: hasPayload,
        isEmptyHeader : False
    };
    return headerMetaData;
endfunction

function ? unknown();
  // Reference implementation:
  // function HeaderRDMA genHeaderRDMA(
    HeaderData headerData,
    HeaderByteNum headerLen,
    Bool hasPayload
);
    let headerByteEn = genHeaderByteEn(headerLen);
    let headerMetaData = genHeaderMetaData(headerLen, hasPayload);
    return HeaderRDMA {
        headerData    : headerData,
        headerByteEn  : headerByteEn,
        headerMetaData: headerMetaData
    };
endfunction

function HeaderRDMA genEmptyHeaderRDMA(Bool hasPayload);
  // Reference implementation:
  // function HeaderRDMA genEmptyHeaderRDMA(Bool hasPayload);
    let emptyHeaderMetaData = HeaderMetaData {
        headerLen           : 0,
        headerFragNum       : 0,
        lastFragValidByteNum: 0,
        hasPayload          : hasPayload,
        isEmptyHeader       : True
    };
    return HeaderRDMA {
        headerData    : dontCareValue,
        headerByteEn  : 0,
        headerMetaData: emptyHeaderMetaData
    };
endfunction

function ? unknown();
  // Reference implementation:
  // function Tuple2#(HeaderByteNum, HeaderBitNum) calcHeaderInvalidFragByteAndBitNum(
    HeaderFragNum headerValidFragNum
);
    HeaderFragNum headerInvalidFragNum =
        fromInteger(valueOf(HEADER_MAX_FRAG_NUM)) - headerValidFragNum;
    HeaderByteNum headerInvalidFragByteNum =
        zeroExtend(headerInvalidFragNum) << valueOf(DATA_BUS_BYTE_NUM_WIDTH);
    HeaderBitNum headerInvalidFragBitNum =
        zeroExtend(headerInvalidFragNum) << valueOf(DATA_BUS_BIT_NUM_WIDTH);
    return tuple2(head

function ? unknown();
  // Reference implementation:
  // function Bool compareAccessTypeFlags(
    FlagsType#(MemAccessTypeFlag) flags1, FlagsType#(MemAccessTypeFlag) flags2
);
    return containFlags(flags1, flags2);
    // return !isZero(pack(flags1 & flags2));
endfunction

function ? unknown();
  // Reference implementation:
  // function Bool containAccessTypeFlag(
    FlagsType#(MemAccessTypeFlag) flags, MemAccessTypeFlag flag
);
    return containEnum(flags, flag);
    // return !isZero(pack(flags & enum2Flag(flag)));
endfunction

function Bool psnInRangeExclusive(PSN psn, PSN psnStart, PSN psnEnd);
  // Reference implementation:
  // function Bool psnInRangeExclusive(PSN psn, PSN psnStart, PSN psnEnd);
    let result = False;
    let psnGtStart = psnStart < psn;
    let psnLtEnd = psn < psnEnd;

    if (msb(psnStart) == msb(psnEnd)) begin
        // PSN range no wrap around
        result = psnGtStart && psnLtEnd;
    end
    else begin
        // PSN range has wrap around max PSN
        result = (psnGtStart && msb(psnStart) == msb(psn)) ||
            (psnLtEnd && msb(psn) == msb(psnEnd));
    end
    return result;
endfun

function PSN calcOldestValidPsn4RQ(PSN ePSN);
  // Reference implementation:
  // function PSN calcOldestValidPsn4RQ(PSN ePSN);
    // PSN - 2^23
    return { ~msb(ePSN), removeMSB(ePSN) };
endfunction

function PSN calcPsnDiff(PSN psnA, PSN psnB);
  // Reference implementation:
  // function PSN calcPsnDiff(PSN psnA, PSN psnB);
    return truncate({ 1'b1, psnA } - { 1'b0, psnB });
endfunction

function Bool isDefaultPKEY(PKEY pkey);
  // Reference implementation:
  // function Bool isDefaultPKEY(PKEY pkey);
    return isAllOnesR(pkey);
endfunction

function IndexMR key2IndexMR(Bit#(nSz);
  // Reference implementation:
  // function IndexMR key2IndexMR(Bit#(nSz) key) provisos(
    Add#(KEY_WIDTH, 0, nSz)
);
    return unpack(truncateLSB(key));
endfunction

function ADDR addrAddPsnMultiplyPMTU(ADDR addr, PSN psn, PMTU pmtu);
  // Reference implementation:
  // function ADDR addrAddPsnMultiplyPMTU(ADDR addr, PSN psn, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            { (addr[valueOf(ADDR_WIDTH)-1 : 8] + zeroExtend(psn)), addr[7 : 0] };
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            { (addr[valueOf(ADDR_WIDTH)-1 : 9] + zeroExtend(psn)), addr[8 : 0] };
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            { (addr[valueOf(ADDR_WIDTH)-1 : 10]

function Length lenSubtractPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
  // Reference implementation:
  // function Length lenSubtractPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            { (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 8] - psn), len[7 : 0] };
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            { (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9] - truncate(psn)), len[8 : 0] };
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            { (len[valueOf(RDMA_MAX_LEN_WI

function Length lenAddPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
  // Reference implementation:
  // function Length lenAddPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            { (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 8] + psn), len[7 : 0] };
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            { (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9] + truncate(psn)), len[8 : 0] };
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            { (len[valueOf(RDMA_MAX_LEN_WIDTH)-

function Length lenSubtractPktLen(Length len, PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Length lenSubtractPktLen(Length len, PktLen pktLen, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            { len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9], (len[8 : 0] - truncate(pktLen)) };
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            { len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 10], (len[9 : 0] - truncate(pktLen)) };
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            { len[valueOf(RD

function Length lenAddPktLen(Length len, PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Length lenAddPktLen(Length len, PktLen pktLen, PMTU pmtu);
    let oneAsPSN = 1;
    return pktLenEqPMTU(pktLen, pmtu) ?
        lenAddPsnMultiplyPMTU(len, oneAsPSN, pmtu) :
        case (pmtu)
            IBV_MTU_256 : begin
                // 8 = log2(256)
                { len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 8], pktLen[7 : 0] };
            end
            IBV_MTU_512 : begin
                // 9 = log2(512)
                { len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9], pktLen[8 : 0] };
 

function Bool lenGtEqPktLen(Length len, PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Bool lenGtEqPktLen(Length len, PktLen pktLen, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 9)) lenHighPart = truncateLSB(len); // [valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9];
            (!isZeroR(lenHighPart) || (len[8 : 0] >= pktLen[8 : 0]));
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 10)) lenHighPart = truncateLSB(len); // [valueOf(RDM

function Bool lenGtEqPktLen4LastOrOnlyPkt(Length len, PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Bool lenGtEqPktLen4LastOrOnlyPkt(Length len, PktLen pktLen, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            (len[8 : 0] >= pktLen[8 : 0]);
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            (len[9 : 0] >= pktLen[9 : 0]);
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            (len[10 : 0] >= pktLen[10 : 0]);
        end
        IBV_MTU_2048: begin
            // 11 = log2(204

function Bool lenEqPktLen(Length len, PktLen pktLen, PMTU pmtu);
  // Reference implementation:
  // function Bool lenEqPktLen(Length len, PktLen pktLen, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 9)) lenHighPart = truncateLSB(len); // [valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9];
            (isZero(lenHighPart) && (len[8 : 0] == pktLen[8 : 0]));
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 10)) lenHighPart = truncateLSB(len); // [valueOf(RDMA_MA

function Bool lenGtEqPMTU(Length len, PMTU pmtu);
  // Reference implementation:
  // function Bool lenGtEqPMTU(Length len, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 8)) lenHighPart = truncateLSB(len); // [valueOf(RDMA_MAX_LEN_WIDTH)-1 : 8];
            (!isZeroR(lenHighPart)); // truncate len[7 : 0]
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 9)) lenHighPart = truncateLSB(len); // [valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9];
   

function Bool lenGtEqPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
  // Reference implementation:
  // function Bool lenGtEqPsnMultiplyPMTU(Length len, PSN psn, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            // 8 = log2(256)
            (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 8] >= psn);
        end
        IBV_MTU_512 : begin
            // 9 = log2(512)
            (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 9] >= psn);
        end
        IBV_MTU_1024: begin
            // 10 = log2(1024)
            (len[valueOf(RDMA_MAX_LEN_WIDTH)-1 : 10] >= psn);
        end
        IBV_MT

function PktLen pktLenAddBusByteWidth(PktLen pktLen);
  // Reference implementation:
  // function PktLen pktLenAddBusByteWidth(PktLen pktLen);
    Bit#(DATA_BUS_BYTE_NUM_WIDTH) lowerPart = truncate(pktLen);
    Bit#(TSub#(PKT_LEN_WIDTH, DATA_BUS_BYTE_NUM_WIDTH)) higherPart = truncateLSB(pktLen);
    return { (higherPart + 1), lowerPart };
endfunction

function Bool fragLenEqBusByteWidth(ByteEnBitNum fragLen);
  // Reference implementation:
  // function Bool fragLenEqBusByteWidth(ByteEnBitNum fragLen);
    let tmpFragLen = fragLen;
    let idx = valueOf(DATA_BUS_BYTE_NUM_WIDTH);
    tmpFragLen[idx] = 0;
    return isZero(tmpFragLen);
endfunction

function PktLen pktLenAddFragLen(PktLen pktLen, ByteEnBitNum fragLen);
  // Reference implementation:
  // function PktLen pktLenAddFragLen(PktLen pktLen, ByteEnBitNum fragLen);
    Bit#(DATA_BUS_BYTE_NUM_WIDTH) lowerPartFragLen = truncate(fragLen);
    Bit#(TSub#(PKT_LEN_WIDTH, DATA_BUS_BYTE_NUM_WIDTH)) higherPartPktLen = truncateLSB(pktLen);
    return fragLenEqBusByteWidth(fragLen) ?
        pktLenAddBusByteWidth(pktLen) :
        { higherPartPktLen, lowerPartFragLen };
endfunction

function Bool checkAddrAndLenWithinRange(ADDR laddr, Length dlen, ADDR raddr, Length rlen);
  // Reference implementation:
  // function Bool checkAddrAndLenWithinRange(ADDR laddr, Length dlen, ADDR raddr, Length rlen);
    // Integer addrMSB        = valueOf(ADDR_WIDTH) - 1;
    // Integer addrMidHighBit = valueOf(ADDR_WIDTH) - valueOf(RDMA_MAX_LEN_WIDTH);
    // Integer addrMidLowBit  = valueOf(ADDR_WIDTH) - valueOf(RDMA_MAX_LEN_WIDTH) - 1;

    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) lAddrHighPart = truncateLSB(laddr); // [addrMSB : addrMidHighBit];
    Bit#(TSub#(ADDR_WIDTH, RDMA_MAX_LEN_WIDTH)) rAddrHighPart = t

function Maybe#(TransType) qpType2TransType(TypeQP qpt);
  // Reference implementation:
  // function Maybe#(TransType) qpType2TransType(TypeQP qpt);
    return case (qpt)
        IBV_QPT_RC        : tagged Valid TRANS_TYPE_RC;
        IBV_QPT_UC        : tagged Valid TRANS_TYPE_UC;
        IBV_QPT_UD        : tagged Valid TRANS_TYPE_UD;
        IBV_QPT_XRC_RECV  ,
        IBV_QPT_XRC_SEND  : tagged Valid TRANS_TYPE_XRC;
        default           : tagged Invalid;
    endcase;
endfunction

function Bool transTypeMatchQpType(TransType tt, TypeQP qpt, Bool isRecvSide);
  // Reference implementation:
  // function Bool transTypeMatchQpType(TransType tt, TypeQP qpt, Bool isRecvSide);
    return case (tt)
        TRANS_TYPE_CNP: True;
        TRANS_TYPE_RC : (qpt == IBV_QPT_RC);
        TRANS_TYPE_UC : (qpt == IBV_QPT_UC);
        TRANS_TYPE_UD : (qpt == IBV_QPT_UD);
        TRANS_TYPE_XRC: (
            (!isRecvSide && qpt == IBV_QPT_XRC_RECV) ||
            (isRecvSide && qpt == IBV_QPT_XRC_SEND)
        );
        default: False;
    endcase;
endfunction

function Bool qpNeedGenResp(TransType transType);
  // Reference implementation:
  // function Bool qpNeedGenResp(TransType transType);
    return case (transType)
        TRANS_TYPE_RC ,
        TRANS_TYPE_XRC,
        TRANS_TYPE_RD : True;
        // TRANS_TYPE_UC ,
        // TRANS_TYPE_UD ,
        default       : False;
    endcase;
endfunction

function Bool isRawPktTypeQP(TypeQP qpType);
  // Reference implementation:
  // function Bool isRawPktTypeQP(TypeQP qpType);
    return qpType == IBV_QPT_RAW_PACKET;
endfunction

function Bool isSupportedReqOpCodeRQ(TypeQP qpt, RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isSupportedReqOpCodeRQ(TypeQP qpt, RdmaOpCode opcode);
    case (qpt)
        IBV_QPT_UC: return case (opcode)
            SEND_FIRST                    ,
            SEND_MIDDLE                   ,
            SEND_LAST                     ,
            SEND_LAST_WITH_IMMEDIATE      ,
            SEND_ONLY                     ,
            SEND_ONLY_WITH_IMMEDIATE      : True;
            RDMA_WRITE_FIRST              ,
            RDMA_WRITE_MIDDLE             ,
            RDMA_

function PAD calcPadCnt(Bit#(nSz);
  // Reference implementation:
  // function PAD calcPadCnt(Bit#(nSz) len) provisos(
    Add#(PAD_WIDTH, anysize, nSz)
);
    // PadMask padMask = maxBound;
    // PAD tmpCnt = truncate(len) & padMask;
    PAD tmpCnt = truncate(len);
    PAD padCnt = (1 << valueOf(PAD_WIDTH)) - tmpCnt;
    return padCnt;
endfunction

function ? unknown();
  // Reference implementation:
  // function Tuple2#(TransType, RdmaOpCode) extractTranTypeAndRdmaOpCode(
    Bit#(nSz) inputData
);
    TransType transType = unpack(inputData[
        valueOf(nSz)-1 :
        valueOf(nSz) - valueOf(TRANS_TYPE_WIDTH)
    ]);
    RdmaOpCode rdmaOpCode = unpack(inputData[
        valueOf(nSz) - valueOf(TRANS_TYPE_WIDTH) - 1 :
        valueOf(nSz) - valueOf(TRANS_TYPE_WIDTH) - valueOf(RDMA_OPCODE_WIDTH)
    ]);

    return tuple2(transType, rdmaOpCode);
endfunction

function BTH extractBTH(HeaderData headerData);
  // Reference implementation:
  // function BTH extractBTH(HeaderData headerData);
    let bth = unpack(headerData[
        valueOf(HEADER_MAX_DATA_WIDTH)-1 :
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH)
    ]);
    return bth;
endfunction

function AETH extractAETH(HeaderData headerData);
  // Reference implementation:
  // function AETH extractAETH(HeaderData headerData);
    let aeth = unpack(headerData[
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(AETH_WIDTH)
    ]);
    return aeth;
endfunction

function AtomicAckEth extractAtomicAckEth(HeaderData headerData);
  // Reference implementation:
  // function AtomicAckEth extractAtomicAckEth(HeaderData headerData);
    let atomicAckEth = unpack(headerData[
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(AETH_WIDTH) -1 :
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(AETH_WIDTH) - valueOf(ATOMIC_ACK_ETH_WIDTH)
    ]);
    return atomicAckEth;
endfunction

function XRCETH extractXRCETH(HeaderData headerData);
  // Reference implementation:
  // function XRCETH extractXRCETH(HeaderData headerData);
    let xrceth = unpack(headerData[
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH)
    ]);
    return xrceth;
endfunction

function RETH extractRETH(HeaderData headerData, TransType transType);
  // Reference implementation:
  // function RETH extractRETH(HeaderData headerData, TransType transType);
    let reth = case (transType)
        TRANS_TYPE_XRC: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) -1 :
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(RETH_WIDTH)
        ]);
        default: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
            valueOf(HEADER_MAX_DAT

function LETH extractLETH(HeaderData headerData, TransType transType);
  // Reference implementation:
  // function LETH extractLETH(HeaderData headerData, TransType transType);
    let reth = case (transType)
        TRANS_TYPE_XRC: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(RETH_WIDTH) -1 :
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(RETH_WIDTH) - valueOf(LETH_WIDTH)
        ]);
        default: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WI

function AtomicEth extractAtomicEth(HeaderData headerData, TransType transType);
  // Reference implementation:
  // function AtomicEth extractAtomicEth(HeaderData headerData, TransType transType);
    let atomicEth = case (transType)
        TRANS_TYPE_XRC: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) -1 :
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(ATOMIC_ETH_WIDTH)
        ]);
        default: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
            v

function DETH extractDETH(HeaderData headerData);
  // Reference implementation:
  // function DETH extractDETH(HeaderData headerData);
    let deth = unpack(headerData[
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
        valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(DETH_WIDTH)
    ]);
    return deth;
endfunction

function Bool isAlignedAtomicAddr(ADDR atomicAddr);
  // Reference implementation:
  // function Bool isAlignedAtomicAddr(ADDR atomicAddr);
    AtomicAddrByteAlignment alignment = truncate(atomicAddr);
    return isZero(alignment);
endfunction

function ImmDt extractImmDt(HeaderData headerData, RdmaOpCode opcode, TransType transType);
  // Reference implementation:
  // function ImmDt extractImmDt(HeaderData headerData, RdmaOpCode opcode, TransType transType);
    case (opcode)
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: begin
            return case (transType)
                TRANS_TYPE_XRC: unpack(headerData[
                    valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(RETH_WIDTH) -1 :
                    valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(RETH_WIDTH) - valueOf(IMM_DT

function IETH extractIETH(HeaderData headerData, TransType transType);
  // Reference implementation:
  // function IETH extractIETH(HeaderData headerData, TransType transType);
    let ieth = case (transType)
        TRANS_TYPE_XRC: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) -1 :
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) - valueOf(XRCETH_WIDTH) - valueOf(IETH_WIDTH)
        ]);
        default: unpack(headerData[
            valueOf(HEADER_MAX_DATA_WIDTH) - valueOf(BTH_WIDTH) -1 :
            valueOf(HEADER_MAX_DAT

function Bool isCongestionNotificationPkt(BTH bth);
  // Reference implementation:
  // function Bool isCongestionNotificationPkt(BTH bth);
    return { pack(bth.trans), pack(bth.opcode) } == fromInteger(valueOf(ROCE_CNP));
endfunction

function Bool isFirstRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isFirstRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_FIRST              ,
        RDMA_WRITE_FIRST        ,
        RDMA_READ_RESPONSE_FIRST: True;

        default                 : False;
    endcase;
endfunction

function Bool isMiddleRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isMiddleRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_MIDDLE              ,
        RDMA_WRITE_MIDDLE        ,
        RDMA_READ_RESPONSE_MIDDLE: True;

        default                  : False;
    endcase;
endfunction

function Bool isLastRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isLastRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_LAST                     ,
        SEND_LAST_WITH_IMMEDIATE      ,
        SEND_LAST_WITH_INVALIDATE     ,

        RDMA_WRITE_LAST               ,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,

        RDMA_READ_RESPONSE_LAST       : True;

        default                       : False;
    endcase;
endfunction

function Bool isOnlyRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isOnlyRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_ONLY                     ,
        SEND_ONLY_WITH_IMMEDIATE      ,
        SEND_ONLY_WITH_INVALIDATE     ,

        RDMA_WRITE_ONLY               ,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE,

        RDMA_READ_REQUEST             ,
        COMPARE_SWAP                  ,
        FETCH_ADD                     ,

        RDMA_READ_RESPONSE_ONLY       ,

        ACKNOWLEDGE                   ,
        ATOMIC_ACKNO

function Bool isFirstOrOnlyRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isFirstOrOnlyRdmaOpCode(RdmaOpCode opcode);
    return isFirstRdmaOpCode(opcode) || isOnlyRdmaOpCode(opcode);
endfunction

function Bool isFirstOrMiddleRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isFirstOrMiddleRdmaOpCode(RdmaOpCode opcode);
    return isFirstRdmaOpCode(opcode) || isMiddleRdmaOpCode(opcode);
endfunction

function Bool isLastOrOnlyRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isLastOrOnlyRdmaOpCode(RdmaOpCode opcode);
    return isLastRdmaOpCode(opcode) || isOnlyRdmaOpCode(opcode);
endfunction

function Bool isMiddleOrLastRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isMiddleOrLastRdmaOpCode(RdmaOpCode opcode);
    return isLastRdmaOpCode(opcode) || isOnlyRdmaOpCode(opcode);
endfunction

function Bool isSendReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isSendReqRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_FIRST               ,
        SEND_MIDDLE              ,
        SEND_LAST                ,
        SEND_LAST_WITH_IMMEDIATE ,
        SEND_ONLY                ,
        SEND_ONLY_WITH_IMMEDIATE ,
        SEND_LAST_WITH_INVALIDATE,
        SEND_ONLY_WITH_INVALIDATE: True;
        default                  : False;
    endcase;
endfunction

function Bool isWriteReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isWriteReqRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        RDMA_WRITE_FIRST              ,
        RDMA_WRITE_MIDDLE             ,
        RDMA_WRITE_LAST               ,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY               ,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: True;
        default                       : False;
    endcase;
endfunction

function Bool isWriteImmReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isWriteImmReqRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: True;
        default                       : False;
    endcase;
endfunction

function Bool isSendWriteImmReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isSendWriteImmReqRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        SEND_FIRST                    ,
        SEND_MIDDLE                   ,
        SEND_LAST                     ,
        SEND_LAST_WITH_IMMEDIATE      ,
        SEND_ONLY                     ,
        SEND_ONLY_WITH_IMMEDIATE      ,
        SEND_LAST_WITH_INVALIDATE     ,
        SEND_ONLY_WITH_INVALIDATE     ,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: True;
       

function Bool isReadReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isReadReqRdmaOpCode(RdmaOpCode opcode);
    return opcode == RDMA_READ_REQUEST;
endfunction

function Bool isAtomicReqRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isAtomicReqRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        COMPARE_SWAP,
        FETCH_ADD   : True;
        default     : False;
    endcase;
endfunction

function Bool isReadRespRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isReadRespRdmaOpCode(RdmaOpCode opcode);
    return case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  : True;
        default                  : False;
    endcase;
endfunction

function Bool isRdmaRespOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isRdmaRespOpCode(RdmaOpCode opcode);
    return case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  ,
        ACKNOWLEDGE              ,
        ATOMIC_ACKNOWLEDGE       : True;
        default                  : False;
    endcase;
endfunction

function Bool rdmaRespHasAETH(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool rdmaRespHasAETH(RdmaOpCode opcode);
    return case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  ,
        ACKNOWLEDGE              ,
        ATOMIC_ACKNOWLEDGE       : True;
        default                  : False;
    endcase;
endfunction

function Bool isAtomicRespRdmaOpCode(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool isAtomicRespRdmaOpCode(RdmaOpCode opcode);
    return opcode == ATOMIC_ACKNOWLEDGE;
endfunction

function Bool rdmaRespNeedDmaWrite(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool rdmaRespNeedDmaWrite(RdmaOpCode opcode);
    return case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  ,
        ATOMIC_ACKNOWLEDGE       : True;
        default                  : False;
    endcase;
endfunction

function Bool rdmaReqHasRETH(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool rdmaReqHasRETH(RdmaOpCode opcode);
    return case (opcode)
        RDMA_WRITE_FIRST              ,
        RDMA_WRITE_ONLY               ,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE,
        RDMA_READ_REQUEST             : True;
        default                       : False;
    endcase;
endfunction

function Bool rdmaReqHasImmDt(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool rdmaReqHasImmDt(RdmaOpCode opcode);
    return case (opcode)
        SEND_LAST_WITH_IMMEDIATE      ,
        SEND_ONLY_WITH_IMMEDIATE      ,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: True;
        default                       : False;
    endcase;
endfunction

function Bool rdmaReqHasIETH(RdmaOpCode opcode);
  // Reference implementation:
  // function Bool rdmaReqHasIETH(RdmaOpCode opcode);
    return case (opcode)
        SEND_LAST_WITH_INVALIDATE,
        SEND_ONLY_WITH_INVALIDATE: True;
        default                  : False;
    endcase;
endfunction

function RdmaRespType getRdmaRespType(RdmaOpCode opcode, AETH aeth);
  // Reference implementation:
  // function RdmaRespType getRdmaRespType(RdmaOpCode opcode, AETH aeth);
    case (opcode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  ,
        ATOMIC_ACKNOWLEDGE       : return RDMA_RESP_NORMAL;
        ACKNOWLEDGE              : case (aeth.code)
            AETH_CODE_ACK: return RDMA_RESP_NORMAL;
            AETH_CODE_RNR: return RDMA_RESP_RETRY;
            AETH_CODE_NAK: return case (aeth.value)
      

function RetryReason getRetryReasonFromAETH(AETH aeth);
  // Reference implementation:
  // function RetryReason getRetryReasonFromAETH(AETH aeth);
    return case (aeth.code)
        AETH_CODE_RNR: RETRY_REASON_RNR;
        AETH_CODE_NAK: (
            (aeth.value == zeroExtend(pack(AETH_NAK_SEQ_ERR))) ?
                RETRY_REASON_SEQ_ERR : RETRY_REASON_NOT_RETRY
        );
        default: RETRY_REASON_NOT_RETRY;
    endcase;
endfunction

function ? unknown();
  // Reference implementation:
  // function Bool checkNormalRespOpCodeSeqSQ(
    RdmaOpCode preOpCode, RdmaOpCode curOpCode
);
    return case (preOpCode)
        RDMA_READ_RESPONSE_FIRST ,
        RDMA_READ_RESPONSE_MIDDLE: (
            curOpCode == RDMA_READ_RESPONSE_MIDDLE ||
            curOpCode == RDMA_READ_RESPONSE_LAST
        );
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  ,
        ACKNOWLEDGE              ,
        ATOMIC_ACKNOWLEDGE       : True;
        default                  : False;
    en

function ? unknown();
  // Reference implementation:
  // function Bool checkNormalReqOpCodeSeqRQ(
    RdmaOpCode preOpCode, RdmaOpCode curOpCode
);
    case (preOpCode)
        SEND_FIRST                    ,
        SEND_MIDDLE                   : return case (curOpCode)
                                            SEND_MIDDLE              ,
                                            SEND_LAST                ,
                                            SEND_LAST_WITH_IMMEDIATE ,
                                            SEND_LAST_WITH_INVALIDATE: 

function ? unknown();
  // Reference implementation:
  // function Bool containWorkReqFlag(
    FlagsType#(WorkReqSendFlag) flags, WorkReqSendFlag flag
);
    return containEnum(flags, flag);
    // return !isZero(pack(flags & enum2Flag(flag)));
endfunction

function ResiduePMTU truncateByPMTU(Bit#(nSz);
  // Reference implementation:
  // function ResiduePMTU truncateByPMTU(Bit#(nSz) bits, PMTU pmtu) provisos(
    Add#(MAX_PMTU_WIDTH, anysizeJ, nSz),
    Add#(TSub#(MAX_PMTU_WIDTH, 1), anysizeK, nSz),
    Add#(TSub#(MAX_PMTU_WIDTH, 2), anysizeL, nSz),
    Add#(TSub#(MAX_PMTU_WIDTH, 3), anysizeM, nSz),
    Add#(TSub#(MAX_PMTU_WIDTH, 4), anysizeN, nSz)
);
    return case (pmtu)
        IBV_MTU_256 : begin
            Bit#(TSub#(MAX_PMTU_WIDTH, 4)) residue = truncate(bits); // [7 : 0]
            zeroExtend(residue);
        end
    

function ? unknown();
  // Reference implementation:
  // function Tuple2#(PktNum, ResiduePMTU) truncateLenByPMTU(Length len, PMTU pmtu);
    return case (pmtu)
        IBV_MTU_256 : begin
            Bit#(8) residue = truncate(len); // [7 : 0]
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 8)) truncatedLen = truncateLSB(len);
            tuple2(zeroExtend(truncatedLen), zeroExtend(residue));
        end
        IBV_MTU_512 : begin
            Bit#(9) residue = truncate(len); // [8 : 0]
            Bit#(TSub#(RDMA_MAX_LEN_WIDTH, 9)) truncatedLen = truncate

function ? unknown();
  // Reference implementation:
  // function Tuple2#(PSN, PSN) calcNextAndEndPSN(
    PSN startPSN, PktNum pktNum, Bool isOnlyPkt, PMTU pmtu
);
    let startPlusOne = startPSN + 1;
    // In case pktNum is zero
    PSN nextPSN = isOnlyPkt ? startPlusOne : truncate(zeroExtend(startPSN) + pktNum);
    PSN endPSN = isOnlyPkt ? startPSN : (nextPSN - 1);
    return tuple2(nextPSN, endPSN);
endfunction

function Bool workReqHasAckReq(WorkReq wr);
  // Reference implementation:
  // function Bool workReqHasAckReq(WorkReq wr);
    return containWorkReqFlag(wr.flags, IBV_SEND_SIGNALED);
endfunction

function Bool workReqRequireAck(WorkReq wr);
  // Reference implementation:
  // function Bool workReqRequireAck(WorkReq wr);
    return workReqHasAckReq(wr) || isReadOrAtomicWorkReq(wr.opcode);
endfunction

function Bool workReqNeedDmaReadSQ(WorkReq wr);
  // Reference implementation:
  // function Bool workReqNeedDmaReadSQ(WorkReq wr);
    return case (wr.opcode)
        IBV_WR_RDMA_WRITE         ,
        IBV_WR_RDMA_WRITE_WITH_IMM,
        IBV_WR_SEND               ,
        IBV_WR_SEND_WITH_IMM      ,
        IBV_WR_SEND_WITH_INV      : !isZeroR(wr.len);
        default                   : False;
    endcase;
endfunction

function Bool workReqNeedDmaWriteSQ(WorkReq wr);
  // Reference implementation:
  // function Bool workReqNeedDmaWriteSQ(WorkReq wr);
    return case (wr.opcode)
        IBV_WR_RDMA_READ           : !isZeroR(wr.len);
        IBV_WR_ATOMIC_CMP_AND_SWP  ,
        IBV_WR_ATOMIC_FETCH_AND_ADD: True;
        default                    : False;
    endcase;
endfunction

function Bool workReqHasPayload(WorkReq wr);
  // Reference implementation:
  // function Bool workReqHasPayload(WorkReq wr);
    return !(isZeroR(wr.len) || isReadOrAtomicWorkReq(wr.opcode));
endfunction

function Bool workReqNeedWorkCompSQ(WorkReq wr);
  // Reference implementation:
  // function Bool workReqNeedWorkCompSQ(WorkReq wr);
    return
        containWorkReqFlag(wr.flags, IBV_SEND_SIGNALED) ||
        isReadOrAtomicWorkReq(wr.opcode);
endfunction

function Bool workReqHasComp(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool workReqHasComp(WorkReqOpCode opcode);
    return opcode == IBV_WR_ATOMIC_CMP_AND_SWP;
endfunction

function Bool workReqHasSwap(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool workReqHasSwap(WorkReqOpCode opcode);
    return case (opcode)
        IBV_WR_ATOMIC_CMP_AND_SWP  ,
        IBV_WR_ATOMIC_FETCH_AND_ADD: True;
        default: False;
    endcase;
endfunction

function Bool isSendWorkReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool isSendWorkReq(WorkReqOpCode opcode);
    return case (opcode)
        IBV_WR_SEND         ,
        IBV_WR_SEND_WITH_IMM,
        IBV_WR_SEND_WITH_INV: True;
        default             : False;
    endcase;
endfunction

function Bool isReadWorkReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool isReadWorkReq(WorkReqOpCode opcode);
    return opcode == IBV_WR_RDMA_READ;
endfunction

function Bool isReadRespWorkReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool isReadRespWorkReq(WorkReqOpCode opcode);
    return opcode == IBV_WR_RDMA_READ_RESP;
endfunction

function Bool isAtomicWorkReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool isAtomicWorkReq(WorkReqOpCode opcode);
    return workReqHasSwap(opcode);
endfunction

function Bool isReadOrAtomicWorkReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool isReadOrAtomicWorkReq(WorkReqOpCode opcode);
    return case (opcode)
        IBV_WR_RDMA_READ,
        IBV_WR_ATOMIC_CMP_AND_SWP,
        IBV_WR_ATOMIC_FETCH_AND_ADD: True;
        default: False;
    endcase;
endfunction

function Bool workReqNeedRecvReq(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool workReqNeedRecvReq(WorkReqOpCode opcode);
    return case (opcode)
        IBV_WR_SEND               ,
        IBV_WR_SEND_WITH_IMM      ,
        IBV_WR_SEND_WITH_INV      ,
        IBV_WR_RDMA_WRITE_WITH_IMM: True;
        default                   : False;
    endcase;
endfunction

function Bool workReqHasImmDt(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool workReqHasImmDt(WorkReqOpCode opcode);
    return case (opcode)
        IBV_WR_RDMA_WRITE_WITH_IMM,
        IBV_WR_SEND_WITH_IMM: True;
        default: False;
    endcase;
endfunction

function Bool workReqHasInv(WorkReqOpCode opcode);
  // Reference implementation:
  // function Bool workReqHasInv(WorkReqOpCode opcode);
    return opcode == IBV_WR_SEND_WITH_INV;
endfunction

function PendingWorkReq genNewPendingWorkReq(WorkReq wr);
  // Reference implementation:
  // function PendingWorkReq genNewPendingWorkReq(WorkReq wr) = PendingWorkReq {
    wr: wr,
    startPSN: tagged Invalid,
    endPSN: tagged Invalid,
    pktNum: tagged Invalid,
    isOnlyReqPkt: tagged Invalid
};

/*
module mkConnectPendingWorkReqPipeOut2PendingWorkReqQ#(
    PipeOut#(PendingWorkReq) pipeIn, FIFOF#(PendingWorkReq) pendingWorkReqBufQ
)(Empty);
    rule connect;
        let pendingWR = pipeIn.first;
        pendingWorkReqBufQ.enq(pendingWR);
        pipeIn.deq;

        // $display(


function ? unknown();
  // Reference implementation:
  // function Maybe#(WorkCompStatus) pktStatus2WorkCompStatusSQ(
    PktVeriStatus pktStatus
);
    return case (pktStatus)
        PKT_ST_VALID  : tagged Valid IBV_WC_SUCCESS;
        PKT_ST_LEN_ERR: tagged Valid IBV_WC_LOC_LEN_ERR;
        // PKT_ST_QP_ACC_ERR: tagged Valid IBV_WC_LOC_ACCESS_ERR;
        default       : tagged Invalid;
    endcase;
endfunction

function Maybe#(WorkCompOpCode) workReqOpCode2WorkCompOpCode4SQ(WorkReqOpCode wrOpCode);
  // Reference implementation:
  // function Maybe#(WorkCompOpCode) workReqOpCode2WorkCompOpCode4SQ(WorkReqOpCode wrOpCode);
    return case (wrOpCode)
        IBV_WR_RDMA_WRITE          : tagged Valid IBV_WC_RDMA_WRITE;
        IBV_WR_RDMA_WRITE_WITH_IMM : tagged Valid IBV_WC_RDMA_WRITE;
        IBV_WR_SEND                : tagged Valid IBV_WC_SEND;
        IBV_WR_SEND_WITH_IMM       : tagged Valid IBV_WC_SEND;
        IBV_WR_RDMA_READ           : tagged Valid IBV_WC_RDMA_READ;
        IBV_WR_ATOMIC_CMP_AND_SWP  : tagged Valid IB

function Maybe#(WorkCompStatus) genErrWorkCompStatusFromAethSQ(AETH aeth);
  // Reference implementation:
  // function Maybe#(WorkCompStatus) genErrWorkCompStatusFromAethSQ(AETH aeth);
    case (aeth.code)
        // AETH_CODE_ACK: return tagged Valid IBV_WC_SUCCESS;
        // AETH_CODE_RNR: return tagged Valid IBV_WC_RNR_RETRY_EXC_ERR;
        AETH_CODE_NAK: return case (aeth.value)
            // zeroExtend(pack(AETH_NAK_SEQ_ERR)): tagged Valid IBV_WC_RETRY_EXC_ERR;
            zeroExtend(pack(AETH_NAK_INV_REQ)): tagged Valid IBV_WC_REM_INV_REQ_ERR;
            zeroExtend(pack(AETH_NAK_RMT_ACC)): tag

function Maybe#(WorkCompOpCode) rdmaOpCode2WorkCompOpCode4RQ(RdmaOpCode opcode);
  // Reference implementation:
  // function Maybe#(WorkCompOpCode) rdmaOpCode2WorkCompOpCode4RQ(RdmaOpCode opcode);
    return case (opcode)
        SEND_FIRST                    ,
        SEND_MIDDLE                   ,
        SEND_LAST                     ,
        SEND_LAST_WITH_IMMEDIATE      ,
        SEND_ONLY                     ,
        SEND_ONLY_WITH_IMMEDIATE      ,
        SEND_LAST_WITH_INVALIDATE     ,
        SEND_ONLY_WITH_INVALIDATE     : tagged Valid IBV_WC_RECV;

        RDMA_WRITE_LAST_WITH_IMMEDIATE,
       

function WorkCompFlags rdmaOpCode2WorkCompFlagsRQ(RdmaOpCode opcode);
  // Reference implementation:
  // function WorkCompFlags rdmaOpCode2WorkCompFlagsRQ(RdmaOpCode opcode);
    return case (opcode)
        SEND_FIRST                    ,
        SEND_MIDDLE                   ,
        SEND_LAST                     ,
        SEND_ONLY                     : IBV_WC_NO_FLAGS;

        SEND_LAST_WITH_IMMEDIATE      ,
        SEND_ONLY_WITH_IMMEDIATE      ,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE: IBV_WC_WITH_IMM;

        SEND_LAST_WITH_INVALIDATE     ,
        S

function ? unknown();
  // Reference implementation:
  // function PipeOut#(anytype) muxPipeOut(
    Bool sel, PipeOut#(anytype) pipeIn1, PipeOut#(anytype) pipeIn2
);
    PipeOut#(anytype) resultPipeOut = interface PipeOut;
        method anytype first();
            return sel ? pipeIn1.first : pipeIn2.first;
        endmethod

        method Action deq();
            if (sel) begin
                pipeIn1.deq;
            end
            else begin
                pipeIn2.deq;
            end
        endmethod

        method Bool notEmpty();
       

function ? unknown();
  // Reference implementation:
  // function Tuple2#(PipeOut#(anytype), PipeOut#(anytype)) deMuxPipeOut(
    Bool sel, PipeOut#(anytype) pipeIn
);
    PipeOut#(anytype) p1 = interface PipeOut;
        method anytype first() if (sel);
            return pipeIn.first;
        endmethod
        method Action deq() if (sel);
            pipeIn.deq;
        endmethod
        method Bool notEmpty() if (sel);
            return pipeIn.notEmpty;
        endmethod
    endinterface;

    PipeOut#(anytype) p2 = interface PipeOut;
        met

function ? unknown();
  // Reference implementation:
  // function Rules genEmptyPipeOutRule(
    PipeOut#(anytype) inputPipeOut, String assertMsg
);
    return (
        rules
            rule checkEmptyPipeIn;
                immAssert(
                    !inputPipeOut.notEmpty,
                    assertMsg,
                    $format(
                        "inputPipeOut.notEmpty=",
                        fshow(inputPipeOut.notEmpty),
                        " should be empty"
                    )
                );
            endrule
       

function ? unknown();
  // Reference implementation:
  // function ActionValue#(PayloadConReq) genDiscardPayloadReq(
    PktFragNum fragNum,
    DmaReqSrcType initiator,
    QPN sqpn,
    ADDR startAddr,
    PktLen len,
    PSN psn
);
    actionvalue
        immAssert(
            !isZero(fragNum),
            "fragNum non-zero assertion @ genDiscardPayloadReq()",
            $format("fragNum=%0d", fragNum, " should be non-zero")
        );
        let discardReq = PayloadConReq {
            fragNum    : fragNum,
            consumeInfo: tagged Discar

function ? unknown();
  // Reference implementation:
  // function Action genDiscardPayloadReq(
    PktFragNum fragNum,
    DmaReqSrcType initiator,
    QPN sqpn,
    ADDR startAddr,
    PktLen len,
    PSN psn,
    FIFOF#(PayloadConReq) payloadConReqQ
);
    action
        immAssert(
            !isZero(fragNum),
            "fragNum non-zero assertion @ genDiscardPayloadReq()",
            $format("fragNum=%0d", fragNum, " should be non-zero")
        );
        let discardReq = PayloadConReq {
            fragNum    : fragNum,
            consumeInf

function ? unknown();
  // Reference implementation:
  //     function Action connectAction(anytype connectVal)
)(Empty) provisos(
    FShow#(anytype),
    Bits#(anytype, anysize)
    // Bits#(DataStream, anysize)
);
    Reg#(BTH) bthReg <- mkRegU;

    rule connect;
        let data <- getIn.get;
        putOut.put(data);
        connectAction(data);

    endrule
endmodule


Output in ```bsv block. Include imports referencing existing types. Generate now: