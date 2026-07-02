// DataTypes.bsv — Generated RDMA data type definitions
//
// NOTE: Several identifiers are referenced but defined elsewhere in the project:
//   AETH_VALUE_WIDTH, MAX_SGE, BTH_BYTE_WIDTH, XRCETH_BYTE_WIDTH, RETH_BYTE_WIDTH,
//   LETH_BYTE_WIDTH, ATOMIC_ETH_BYTE_WIDTH, DATA_BUS_WIDTH, MAX_PMTU, MIN_PMTU,
//   RDMA_MAX_LEN_WIDTH, MIN_PKT_NUM_IN_RECV_BUF, TARGET_CYCLE_NS, PAGE_SIZE_CAP,
//   ADDR_WIDTH, MAX_MR, MAX_PD, KEY_WIDTH, PAD_WIDTH, MAX_QP_WR, MAX_QP_RD_ATOM,
//   WR_ID_WIDTH, LKEY, RKEY, ADDR, Length, QPN, PSN, QKEY, IMM, Long, PKEY,
//   RdmaOpCode, PayloadConInfo, FlagsType, ScanFIFOF

import Assert       :: *;
import ClientServer :: *;
import FIFOF         :: *;
import GetPut        :: *;
import Maybe         :: *;
import Pipe          :: *;
import Reserved      :: *;
import SpecialFIFOs  :: *;
import Vector        :: *;

// ==========================================================================
// Numeric constants
// ==========================================================================
typedef 8                BYTE_WIDTH;
typedef TExp#(31)        RDMA_MAX_LEN;
typedef 8                ATOMIC_WORK_REQ_LEN;
typedef 3                RETRY_CNT_WIDTH;
typedef 7                INFINITE_RETRY;
typedef 0                INFINITE_TIMEOUT;
typedef TMul#(8192, TExp#(30))          MAX_TIMEOUT_NS;
typedef TMul#(655360, 1000)             MAX_RNR_WAIT_NS;
typedef 16'hFFFF         DEFAULT_PKEY;
typedef 32'hFFFFFFFF     DEFAULT_QKEY;
typedef 3                DEFAULT_RETRY_NUM;
typedef 64               ATOMIC_ADDR_BIT_ALIGNMENT;
typedef 32               PD_HANDLE_WIDTH;
typedef 8                QP_CAP_CNT_WIDTH_SMALL;  // was QP_CAP_CNT_WIDTH (8)
typedef 32               QP_CAP_CNT_WIDTH;        // was QP_CAP_CNT_WIDTH (32) — overrides above
typedef 8                PENDING_READ_ATOMIC_REQ_CNT_WIDTH;
typedef 48               PHYSICAL_ADDR_WIDTH;

// ==========================================================================
// Computed type-level naturals (TLog / TAdd / TDiv / TSub / TMul / TExp)
// ==========================================================================
typedef AETH_VALUE_WIDTH                                     TIMER_WIDTH;
typedef TLog#(MAX_SGE)                                       SGE_IDX_WIDTH;
typedef TAdd#(1, SGE_IDX_WIDTH)                              SGE_NUM_WIDTH;

// HEADER_MAX_BYTE_LENGTH — two competing definitions; pick one:
typedef TAdd#(TAdd#(BTH_BYTE_WIDTH, XRCETH_BYTE_WIDTH),
              TAdd#(RETH_BYTE_WIDTH, LETH_BYTE_WIDTH))       HEADER_MAX_BYTE_LENGTH;
// typedef TAdd#(TAdd#(BTH_BYTE_WIDTH, XRCETH_BYTE_WIDTH),
//               ATOMIC_ETH_BYTE_WIDTH)                      HEADER_MAX_BYTE_LENGTH;

