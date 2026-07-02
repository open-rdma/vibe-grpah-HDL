package Headers;

import Reserved :: *;

// ===== Width Constants =====
typedef 64   ADDR_WIDTH;
typedef 64   LONG_WIDTH;
typedef 24   PSN_WIDTH;
typedef 24   QPN_WIDTH;
typedef 32   RDMA_MAX_LEN_WIDTH;
typedef 64   WR_ID_WIDTH;
typedef 2    PAD_WIDTH;
typedef 16   PKEY_WIDTH;
typedef 5    AETH_VALUE_WIDTH;
typedef 24   MSN_WIDTH;
typedef 32   KEY_WIDTH;
typedef 32   IMM_WIDTH;
typedef 256  MIN_PMTU;
typedef 4096 MAX_PMTU;

// ===== Type Aliases =====
typedef Bit#(ADDR_WIDTH)         ADDR;
typedef Bit#(RDMA_MAX_LEN_WIDTH) Length;
typedef Bit#(LONG_WIDTH)         Long;
typedef Bit#(QPN_WIDTH)          QPN;
typedef Bit#(PSN_WIDTH)          PSN;
typedef Bit#(PAD_WIDTH)          PAD;
typedef Bit#(PKEY_WIDTH)         PKEY;
typedef Bit#(AETH_VALUE_WIDTH)   AethValue;
typedef Bit#(MSN_WIDTH)          MSN;
typedef Bit#(KEY_WIDTH)          RKEY;
typedef Bit#(KEY_WIDTH)          LKEY;
typedef Bit#(KEY_WIDTH)          QKEY;
typedef Bit#(IMM_WIDTH)          IMM;

// ===== RC Transport Opcodes =====
typedef 'h00 RC_SEND_FIRST;
typedef 'h01 RC_SEND_MIDDLE;
typedef 'h02 RC_SEND_LAST;
typedef 'h03 RC_SEND_LAST_WITH_IMMEDIATE;
typedef 'h04 RC_SEND_ONLY;
typedef 'h05 RC_SEND_ONLY_WITH_IMMEDIATE;
typedef 'h06 RC_RDMA_WRITE_FIRST;
typedef 'h07 RC_RDMA_WRITE_MIDDLE;
typedef 'h08 RC_RDMA_WRITE_LAST;
typedef 'h09 RC_RDMA_WRITE_LAST_WITH_IMMEDIATE;
typedef 'h0a RC_RDMA_WRITE_ONLY;
typedef 'h0b RC_RDMA_WRITE_ONLY_WITH_IMMEDIATE;
typedef 'h0c RC_RDMA_READ_REQUEST;
typedef 'h0d RC_RDMA_READ_RESPONSE_FIRST;
typedef 'h0e RC_RDMA_READ_RESPONSE_MIDDLE;
typedef 'h0f RC_RDMA_READ_RESPONSE_LAST;
typedef 'h10 RC_RDMA_READ_RESPONSE_ONLY;
typedef 'h11 RC_ACKNOWLEDGE;
typedef 'h12 RC_ATOMIC_ACKNOWLEDGE;
typedef 'h13 RC_COMPARE_SWAP;
typedef 'h14 RC_FETCH_ADD;
typedef 'h16 RC_SEND_LAST_WITH_INVALIDATE;
typedef 'h17 RC_SEND_ONLY_WITH_INVALIDATE;

// ===== XRC Transport Opcodes =====
typedef 'ha0 XRC_SEND_FIRST;
typedef 'ha1 XRC_SEND_MIDDLE;
typedef 'ha2 XRC_SEND_LAST;
typedef 'ha3 XRC_SEND_LAST_WITH_IMMEDIATE;
typedef 'ha4 XRC_SEND_ONLY;
typedef 'ha5 XRC_SEND_ONLY_WITH_IMMEDIATE;
typedef 'ha6 XRC_RDMA_WRITE_FIRST;
typedef 'ha7 XRC_RDMA_WRITE_MIDDLE;
typedef 'ha8 XRC_RDMA_WRITE_LAST;
typedef 'ha9 XRC_RDMA_WRITE_LAST_WITH_IMMEDIATE;
typedef 'haa XRC_RDMA_WRITE_ONLY;
typedef 'hab XRC_RDMA_WRITE_ONLY_WITH_IMMEDIATE;
typedef 'hac XRC_RDMA_READ_REQUEST;
typedef 'had XRC_RDMA_READ_RESPONSE_FIRST;
typedef 'hae XRC_RDMA_READ_RESPONSE_MIDDLE;
typedef 'haf XRC_RDMA_READ_RESPONSE_LAST;
typedef 'hb0 XRC_RDMA_READ_RESPONSE_ONLY;
typedef 'hb1 XRC_ACKNOWLEDGE;
typedef 'hb2 XRC_ATOMIC_ACKNOWLEDGE;
typedef 'hb3 XRC_COMPARE_SWAP;
typedef 'hb4 XRC_FETCH_ADD;
typedef 'hb6 XRC_SEND_LAST_WITH_INVALIDATE;
typedef 'hb7 XRC_SEND_ONLY_WITH_INVALIDATE;

