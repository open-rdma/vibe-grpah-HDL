import Reserved      :: *;
import FIFOF         :: *;
import Vector        :: *;
import ClientServer  :: *;

// ----- Basic type aliases -----

typedef Bit#(32)     AddrIPv4;
typedef Bit#(128)    AddrIPv6;
typedef Bit#(48)     MAC;

// ----- Width constants -----
// ???MAX_SGE, ???TWO (PktNumAddOn), ???DATA_BUS_BYTE_NUM_WIDTH, ???DATA_BUS_BIT_NUM_WIDTH

typedef Bit#(TWO)                  PktNumAddOn;
typedef Bit#(DATA_BUS_BYTE_NUM_WIDTH) ShiftByteNum;
typedef Bit#(DATA_BUS_BIT_NUM_WIDTH)  ShiftBitNum;

// ----- Scatter-Gather List -----

typedef Vector#(MAX_SGE, ScatterGatherElem) ScatterGatherList;

// ----- Server/Client -----

typedef Server#(DmaReadCntrlReq, DmaReadCntrlResp) DmaCntrlReadSrv;
typedef Client#(DmaReadCntrlReq, DmaReadCntrlResp) DmaCntrlReadClt;

// ===== Enums =====

typedef enum {
    MERGE_SGE_PAYLOAD_INIT,
    MERGE_SGE_PAYLOAD_FIRST_OR_MID_PKT,
    MERGE_SGE_PAYLOAD_LAST_OR_ONLY_PKT
} MergePayloadStateEachSGE deriving (Bits, Eq, FShow);

typedef enum {
    MERGE_SGL_PAYLOAD_INIT,
    MERGE_SGL_PAYLOAD_FIRST_OR_MID_SGE,
    MERGE_SGL_PAYLOAD_LAST_OR_ONLY_SGE
} MergePayloadStateAllSGE deriving (Bits, Eq, FShow);

typedef enum {
    ADJUST_PAYLOAD_SEGMENT_INIT,
    ADJUST_PAYLOAD_SEGMENT_FIRST_OR_MID_PKT,
    ADJUST_PAYLOAD_SEGMENT_LAST_OR_ONLY_PKT
} AdjustPayloadSegmentState deriving (Bits, Eq, FShow);

// ===== Structs =====

typedef struct {
    WorkReqID           id;
    WorkReqOpCode       opcode;
    FlagsType#(WorkReqSendFlag) flags;
    TypeQP              qpType;
    PSN                 psn;
    PMTU                pmtu;
    IP                  dqpIP;
    MAC                 macAddr;
    ScatterGatherList   sgl;
    Length              totalLen;
    ADDR                raddr;
    RKEY                rkey;
    QPN                 sqpn;
    QPN                 dqpn;
    Maybe#(Long)        comp;
    Maybe#(Long)        swap;
    Maybe#(ImmOrRKey)   immDtOrInvRKey;
    Maybe#(QPN)         srqn;
    Maybe#(QKEY)        qkey;
    Bool                isFirst;
    Bool                isLast;
} WorkQueueElem deriving (Bits);

typedef SizeOf#(WorkQueueElem)           WorkQueueElem_WIDTH;
typedef TDiv#(WorkQueueElem_WIDTH, 8)    WorkQueueElem_BYTE_WIDTH;

typedef struct {
    ADDR    laddr;
    Length  len;
    LKEY    lkey;
    Bool    isFirst;
    Bool    isLast;
} ScatterGatherElem deriving (Bits, FShow);

typedef SizeOf#(ScatterGatherElem)           ScatterGatherElem_WIDTH;
typedef TDiv#(ScatterGatherElem_WIDTH, 8)    ScatterGatherElem_BYTE_WIDTH;

typedef struct {
    PktLen  firstPktLen;
    PktLen  lastPktLen;
    PktNum  sgePktNum;
    PMTU    pmtu;
} PktMetaDataSGE deriving (Bits, FShow);

typedef SizeOf#(PktMetaDataSGE)           PktMetaDataSGE_WIDTH;
typedef TDiv#(PktMetaDataSGE_WIDTH, 8)    PktMetaDataSGE_BYTE_WIDTH;

typedef struct {
    ByteEnBitNum    lastFragValidByteNum;
    Bool            isFirst;
    Bool            isLast;
} MergedMetaDataSGE deriving (Bits, FShow);

typedef SizeOf#(MergedMetaDataSGE)           MergedMetaDataSGE_WIDTH;
typedef TDiv#(MergedMetaDataSGE_WIDTH, 8)    MergedMetaDataSGE_BYTE_WIDTH;

typedef struct {
    PktLen          firstPktLen;
    PktFragNum      firstPktFragNum;
    ByteEnBitNum    firstPktLastFragValidByteNum;
    ByteEnBitNum    origLastFragValidByteNum;
    PktNum          adjustedPktNum;
    PMTU            pmtu;
} AdjustedTotalPayloadMetaData deriving (Bits, FShow);