typedef TDiv#(DATA_BUS_WIDTH, 8)                             DATA_BUS_BYTE_WIDTH;
typedef TLog#(DATA_BUS_BYTE_WIDTH)                           DATA_BUS_BYTE_NUM_WIDTH;
typedef TLog#(DATA_BUS_WIDTH)                                DATA_BUS_BIT_NUM_WIDTH;
typedef TDiv#(HEADER_MAX_BYTE_LENGTH, DATA_BUS_BYTE_WIDTH)   HEADER_MAX_FRAG_NUM;
typedef TMul#(DATA_BUS_WIDTH, HEADER_MAX_FRAG_NUM)           HEADER_MAX_DATA_WIDTH;
typedef TMul#(DATA_BUS_BYTE_WIDTH, HEADER_MAX_FRAG_NUM)      HEADER_MAX_BYTE_EN_WIDTH;
typedef TLog#(TAdd#(1, HEADER_MAX_BYTE_EN_WIDTH))            HEADER_MAX_BYTE_NUM_WIDTH;
typedef TLog#(TAdd#(1, HEADER_MAX_FRAG_NUM))                 HEADER_FRAG_NUM_WIDTH;
typedef TLog#(MAX_PMTU)                                      MAX_PMTU_WIDTH;
typedef TLog#(TLog#(MAX_PMTU))                               PMTU_VALUE_MAX_WIDTH;
typedef TDiv#(MAX_PMTU, DATA_BUS_BYTE_WIDTH)                 PMTU_MAX_FRAG_NUM;
typedef TDiv#(MIN_PMTU, DATA_BUS_BYTE_WIDTH)                 PMTU_MIN_FRAG_NUM;
typedef TAdd#(1, TSub#(RDMA_MAX_LEN_WIDTH, TLog#(DATA_BUS_BYTE_WIDTH)))  TOTAL_FRAG_NUM_WIDTH;
typedef TAdd#(1, TLog#(PMTU_MAX_FRAG_NUM))                   PMTU_FRAG_NUM_WIDTH;
typedef TAdd#(1, TSub#(RDMA_MAX_LEN_WIDTH, TLog#(MIN_PMTU))) PKT_NUM_WIDTH;
typedef TAdd#(1, TLog#(MAX_PMTU))                            PKT_LEN_WIDTH;
typedef TDiv#(ATOMIC_ADDR_BIT_ALIGNMENT, BYTE_WIDTH)         ATOMIC_ADDR_BYTE_ALIGNMENT;
typedef TExp#(PAD_WIDTH)                                     FRAG_MIN_VALID_BYTE_NUM;
typedef TMul#(MIN_PKT_NUM_IN_RECV_BUF, PMTU_MAX_FRAG_NUM)    DATA_STREAM_FRAG_BUF_SIZE;
typedef TDiv#(DATA_STREAM_FRAG_BUF_SIZE, PMTU_MIN_FRAG_NUM)  PKT_META_DATA_BUF_SIZE;
typedef TDiv#(MAX_RNR_WAIT_NS, TARGET_CYCLE_NS)              MAX_RNR_WAIT_CYCLES;
typedef TLog#(MAX_RNR_WAIT_CYCLES)                           RNR_WAIT_CYCLE_CNT_WIDTH;
typedef TDiv#(MAX_TIMEOUT_NS, TARGET_CYCLE_NS)               MAX_TIMEOUT_CYCLES;
typedef TAdd#(1, TLog#(MAX_TIMEOUT_CYCLES))                  TIMEOUT_CYCLE_CNT_WIDTH;
typedef TExp#(14)                                            TLB_CACHE_SIZE;
typedef TLog#(PAGE_SIZE_CAP)                                 PAGE_OFFSET_WIDTH;
typedef TLog#(TLB_CACHE_SIZE)                                TLB_CACHE_INDEX_WIDTH;
typedef TSub#(PHYSICAL_ADDR_WIDTH, PAGE_OFFSET_WIDTH)        TLB_CACHE_PA_DATA_WIDTH;
typedef TSub#(TSub#(ADDR_WIDTH, TLB_CACHE_INDEX_WIDTH), PAGE_OFFSET_WIDTH)  TLB_CACHE_TAG_WIDTH;
typedef TDiv#(MAX_MR, MAX_PD)                                MAX_MR_PER_PD;
typedef TLog#(MAX_MR_PER_PD)                                 MR_INDEX_WIDTH;
typedef TSub#(KEY_WIDTH, MR_INDEX_WIDTH)                     MR_KEY_PART_WIDTH;

// ==========================================================================
// Bit# aliases — primitive widths
// ==========================================================================
typedef Bit#(DATA_BUS_WIDTH)              DATA;
typedef Bit#(DATA_BUS_BYTE_WIDTH)         ByteEn;
typedef Bit#(SGE_IDX_WIDTH)               IdxSGL;
typedef Bit#(SGE_NUM_WIDTH)               NumSGE;
typedef Bit#(HEADER_MAX_DATA_WIDTH)       HeaderData;
typedef Bit#(HEADER_MAX_BYTE_EN_WIDTH)    HeaderByteEn;
typedef Bit#(HEADER_MAX_BYTE_NUM_WIDTH)   HeaderByteNum;
typedef Bit#(TAdd#(1, HEADER_MAX_DATA_WIDTH))   HeaderBitNum;
typedef Bit#(HEADER_FRAG_NUM_WIDTH)       HeaderFragNum;
typedef Bit#(DATA_BUS_BIT_NUM_WIDTH)      BusBitWidthMask;
typedef Bit#(DATA_BUS_BYTE_NUM_WIDTH)     BusByteWidthMask;
typedef Bit#(PAD_WIDTH)                   PadMask;
typedef Bit#(TAdd#(1, DATA_BUS_BIT_NUM_WIDTH))   BusBitNum;
typedef Bit#(TAdd#(1, DATA_BUS_BYTE_NUM_WIDTH))  ByteEnBitNum;