// ===== UD Transport Opcodes =====
typedef 'h64 UD_SEND_ONLY;
typedef 'h65 UD_SEND_ONLY_WITH_IMMEDIATE;
typedef 'h81 ROCE_CNP;

// ===== TransType Enum =====
typedef enum {
    RC  = 3'h0,
    UC  = 3'h1,
    RD  = 3'h2,
    UD  = 3'h3,
    CNP = 3'h4,
    XRC = 3'h5
} TransType deriving(Bits, Bounded, Eq, FShow);

typedef SizeOf#(TransType) TRANS_TYPE_WIDTH;

// ===== RdmaOpCode Enum =====
typedef enum {
    SEND_FIRST                     = 5'h00,
    SEND_MIDDLE                    = 5'h01,
    SEND_LAST                      = 5'h02,
    SEND_LAST_WITH_IMMEDIATE       = 5'h03,
    SEND_ONLY                      = 5'h04,
    SEND_ONLY_WITH_IMMEDIATE       = 5'h05,
    RDMA_WRITE_FIRST               = 5'h06,
    RDMA_WRITE_MIDDLE              = 5'h07,
    RDMA_WRITE_LAST                = 5'h08,
    RDMA_WRITE_LAST_WITH_IMMEDIATE = 5'h09,
    RDMA_WRITE_ONLY                = 5'h0a,
    RDMA_WRITE_ONLY_WITH_IMMEDIATE = 5'h0b,
    RDMA_READ_REQUEST              = 5'h0c,
    RDMA_READ_RESPONSE_FIRST       = 5'h0d,
    RDMA_READ_RESPONSE_MIDDLE      = 5'h0e,
    RDMA_READ_RESPONSE_LAST        = 5'h0f,
    RDMA_READ_RESPONSE_ONLY        = 5'h10,
    ACKNOWLEDGE                    = 5'h11,
    ATOMIC_ACKNOWLEDGE             = 5'h12,
    COMPARE_SWAP                   = 5'h13,
    FETCH_ADD                      = 5'h14,
    RESYNC                         = 5'h15,
    SEND_LAST_WITH_INVALIDATE      = 5'h16,
    SEND_ONLY_WITH_INVALIDATE      = 5'h17
} RdmaOpCode deriving(Bits, Bounded, Eq, FShow);

typedef SizeOf#(RdmaOpCode) RDMA_OPCODE_WIDTH;

// ===== AETH Types =====
typedef enum {
    ACK  = 2'b00,
    RNR  = 2'b01,
    RSVD = 2'b10,
    NAK  = 2'b11
} AethCode deriving(Bits, Bounded, Eq, FShow);

typedef enum {
    INVALID_CREDIT_CNT = 5'b11111
} AethAckValueCreditCnt deriving(Bits, Bounded, Eq, FShow);

typedef enum {
    SEQ_ERR = 5'h0,
    INV_REQ = 5'h1,
    RMT_ACC = 5'h2,
    RMT_OP  = 5'h3,
    INV_RD  = 5'h4
} AethNakValue deriving(Bits, Bounded, Eq, FShow);

// ===== Header Structs =====
typedef struct {
    TransType       trans;
    RdmaOpCode      opcode;
    Bool            solicited;
    ReservedZero#(1) migReq;
    PAD             padCnt;
    ReservedZero#(4) tver;
    PKEY            pkey;
    ReservedZero#(1) fecn;
    ReservedZero#(1) becn;
    ReservedZero#(6) resv6;
    QPN             dqpn;
    Bool            ackReq;
    ReservedZero#(7) resv7;
    PSN             psn;
} BTH deriving(Bits, Bounded, FShow);

typedef struct {
    ReservedZero#(1) rsvd;
    AethCode        code;
    AethValue       value;
    MSN             msn;
} AETH deriving(Bits, Bounded, FShow);