typedef SizeOf#(AdjustedTotalPayloadMetaData)           AdjustedTotalPayloadMetaData_WIDTH;
typedef TDiv#(AdjustedTotalPayloadMetaData_WIDTH, 8)    AdjustedTotalPayloadMetaData_BYTE_WIDTH;

typedef struct {
    ScatterGatherList   sgl;
    Length              totalLen;
    QPN                 sqpn;
    WorkReqID           wrID;
} DmaReadMetaDataSGL deriving (Bits, FShow);

typedef SizeOf#(DmaReadMetaDataSGL)           DmaReadMetaDataSGL_WIDTH;
typedef TDiv#(DmaReadMetaDataSGL_WIDTH, 8)    DmaReadMetaDataSGL_BYTE_WIDTH;

typedef struct {
    ADDR    startAddr;
    Length  len;
    PMTU    pmtu;
    Bool    isFirst;
    Bool    isLast;
} AddrChunkReq deriving (Bits, FShow);

typedef SizeOf#(AddrChunkReq)           AddrChunkReq_WIDTH;
typedef TDiv#(AddrChunkReq_WIDTH, 8)    AddrChunkReq_BYTE_WIDTH;

typedef struct {
    ADDR    chunkAddr;
    PktLen  chunkLen;
    Bool    isFirst;
    Bool    isLast;
    Bool    isOrigFirst;
    Bool    isOrigLast;
} AddrChunkResp deriving (Bits, FShow);

typedef SizeOf#(AddrChunkResp)           AddrChunkResp_WIDTH;
typedef TDiv#(AddrChunkResp_WIDTH, 8)    AddrChunkResp_BYTE_WIDTH;

typedef struct {
    PktNumAddOn pktNumAddOne;
    PktNum      truncatedPktNum;
    PktLen      lenLowPart;
    PktLen      maxFirstPktLen;
    PktLen      tmpLastPktLen;
    PktLen      pmtuLen;
    PMTU        pmtu;
    ADDR        startAddr;
    ADDR        nextAddr;
    Bool        notFullPkt;
    Bool        hasExtraPkt;
    Bool        hasResidue;
    Bool        isOrigFirst;
    Bool        isOrigLast;
} TmpPktMetaDataSGE deriving (Bits);

typedef SizeOf#(TmpPktMetaDataSGE)           TmpPktMetaDataSGE_WIDTH;
typedef TDiv#(TmpPktMetaDataSGE_WIDTH, 8)    TmpPktMetaDataSGE_BYTE_WIDTH;

typedef struct {
    PktNum  sgePktNum;
    PktLen  firstPktLen;
    PktLen  pmtuLen;
    PktLen  lastPktLen;
    PMTU    pmtu;
    ADDR    startAddr;
    ADDR    nextAddr;
    Bool    isOrigFirst;
    Bool    isOrigLast;
} TmpChunkRespData deriving (Bits);

typedef SizeOf#(TmpChunkRespData)           TmpChunkRespData_WIDTH;
typedef TDiv#(TmpChunkRespData_WIDTH, 8)    TmpChunkRespData_BYTE_WIDTH;

typedef struct {
    DmaReadMetaDataSGL  sglDmaReadMetaData;
    PMTU                pmtu;
} DmaReadCntrlReq deriving (Bits, FShow);

typedef SizeOf#(DmaReadCntrlReq)           DmaReadCntrlReq_WIDTH;
typedef TDiv#(DmaReadCntrlReq_WIDTH, 8)    DmaReadCntrlReq_BYTE_WIDTH;

typedef struct {
    DmaReadResp dmaReadResp;
    Bool        isFirstFragInSGL;
    Bool        isLastFragInSGL;
} DmaReadCntrlResp deriving (Bits, FShow);

typedef SizeOf#(DmaReadCntrlResp)           DmaReadCntrlResp_WIDTH;
typedef TDiv#(DmaReadCntrlResp_WIDTH, 8)    DmaReadCntrlResp_BYTE_WIDTH;

typedef struct {
    ByteEnBitNum    lastFragInvalidByteNum;
    BusBitNum       lastFragInvalidBitNum;
    ByteEnBitNum    curInvalidByteNum;
    BusBitNum       curInvalidBitNum;
    Bool            isOnlySGE;
    Bool            sgeIsFirst;
    Bool            sgeIsLast;
    Bool            hasLessFrag;
} TmpMergedMetaDataSGE deriving (Bits);

typedef SizeOf#(TmpMergedMetaDataSGE)           TmpMergedMetaDataSGE_WIDTH;
typedef TDiv#(TmpMergedMetaDataSGE_WIDTH, 8)    TmpMergedMetaDataSGE_BYTE_WIDTH;

typedef struct {
    WorkReqID           wrID;
    QPN                 sqpn;
    ScatterGatherList   sgl;
    Length              totalLen;
    ADDR                raddr;
    PMTU                pmtu;
    Bool                addPadding;
} PayloadGenReqSG deriving (Bits, FShow);