// PendingReqCnt — two competing widths; the QP_CAP_CNT_WIDTH (32) version overrides:
typedef Bit#(TLog#(TAdd#(1, MAX_QP_WR)))          PendingReqCntSmall; // original
typedef Bit#(QP_CAP_CNT_WIDTH)                     PendingReqCnt;       // overrides above

// PendingReadAtomicReqCnt — two competing widths:
typedef Bit#(TLog#(TAdd#(1, MAX_QP_RD_ATOM)))     PendingReadAtomicReqCntSmall; // original
typedef Bit#(PENDING_READ_ATOMIC_REQ_CNT_WIDTH)    PendingReadAtomicReqCnt;      // overrides above

typedef Bit#(QP_CAP_CNT_WIDTH)    InlineDataSize;
typedef Bit#(QP_CAP_CNT_WIDTH)    ScatterGatherElemCnt;
typedef Bit#(PMTU_VALUE_MAX_WIDTH)  PmtuValueWidth;
typedef Bit#(MAX_PMTU_WIDTH)        ResiduePMTU;
typedef Bit#(TOTAL_FRAG_NUM_WIDTH)  TotalFragNum;
typedef Bit#(PMTU_FRAG_NUM_WIDTH)   PktFragNum;
typedef Bit#(PKT_NUM_WIDTH)         PktNum;
typedef Bit#(PKT_LEN_WIDTH)         PktLen;
typedef Bit#(WR_ID_WIDTH)           WorkReqID;
typedef Bit#(RETRY_CNT_WIDTH)       RetryCnt;
typedef Bit#(TIMER_WIDTH)           TimeOutTimer;
typedef Bit#(TIMER_WIDTH)           RnrTimer;
typedef Bit#(TLog#(ATOMIC_ADDR_BYTE_ALIGNMENT))  AtomicAddrByteAlignment;
typedef Bit#(RNR_WAIT_CYCLE_CNT_WIDTH)           RnrWaitCycleCnt;
typedef Bit#(TIMEOUT_CYCLE_CNT_WIDTH)            TimeOutCycleCnt;
typedef Bit#(PD_HANDLE_WIDTH)       HandlerPD;

// ==========================================================================
// Structs (forward-declared in dependency order)
// ==========================================================================

// --- PayloadTLB ---
typedef struct {
    Bit#(TLB_CACHE_PA_DATA_WIDTH) data;
    Bit#(TLB_CACHE_TAG_WIDTH)     tag;
} PayloadTLB deriving(Bits);
typedef SizeOf#(PayloadTLB)                   PayloadTLB_WIDTH;
typedef TDiv#(PayloadTLB_WIDTH, 8)            PayloadTLB_BYTE_WIDTH;

// --- DataStream ---
typedef struct {
    DATA    data;
    ByteEn  byteEn;
    Bool    isFirst;
    Bool    isLast;
} DataStream deriving(Bits, Bounded, Eq, FShow);
typedef SizeOf#(DataStream)                   DataStream_WIDTH;
typedef TDiv#(DataStream_WIDTH, 8)            DataStream_BYTE_WIDTH;

// --- HeaderMetaData ---
typedef struct {
    HeaderByteNum   headerLen;
    HeaderFragNum   headerFragNum;
    ByteEnBitNum    lastFragValidByteNum;
    Bool            hasPayload;
    Bool            isEmptyHeader;
} HeaderMetaData deriving(Bits, Bounded, Eq);
typedef SizeOf#(HeaderMetaData)               HeaderMetaData_WIDTH;
typedef TDiv#(HeaderMetaData_WIDTH, 8)        HeaderMetaData_BYTE_WIDTH;

// --- HeaderRDMA ---
typedef struct {
    HeaderData      headerData;
    HeaderByteEn    headerByteEn;
    HeaderMetaData  headerMetaData;
} HeaderRDMA deriving(Bits, Bounded, FShow);
typedef SizeOf#(HeaderRDMA)                   HeaderRDMA_WIDTH;
typedef TDiv#(HeaderRDMA_WIDTH, 8)            HeaderRDMA_BYTE_WIDTH;