typedef struct {
    ADDR   va;
    RKEY   rkey;
    Length dlen;
} RETH deriving(Bits, Bounded, FShow);

typedef struct {
    ADDR   va;
    LKEY   lkey;
    Length dlen;
} LETH deriving(Bits, Bounded, FShow);

typedef struct {
    ADDR va;
    RKEY rkey;
    Long swap;
    Long comp;
} AtomicEth deriving(Bits, Bounded, FShow);

typedef struct {
    Long orig;
} AtomicAckEth deriving(Bits, Bounded, FShow);

typedef struct {
    IMM data;
} ImmDt deriving(Bits, Bounded, FShow);

typedef struct {
    RKEY rkey;
} IETH deriving(Bits, Bounded, FShow);

typedef struct {
    QKEY            qkey;
    ReservedZero#(8) rsvd;
    QPN             sqpn;
} DETH deriving(Bits, Bounded, FShow);

typedef struct {
    ReservedZero#(8) rsvd;
    QPN             srqn;
} XRCETH deriving(Bits, Bounded, FShow);

typedef struct {
    ReservedZero#(LONG_WIDTH) rsvd1;
    ReservedZero#(LONG_WIDTH) rsvd2;
} PayloadCNP deriving(Bits, Bounded, FShow);

// ===== Header Size Constants =====
typedef SizeOf#(BTH)         BTH_WIDTH;
typedef TDiv#(BTH_WIDTH, 8)  BTH_BYTE_WIDTH;

typedef SizeOf#(AETH)        AETH_WIDTH;
typedef TDiv#(AETH_WIDTH, 8) AETH_BYTE_WIDTH;

typedef SizeOf#(RETH)        RETH_WIDTH;
typedef TDiv#(RETH_WIDTH, 8) RETH_BYTE_WIDTH;

typedef SizeOf#(LETH)        LETH_WIDTH;
typedef TDiv#(LETH_WIDTH, 8) LETH_BYTE_WIDTH;

typedef SizeOf#(AtomicEth)       ATOMIC_ETH_WIDTH;
typedef TDiv#(ATOMIC_ETH_WIDTH, 8) ATOMIC_ETH_BYTE_WIDTH;

typedef SizeOf#(AtomicAckEth)          ATOMIC_ACK_ETH_WIDTH;
typedef TDiv#(ATOMIC_ACK_ETH_WIDTH, 8) ATOMIC_ACK_ETH_BYTE_WIDTH;

typedef SizeOf#(ImmDt)         IMM_DT_WIDTH;
typedef TDiv#(IMM_DT_WIDTH, 8) IMM_DT_BYTE_WIDTH;

typedef SizeOf#(IETH)        IETH_WIDTH;
typedef TDiv#(IETH_WIDTH, 8) IETH_BYTE_WIDTH;

typedef SizeOf#(DETH)        DETH_WIDTH;
typedef TDiv#(DETH_WIDTH, 8) DETH_BYTE_WIDTH;

typedef SizeOf#(XRCETH)        XRCETH_WIDTH;
typedef TDiv#(XRCETH_WIDTH, 8) XRCETH_BYTE_WIDTH;

typedef SizeOf#(PayloadCNP)      PAYLOAD_CNP_WIDTH;
typedef TDiv#(PAYLOAD_CNP_WIDTH, 8) PAYLOAD_CNP_BYTE_WIDTH;