typedef SizeOf#(PayloadGenReqSG)           PayloadGenReqSG_WIDTH;
typedef TDiv#(PayloadGenReqSG_WIDTH, 8)    PayloadGenReqSG_BYTE_WIDTH;

typedef struct {
    ADDR    raddr;
    PktLen  pktLen;
    PAD     padCnt;
    Bool    isFirst;
    Bool    isLast;
} PayloadGenRespSG deriving (Bits, FShow);

typedef SizeOf#(PayloadGenRespSG)           PayloadGenRespSG_WIDTH;
typedef TDiv#(PayloadGenRespSG_WIDTH, 8)    PayloadGenRespSG_BYTE_WIDTH;

typedef struct {
    PktNum  totalPktNum;
    Bool    isOnlyPkt;
    Bool    isZeroPayloadLen;
} PayloadGenTotalMetaData deriving (Bits, FShow);

typedef SizeOf#(PayloadGenTotalMetaData)           PayloadGenTotalMetaData_WIDTH;
typedef TDiv#(PayloadGenTotalMetaData_WIDTH, 8)    PayloadGenTotalMetaData_BYTE_WIDTH;

typedef struct {
    PktLen  pmtuMask;
    PktLen  addrAndLenLowPartSum;
    PktLen  pmtuLen;
    PktLen  lenLowPart;
    PktLen  maxFirstPktLen;
    PktNum  truncatedPktNum;
    ADDR    pmtuAlignedStartAddr;
    Bool    isZeroPayloadLen;
} TmpPayloadGenMetaData deriving (Bits);

typedef SizeOf#(TmpPayloadGenMetaData)           TmpPayloadGenMetaData_WIDTH;
typedef TDiv#(TmpPayloadGenMetaData_WIDTH, 8)    TmpPayloadGenMetaData_BYTE_WIDTH;

typedef struct {
    ADDR        origRemoteAddr;
    ADDR        secondChunkStartAddr;
    Length      totalLen;
    PktNum      truncatedPktNum;
    PktNumAddOn pktNumAddOne;
    PktLen      lenLowPart;
    PktLen      maxFirstPktLen;
    PktLen      tmpLastPktLen;
    PktLen      pmtuLen;
    PMTU        pmtu;
    Bool        notFullPkt;
    Bool        hasExtraPkt;
    Bool        hasResidue;
    Bool        isZeroPayloadLen;
    Bool        shouldAddPadding;
} TmpAdjustFirstAndLastPktLen deriving (Bits);

typedef SizeOf#(TmpAdjustFirstAndLastPktLen)           TmpAdjustFirstAndLastPktLen_WIDTH;
typedef TDiv#(TmpAdjustFirstAndLastPktLen_WIDTH, 8)    TmpAdjustFirstAndLastPktLen_BYTE_WIDTH;

typedef struct {
    ADDR    firstRemoteAddr;
    ADDR    secondRemoteAddr;
    Length  totalLen;
    PktNum  totalPktNum;
    PktLen  firstPktLen;
    PktLen  lastPktLen;
    PktLen  pmtuLen;
    PMTU    pmtu;
    Bool    isZeroPayloadLen;
    Bool    shouldAddPadding;
} TmpAdjustTotalPayloadMetaData deriving (Bits);

typedef SizeOf#(TmpAdjustTotalPayloadMetaData)           TmpAdjustTotalPayloadMetaData_WIDTH;
typedef TDiv#(TmpAdjustTotalPayloadMetaData_WIDTH, 8)    TmpAdjustTotalPayloadMetaData_BYTE_WIDTH;

typedef struct {
    ADDR        firstRemoteAddr;
    ADDR        secondRemoteAddr;
    PktLen      firstPktLen;
    PktLen      lastPktLen;
    PktLen      pmtuLen;
    ByteEnBitNum firstPktLastFragValidByteNumWithPadding;
    ByteEnBitNum lastPktLastFragValidByteNumWithPadding;
    PAD         firstPktPadCnt;
    PAD         lastPktPadCnt;
    PktNum      totalPktNum;
    PMTU        pmtu;
    Bool        isOnlyPkt;
    Bool        isZeroPayloadLen;
    Bool        shouldAddPadding;
} TmpPayloadGenRespData deriving (Bits);

typedef SizeOf#(TmpPayloadGenRespData)           TmpPayloadGenRespData_WIDTH;
typedef TDiv#(TmpPayloadGenRespData_WIDTH, 8)    TmpPayloadGenRespData_BYTE_WIDTH;

typedef struct {
    ByteEn  firstPktLastFragByteEnWithPadding;
    ByteEn  lastPktLastFragByteEnWithPadding;
    Bool    isZeroPayloadLen;
    Bool    shouldAddPadding;
} TmpPaddingData deriving (Bits);

typedef SizeOf#(TmpPaddingData)           TmpPaddingData_WIDTH;
typedef TDiv#(TmpPaddingData_WIDTH, 8)    TmpPaddingData_BYTE_WIDTH;