// --- RdmaPktMetaData ---
typedef struct {
    PktLen          pktPayloadLen;
    PktFragNum      pktFragNum;
    Bool            isZeroPayloadLen;
    HeaderRDMA      pktHeader;
    HandlerPD       pdHandler;
    Bool            pktValid;
    PktVeriStatus   pktStatus;
} RdmaPktMetaData deriving(Bits, Bounded);
typedef SizeOf#(RdmaPktMetaData)              RdmaPktMetaData_WIDTH;
typedef TDiv#(RdmaPktMetaData_WIDTH, 8)       RdmaPktMetaData_BYTE_WIDTH;

// --- PermCheckReq ---
typedef struct {
    Maybe#(WorkReqID)                wrID;
    LKEY                             lkey;
    RKEY                             rkey;
    Bool                             localOrRmtKey;
    ADDR                             reqAddr;
    Length                           totalLen;
    HandlerPD                        pdHandler;
    Bool                             isZeroDmaLen;
    FlagsType#(MemAccessTypeFlag)    accFlags;
} PermCheckReq deriving(Bits, FShow);
typedef SizeOf#(PermCheckReq)                 PermCheckReq_WIDTH;
typedef TDiv#(PermCheckReq_WIDTH, 8)          PermCheckReq_BYTE_WIDTH;

// --- DmaReadMetaData ---
typedef struct {
    DmaReqSrcType   initiator;
    QPN             sqpn;
    WorkReqID       wrID;
    ADDR            startAddr;
    Length          len;
    IndexMR         mrIdx;
} DmaReadMetaData deriving(Bits, FShow);
typedef SizeOf#(DmaReadMetaData)              DmaReadMetaData_WIDTH;
typedef TDiv#(DmaReadMetaData_WIDTH, 8)       DmaReadMetaData_BYTE_WIDTH;

// --- DmaReadReq ---
typedef struct {
    DmaReqSrcType   initiator;
    QPN             sqpn;
    WorkReqID       wrID;
    ADDR            startAddr;
    PktLen          len;
    IndexMR         mrIdx;
} DmaReadReq deriving(Bits, FShow);
typedef SizeOf#(DmaReadReq)                   DmaReadReq_WIDTH;
typedef TDiv#(DmaReadReq_WIDTH, 8)            DmaReadReq_BYTE_WIDTH;

// --- DmaReadResp ---
typedef struct {
    DmaReqSrcType   initiator;
    QPN             sqpn;
    WorkReqID       wrID;
    Bool            isRespErr;
    DataStream      dataStream;
} DmaReadResp deriving(Bits, FShow);
typedef SizeOf#(DmaReadResp)                  DmaReadResp_WIDTH;
typedef TDiv#(DmaReadResp_WIDTH, 8)           DmaReadResp_BYTE_WIDTH;

// --- DmaWriteMetaData ---
typedef struct {
    DmaReqSrcType   initiator;
    QPN             sqpn;
    ADDR            startAddr;
    PktLen          len;
    PSN             psn;
} DmaWriteMetaData deriving(Bits, Eq, FShow);
typedef SizeOf#(DmaWriteMetaData)             DmaWriteMetaData_WIDTH;
typedef TDiv#(DmaWriteMetaData_WIDTH, 8)      DmaWriteMetaData_BYTE_WIDTH;

// --- DmaWriteReq ---
typedef struct {
    DmaWriteMetaData  metaData;
    DataStream        dataStream;
} DmaWriteReq deriving(Bits, FShow);
typedef SizeOf#(DmaWriteReq)                  DmaWriteReq_WIDTH;
typedef TDiv#(DmaWriteReq_WIDTH, 8)           DmaWriteReq_BYTE_WIDTH;

// --- DmaWriteResp ---
typedef struct {
    DmaReqSrcType   initiator;
    QPN             sqpn;
    PSN             psn;
    Bool            isRespErr;
} DmaWriteResp deriving(Bits, FShow);
typedef SizeOf#(DmaWriteResp)                 DmaWriteResp_WIDTH;
typedef TDiv#(DmaWriteResp_WIDTH, 8)          DmaWriteResp_BYTE_WIDTH;

// --- PayloadGenReq ---
typedef struct {
    DmaReadMetaData dmaReadMetaData;
    Bool            addPadding;
    PMTU            pmtu;
} PayloadGenReq deriving(Bits, FShow);
typedef SizeOf#(PayloadGenReq)                PayloadGenReq_WIDTH;
typedef TDiv#(PayloadGenReq_WIDTH, 8)         PayloadGenReq_BYTE_WIDTH;

// --- PayloadGenResp ---
typedef struct {
    Bool  addPadding;
    Bool  isRespErr;
} PayloadGenResp deriving(Bits, FShow);
typedef SizeOf#(PayloadGenResp)               PayloadGenResp_WIDTH;
typedef TDiv#(PayloadGenResp_WIDTH, 8)        PayloadGenResp_BYTE_WIDTH;