// ===== Functions =====
function Integer calcHeaderLenByTransTypeAndRdmaOpCode(TransType transType, RdmaOpCode rdmaOpCode);
    Bit#(8) key = {pack(transType), pack(rdmaOpCode)};
    Integer result = case (key)
        // --- RC: SEND_FIRST, SEND_MIDDLE, SEND_LAST, SEND_ONLY ---
        8'h00, 8'h01, 8'h02, 8'h04:
            valueOf(BTH_BYTE_WIDTH);

        // --- RC: SEND_LAST_WITH_IMMEDIATE, SEND_ONLY_WITH_IMMEDIATE ---
        8'h03, 8'h05:
            valueOf(BTH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // --- RC: RDMA_WRITE_FIRST ---
        8'h06:
            valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);

        // --- RC: RDMA_WRITE_MIDDLE, RDMA_WRITE_LAST ---
        8'h07, 8'h08:
            valueOf(BTH_BYTE_WIDTH);

        // --- RC: RDMA_WRITE_LAST_WITH_IMMEDIATE, RDMA_WRITE_ONLY_WITH_IMMEDIATE ---
        8'h09, 8'h0b:
            valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // --- RC: RDMA_WRITE_ONLY, RDMA_READ_REQUEST ---
        8'h0a, 8'h0c:
            valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);

        // --- RC/XRC: RDMA_READ_RESPONSE_FIRST/MIDDLE/LAST/ONLY, ACKNOWLEDGE ---
        8'h0d, 8'h0e, 8'h0f, 8'h10, 8'h11,
        8'had, 8'hae, 8'haf, 8'hb0, 8'hb1:
            valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);

        // --- RC/XRC: ATOMIC_ACKNOWLEDGE ---
        8'h12, 8'hb2:
            valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH) + valueOf(ATOMIC_ACK_ETH_BYTE_WIDTH);

        // --- RC: COMPARE_SWAP, FETCH_ADD ---
        8'h13, 8'h14:
            valueOf(BTH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);

        // --- RC: RESYNC ---
        8'h15:
            valueOf(BTH_BYTE_WIDTH);

        // --- RC: SEND_LAST_WITH_INVALIDATE, SEND_ONLY_WITH_INVALIDATE ---
        8'h16, 8'h17:
            valueOf(BTH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);

        // --- UD: SEND_ONLY ---
        8'h64:
            valueOf(BTH_BYTE_WIDTH) + valueOf(DETH_BYTE_WIDTH);

        // --- UD: SEND_ONLY_WITH_IMMEDIATE ---
        8'h65:
            valueOf(BTH_BYTE_WIDTH) + valueOf(DETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // --- CNP: all opcodes ---
        8'h80, 8'h81, 8'h82, 8'h83, 8'h84, 8'h85, 8'h86, 8'h87,
        8'h88, 8'h89, 8'h8a, 8'h8b, 8'h8c, 8'h8d, 8'h8e, 8'h8f,
        8'h90, 8'h91, 8'h92, 8'h93, 8'h94, 8'h95, 8'h96, 8'h97:
            valueOf(BTH_BYTE_WIDTH) + valueOf(PAYLOAD_CNP_BYTE_WIDTH);

        // --- XRC: SEND_FIRST, SEND_MIDDLE, SEND_LAST, SEND_ONLY ---
        8'ha0, 8'ha1, 8'ha2, 8'ha4:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);

        // --- XRC: SEND_LAST_WITH_IMMEDIATE, SEND_ONLY_WITH_IMMEDIATE ---
        8'ha3, 8'ha5:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // --- XRC: RDMA_WRITE_FIRST ---
        8'ha6:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);

        // --- XRC: RDMA_WRITE_MIDDLE, RDMA_WRITE_LAST ---
        8'ha7, 8'ha8:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);

        // --- XRC: RDMA_WRITE_LAST_WITH_IMMEDIATE, RDMA_WRITE_ONLY_WITH_IMMEDIATE ---
        8'ha9, 8'hab:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // --- XRC: RDMA_WRITE_ONLY, RDMA_READ_REQUEST ---
        8'haa, 8'hac:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);

        // --- XRC: COMPARE_SWAP, FETCH_ADD ---
        8'hb3, 8'hb4:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);

        // --- XRC: RESYNC ---
        8'hb5:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);

        // --- XRC: SEND_LAST_WITH_INVALIDATE, SEND_ONLY_WITH_INVALIDATE ---
        8'hb6, 8'hb7:
            valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);

        // --- default: BTH + AETH (UC, RD, and unknown combinations) ---
        default:
            valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);
    endcase;
    return result;
endfunction

function Bool rdmaOpCodeHasPayload(RdmaOpCode opcode);
    return (case (opcode)
        SEND_FIRST,
        SEND_MIDDLE,
        SEND_LAST,
        SEND_LAST_WITH_IMMEDIATE,
        SEND_ONLY,
        SEND_ONLY_WITH_IMMEDIATE,
        RDMA_WRITE_FIRST,
        RDMA_WRITE_MIDDLE,
        RDMA_WRITE_LAST,
        RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RDMA_WRITE_ONLY,
        RDMA_WRITE_ONLY_WITH_IMMEDIATE,
        RDMA_READ_RESPONSE_FIRST,
        RDMA_READ_RESPONSE_MIDDLE,
        RDMA_READ_RESPONSE_LAST,
        RDMA_READ_RESPONSE_ONLY,
        SEND_LAST_WITH_INVALIDATE,
        SEND_ONLY_WITH_INVALIDATE:
            True;
        default:
            False;
    endcase);
endfunction

endpackage: Headers