// --- PayloadConReq ---
typedef struct {
    PktFragNum       fragNum;
    PayloadConInfo   consumeInfo;
} PayloadConReq deriving(Bits, FShow);
typedef SizeOf#(PayloadConReq)                PayloadConReq_WIDTH;
typedef TDiv#(PayloadConReq_WIDTH, 8)         PayloadConReq_BYTE_WIDTH;

// --- PayloadConResp ---
typedef struct {
    DmaWriteResp  dmaWriteResp;
} PayloadConResp deriving(Bits, FShow);
typedef SizeOf#(PayloadConResp)               PayloadConResp_WIDTH;
typedef TDiv#(PayloadConResp_WIDTH, 8)        PayloadConResp_BYTE_WIDTH;

// --- AtomicOpReq ---
typedef struct {
    DmaReqSrcType   initiator;
    Bool            casOrFetchAdd;
    ADDR            startAddr;
    Long            compData;
    Long            swapData;
    QPN             sqpn;
    PSN             psn;
} AtomicOpReq deriving(Bits);
typedef SizeOf#(AtomicOpReq)                  AtomicOpReq_WIDTH;
typedef TDiv#(AtomicOpReq_WIDTH, 8)           AtomicOpReq_BYTE_WIDTH;

// --- AtomicOpResp ---
typedef struct {
    DmaReqSrcType   initiator;
    Long            original;
    QPN             sqpn;
    PSN             psn;
} AtomicOpResp deriving(Bits);
typedef SizeOf#(AtomicOpResp)                 AtomicOpResp_WIDTH;
typedef TDiv#(AtomicOpResp_WIDTH, 8)          AtomicOpResp_BYTE_WIDTH;

// --- QpCapacity ---
typedef struct {
    PendingReqCnt          maxSendWR;
    PendingReqCnt          maxRecvWR;
    ScatterGatherElemCnt   maxSendSGE;
    ScatterGatherElemCnt   maxRecvSGE;
    InlineDataSize         maxInlineData;
} QpCapacity deriving(Bits, FShow);
typedef SizeOf#(QpCapacity)                   QpCapacity_WIDTH;
typedef TDiv#(QpCapacity_WIDTH, 8)            QpCapacity_BYTE_WIDTH;

// --- AttrQP ---
typedef struct {
    StateQP                        qpState;
    StateQP                        curQpState;
    PMTU                           pmtu;
    QKEY                           qkey;
    PSN                            rqPSN;
    PSN                            sqPSN;
    QPN                            dqpn;
    FlagsType#(MemAccessTypeFlag)  qpAccessFlags;
    QpCapacity                     cap;
    PKEY                           pkeyIndex;
    Bool                           sqDraining;
    PendingReqCnt                  maxReadAtomic;
    PendingReqCnt                  maxDestReadAtomic;
    RnrTimer                       minRnrTimer;
    TimeOutTimer                   timeout;
    RetryCnt                       retryCnt;
    RetryCnt                       rnrRetry;
} AttrQP deriving(Bits, FShow);
typedef SizeOf#(AttrQP)                       AttrQP_WIDTH;
typedef TDiv#(AttrQP_WIDTH, 8)                AttrQP_BYTE_WIDTH;

// --- QpInitAttr ---
typedef struct {
    TypeQP  qpType;
    Bool    sqSigAll;
} QpInitAttr deriving(Bits, FShow);
typedef SizeOf#(QpInitAttr)                   QpInitAttr_WIDTH;
typedef TDiv#(QpInitAttr_WIDTH, 8)            QpInitAttr_BYTE_WIDTH;

// --- WorkReq ---
typedef struct {
    WorkReqID                    id;
    WorkReqOpCode                opcode;
    FlagsType#(WorkReqSendFlag)  flags;
    ADDR                         raddr;
    RKEY                         rkey;
    Length                       len;
    ADDR                         laddr;
    LKEY                         lkey;
    QPN                          sqpn;
    Bool                         solicited;
    Maybe#(Long)                 comp;
    Maybe#(Long)                 swap;
    Maybe#(IMM)                  immDt;
    Maybe#(RKEY)                 rkey2Inv;
    Maybe#(QPN)                  srqn;
    Maybe#(QPN)                  dqpn;
    Maybe#(QKEY)                 qkey;
} WorkReq deriving(Bits);
typedef SizeOf#(WorkReq)                      WorkReq_WIDTH;
typedef TDiv#(WorkReq_WIDTH, 8)               WorkReq_BYTE_WIDTH;

// --- PendingWorkReq ---
typedef struct {
    WorkReq        wr;
    Maybe#(PSN)    startPSN;
    Maybe#(PSN)    endPSN;
    Maybe#(PktNum) pktNum;
    Maybe#(Bool)   isOnlyReqPkt;
} PendingWorkReq deriving(Bits);
typedef SizeOf#(PendingWorkReq)               PendingWorkReq_WIDTH;
typedef TDiv#(PendingWorkReq_WIDTH, 8)        PendingWorkReq_BYTE_WIDTH;

// --- RecvReq ---
typedef struct {
    WorkReqID  id;
    Length     len;
    ADDR       laddr;
    LKEY       lkey;
    QPN        sqpn;
} RecvReq deriving(Bits, FShow);
typedef SizeOf#(RecvReq)                      RecvReq_WIDTH;
typedef TDiv#(RecvReq_WIDTH, 8)               RecvReq_BYTE_WIDTH;

// --- WorkComp ---
typedef struct {
    WorkReqID        id;
    WorkCompOpCode   opcode;
    WorkCompFlags    flags;
    WorkCompStatus   status;
    Length           len;
    PKEY             pkey;
    QPN              qpn;
    Maybe#(IMM)      immDt;
    Maybe#(RKEY)     rkey2Inv;
} WorkComp deriving(Bits, FShow);
typedef SizeOf#(WorkComp)                     WorkComp_WIDTH;
typedef TDiv#(WorkComp_WIDTH, 8)              WorkComp_BYTE_WIDTH;

// --- WorkCompGenReqRQ ---
typedef struct {
    Maybe#(WorkReqID)  rrID;
    Length             len;
    PSN                reqPSN;
    Bool               isZeroDmaLen;
    WorkCompStatus     wcStatus;
    RdmaOpCode         reqOpCode;
    Maybe#(IMM)        immDt;
    Maybe#(RKEY)       rkey2Inv;
} WorkCompGenReqRQ deriving(Bits, FShow);
typedef SizeOf#(WorkCompGenReqRQ)             WorkCompGenReqRQ_WIDTH;
typedef TDiv#(WorkCompGenReqRQ_WIDTH, 8)      WorkCompGenReqRQ_BYTE_WIDTH;

// --- WorkCompGenReqSQ ---
typedef struct {
    WorkReq           wr;
    Bool              wcWaitDmaResp;
    WorkCompReqType   wcReqType;
    PSN               triggerPSN;
    WorkCompStatus    wcStatus;
} WorkCompGenReqSQ deriving(Bits, FShow);
typedef SizeOf#(WorkCompGenReqSQ)             WorkCompGenReqSQ_WIDTH;
typedef TDiv#(WorkCompGenReqSQ_WIDTH, 8)      WorkCompGenReqSQ_BYTE_WIDTH;

// ==========================================================================
// Enums
// ==========================================================================

typedef enum {
    RDMA_RESP_NORMAL,
    RDMA_RESP_RETRY,
    RDMA_RESP_ERROR,
    RDMA_RESP_UNKNOWN
} RdmaRespType deriving(Bits, Eq, FShow);

typedef enum {
    RETRY_REASON_NOT_RETRY,
    RETRY_REASON_RNR,
    RETRY_REASON_SEQ_ERR,
    RETRY_REASON_IMPLICIT,
    RETRY_REASON_TIMEOUT
} RetryReason deriving(Bits, Eq, FShow);

typedef enum {
    PKT_ST_VALID,
    PKT_ST_LEN_ERR
} PktVeriStatus deriving(Bits, Bounded, Eq, FShow);

typedef enum {
    DMA_SRC_RQ_RD,
    DMA_SRC_RQ_WR,
    DMA_SRC_RQ_DUP_RD,
    DMA_SRC_RQ_ATOMIC,
    DMA_SRC_RQ_DISCARD,
    DMA_SRC_SQ_RD,
    DMA_SRC_SQ_WR,
    DMA_SRC_SQ_ATOMIC,
    DMA_SRC_SQ_DISCARD
} DmaReqSrcType deriving(Bits, Eq, FShow);

typedef enum {
    IBV_QPS_RESET,
    IBV_QPS_INIT,
    IBV_QPS_RTR,
    IBV_QPS_RTS,
    IBV_QPS_SQD,
    IBV_QPS_SQE,
    IBV_QPS_ERR,
    IBV_QPS_UNKNOWN,
    IBV_QPS_CREATE
} StateQP deriving(Bits, Eq, FShow);

typedef enum {
    IBV_QPT_RC          = 2,
    IBV_QPT_UC          = 3,
    IBV_QPT_UD          = 4,
    IBV_QPT_RAW_PACKET  = 8,
    IBV_QPT_XRC_SEND    = 9,
    IBV_QPT_XRC_RECV    = 10
} TypeQP deriving(Bits, Eq, FShow);

typedef enum {
    IBV_ACCESS_NO_FLAGS       = 0,
    IBV_ACCESS_LOCAL_WRITE    = 1,
    IBV_ACCESS_REMOTE_WRITE   = 2,
    IBV_ACCESS_REMOTE_READ    = 4,
    IBV_ACCESS_REMOTE_ATOMIC  = 8,
    IBV_ACCESS_MW_BIND        = 16,
    IBV_ACCESS_ZERO_BASED     = 32,
    IBV_ACCESS_ON_DEMAND      = 64,
    IBV_ACCESS_HUGETLB        = 128
} MemAccessTypeFlag deriving(Bits, Eq, FShow);

typedef enum {
    IBV_MTU_256  = 1,
    IBV_MTU_512  = 2,
    IBV_MTU_1024 = 3,
    IBV_MTU_2048 = 4,
    IBV_MTU_4096 = 5
} PMTU deriving(Bits, Eq, FShow);

typedef enum {
    IBV_QP_NO_FLAGS              = 0,
    IBV_QP_STATE                 = 1,
    IBV_QP_CUR_STATE             = 2,
    IBV_QP_EN_SQD_ASYNC_NOTIFY   = 4,
    IBV_QP_ACCESS_FLAGS          = 8,
    IBV_QP_PKEY_INDEX            = 16,
    IBV_QP_PORT                  = 32,
    IBV_QP_QKEY                  = 64,
    IBV_QP_AV                    = 128,
    IBV_QP_PATH_MTU              = 256,
    IBV_QP_TIMEOUT               = 512,
    IBV_QP_RETRY_CNT             = 1024,
    IBV_QP_RNR_RETRY             = 2048,
    IBV_QP_RQ_PSN                = 4096,
    IBV_QP_MAX_QP_RD_ATOMIC      = 8192,
    IBV_QP_ALT_PATH              = 16384,
    IBV_QP_MIN_RNR_TIMER         = 32768,
    IBV_QP_SQ_PSN                = 65536,
    IBV_QP_MAX_DEST_RD_ATOMIC    = 131072,
    IBV_QP_PATH_MIG_STATE        = 262144,
    IBV_QP_CAP                   = 524288,
    IBV_QP_DEST_QPN              = 1048576,
    IBV_QP_RATE_LIMIT            = 33554432
} QpAttrMaskFlag deriving(Bits, Eq, FShow);

typedef enum {
    IBV_WR_RDMA_WRITE             = 0,
    IBV_WR_RDMA_WRITE_WITH_IMM    = 1,
    IBV_WR_SEND                   = 2,
    IBV_WR_SEND_WITH_IMM          = 3,
    IBV_WR_RDMA_READ              = 4,
    IBV_WR_ATOMIC_CMP_AND_SWP     = 5,
    IBV_WR_ATOMIC_FETCH_AND_ADD   = 6,
    IBV_WR_LOCAL_INV              = 7,
    IBV_WR_BIND_MW                = 8,
    IBV_WR_SEND_WITH_INV          = 9,
    IBV_WR_TSO                    = 10,
    IBV_WR_DRIVER1                = 11,
    IBV_WR_RDMA_READ_RESP         = 12,
    IBV_WR_FLUSH                  = 14,
    IBV_WR_ATOMIC_WRITE           = 15
} WorkReqOpCode deriving(Bits, Eq, FShow);

typedef enum {
    IBV_SEND_NO_FLAGS  = 0,
    IBV_SEND_FENCE     = 1,
    IBV_SEND_SIGNALED  = 2,
    IBV_SEND_SOLICITED = 4,
    IBV_SEND_INLINE    = 8,
    IBV_SEND_IP_CSUM   = 16
} WorkReqSendFlag deriving(Bits, Eq, FShow);

typedef enum {
    IBV_WC_SEND                = 0,
    IBV_WC_RDMA_WRITE          = 1,
    IBV_WC_RDMA_READ           = 2,
    IBV_WC_COMP_SWAP           = 3,
    IBV_WC_FETCH_ADD           = 4,
    IBV_WC_BIND_MW             = 5,
    IBV_WC_LOCAL_INV           = 6,
    IBV_WC_TSO                 = 7,
    IBV_WC_RECV                = 128,
    IBV_WC_RECV_RDMA_WITH_IMM  = 129,
    IBV_WC_TM_ADD              = 130,
    IBV_WC_TM_DEL              = 131,
    IBV_WC_TM_SYNC             = 132,
    IBV_WC_TM_RECV             = 133,
    IBV_WC_TM_NO_TAG           = 134,
    IBV_WC_DRIVER1             = 135,
    IBV_WC_DRIVER2             = 136,
    IBV_WC_DRIVER3             = 137
} WorkCompOpCode deriving(Bits, Eq, FShow);

typedef enum {
    IBV_WC_SUCCESS              = 0,
    IBV_WC_LOC_LEN_ERR          = 1,
    IBV_WC_LOC_QP_OP_ERR        = 2,
    IBV_WC_LOC_EEC_OP_ERR       = 3,
    IBV_WC_LOC_PROT_ERR         = 4,
    IBV_WC_WR_FLUSH_ERR         = 5,
    IBV_WC_MW_BIND_ERR          = 6,
    IBV_WC_BAD_RESP_ERR         = 7,
    IBV_WC_LOC_ACCESS_ERR       = 8,
    IBV_WC_REM_INV_REQ_ERR      = 9,
    IBV_WC_REM_ACCESS_ERR       = 10,
    IBV_WC_REM_OP_ERR           = 11,
    IBV_WC_RETRY_EXC_ERR        = 12,
    IBV_WC_RNR_RETRY_EXC_ERR    = 13,
    IBV_WC_LOC_RDD_VIOL_ERR     = 14,
    IBV_WC_REM_INV_RD_REQ_ERR   = 15,
    IBV_WC_REM_ABORT_ERR        = 16,
    IBV_WC_INV_EECN_ERR         = 17,
    IBV_WC_INV_EEC_STATE_ERR    = 18,
    IBV_WC_FATAL_ERR            = 19,
    IBV_WC_RESP_TIMEOUT_ERR     = 20,
    IBV_WC_GENERAL_ERR          = 21,
    IBV_WC_TM_ERR               = 22,
    IBV_WC_TM_RNDV_INCOMPLETE   = 23
} WorkCompStatus deriving(Bits, Eq, FShow);

typedef enum {
    IBV_WC_NO_FLAGS      = 0,
    IBV_WC_GRH           = 1,
    IBV_WC_WITH_IMM      = 2,
    IBV_WC_IP_CSUM_OK    = 4,
    IBV_WC_WITH_INV      = 8,
    IBV_WC_TM_SYNC_REQ   = 16,
    IBV_WC_TM_MATCH      = 32,
    IBV_WC_TM_DATA_VALID = 64
} WorkCompFlags deriving(Bits, Eq, FShow);

typedef enum {
    WC_REQ_TYPE_FULL_ACK,
    WC_REQ_TYPE_PARTIAL_ACK,
    WC_REQ_TYPE_NO_WC,
    WC_REQ_TYPE_UNKNOWN
} WorkCompReqType deriving(Bits, Eq, FShow);

typedef enum {
    IBV_EVENT_CQ_ERR,
    IBV_EVENT_QP_FATAL,
    IBV_EVENT_QP_REQ_ERR,
    IBV_EVENT_QP_ACCESS_ERR,
    IBV_EVENT_COMM_EST,
    IBV_EVENT_SQ_DRAINED,
    IBV_EVENT_PATH_MIG,
    IBV_EVENT_PATH_MIG_ERR,
    IBV_EVENT_DEVICE_FATAL,
    IBV_EVENT_PORT_ACTIVE,
    IBV_EVENT_PORT_ERR,
    IBV_EVENT_LID_CHANGE,
    IBV_EVENT_PKEY_CHANGE,
    IBV_EVENT_SM_CHANGE,
    IBV_EVENT_SRQ_ERR,
    IBV_EVENT_SRQ_LIMIT_REACHED,
    IBV_EVENT_QP_LAST_WQE_REACHED,
    IBV_EVENT_CLIENT_REREGISTER,
    IBV_EVENT_GID_CHANGE,
    IBV_EVENT_WQ_FATAL
} AsyncEventType deriving(Bits, Eq);

// ==========================================================================
// Higher-order type aliases (Server / Client / PipeOut / FIFOF variants)
// ==========================================================================
typedef UInt#(MR_INDEX_WIDTH)                     IndexMR;
typedef Bit#(MR_KEY_PART_WIDTH)                   KeyPartMR;

typedef Server#(DmaReadReq, DmaReadResp)          DmaReadSrv;
typedef Server#(DmaWriteReq, DmaWriteResp)        DmaWriteSrv;
typedef Client#(DmaReadReq, DmaReadResp)          DmaReadClt;
typedef Client#(DmaWriteReq, DmaWriteResp)        DmaWriteClt;
typedef Server#(PermCheckReq, Bool)               PermCheckSrv;
typedef Client#(PermCheckReq, Bool)               PermCheckClt;

typedef PipeOut#(DataStream)                      DataStreamPipeOut;
typedef ScanFIFOF#(MAX_QP_WR, PendingWorkReq)     PendingWorkReqBuf;
typedef PipeOut#(RecvReq)                         RecvReqBuf;
