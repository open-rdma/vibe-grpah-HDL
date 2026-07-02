Generate the Bluespec SystemVerilog file for: Headers
Module type: typedef_and_functions

## BSV Quick Reference
- typedef VALUE NAME; — numeric constant (e.g., `typedef 32 X;` or `typedef TAdd#(a,b) Y;`)
- typedef Bit#(W) NAME; — bit vector type alias
- typedef enum {A=3'h0, B=3'h1} T deriving(Bits,Eq,FShow); — enumeration
- typedef struct { T1 f1; T2 f2; } S deriving(Bits,FShow); — struct
- SizeOf#(T) — bit width; TDiv#(a,b) — division; TExp#(n) — 2^n
- valueOf(X) — numeric value of typedef
- ReservedZero#(n) — n-bit reserved field (requires `import Reserved :: *;`)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method RTYPE NAME(ARGS); endinterface
- module mkNAME(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;
- Reg#(T) r[N] <- mkCReg(N, v);
- Bool, Bit#(n), Maybe#(T) with tagged Valid v / tagged Invalid
- case (expr) matches tagged Valid .v: ... endcase
- pack(v) / unpack(b) convert to/from bits


## Requirements
Defines the RDMA wire protocol headers used in RoCEv2 (RDMA over Converged Ethernet v2). Includes the Base Transport Header (BTH), various extended transport headers (AETH, RETH, LETH, AtomicEth, etc.), and enumeration types for transport types, RDMA opcodes, and AETH acknowledgment/error codes.


## Type Definitions (output EXACTLY these)
typedef 64 ADDR_WIDTH; // Address bit width
typedef 64 LONG_WIDTH; // Long integer bit width
typedef 24 PSN_WIDTH; // Packet Sequence Number bit width
typedef 24 QPN_WIDTH; // Queue Pair Number bit width
typedef 32 RDMA_MAX_LEN_WIDTH; // Maximum RDMA transfer length bit width
typedef 64 WR_ID_WIDTH; // Work Request ID bit width
typedef 2 PAD_WIDTH; // Padding count bit width
typedef 16 PKEY_WIDTH; // Partition Key bit width
typedef 5 AETH_VALUE_WIDTH; // AETH value field bit width
typedef 24 MSN_WIDTH; // Message Sequence Number bit width
typedef 32 KEY_WIDTH; // Key (R_Key/L_Key/Q_Key) bit width
typedef 32 IMM_WIDTH; // Immediate data bit width
typedef 256 MIN_PMTU; // Minimum Path MTU in bytes
typedef 4096 MAX_PMTU; // Maximum Path MTU in bytes
typedef Bit#(ADDR_WIDTH) ADDR; // Address type
typedef Bit#(RDMA_MAX_LEN_WIDTH) Length; // Byte length type for RDMA operations
typedef Bit#(LONG_WIDTH) Long; // 64-bit long value type
typedef Bit#(QPN_WIDTH) QPN; // Queue Pair Number type
typedef Bit#(PSN_WIDTH) PSN; // Packet Sequence Number type
typedef Bit#(PAD_WIDTH) PAD; // Padding count type
typedef Bit#(PKEY_WIDTH) PKEY; // Partition Key type
typedef Bit#(AETH_VALUE_WIDTH) AethValue; // AETH value field type
typedef Bit#(MSN_WIDTH) MSN; // Message Sequence Number type
typedef Bit#(KEY_WIDTH) RKEY; // Remote Key type (alias for KEY_WIDTH)
typedef Bit#(KEY_WIDTH) LKEY; // Local Key type (alias for KEY_WIDTH)
typedef Bit#(KEY_WIDTH) QKEY; // Queue Key type (alias for KEY_WIDTH)
typedef Bit#(IMM_WIDTH) IMM; // Immediate data type
typedef 8'h00 RC_SEND_FIRST; // RC Send First opcode
typedef 8'h01 RC_SEND_MIDDLE; // RC Send Middle opcode
typedef 8'h02 RC_SEND_LAST; // RC Send Last opcode
typedef 8'h03 RC_SEND_LAST_WITH_IMMEDIATE; // RC Send Last with Immediate opcode
typedef 8'h04 RC_SEND_ONLY; // RC Send Only opcode
typedef 8'h05 RC_SEND_ONLY_WITH_IMMEDIATE; // RC Send Only with Immediate opcode
typedef 8'h06 RC_RDMA_WRITE_FIRST; // RC RDMA Write First opcode
typedef 8'h07 RC_RDMA_WRITE_MIDDLE; // RC RDMA Write Middle opcode
typedef 8'h08 RC_RDMA_WRITE_LAST; // RC RDMA Write Last opcode
typedef 8'h09 RC_RDMA_WRITE_LAST_WITH_IMMEDIATE; // RC RDMA Write Last with Immediate opcode
typedef 8'h0a RC_RDMA_WRITE_ONLY; // RC RDMA Write Only opcode
typedef 8'h0b RC_RDMA_WRITE_ONLY_WITH_IMMEDIATE; // RC RDMA Write Only with Immediate opcode
typedef 8'h0c RC_RDMA_READ_REQUEST; // RC RDMA Read Request opcode
typedef 8'h0d RC_RDMA_READ_RESPONSE_FIRST; // RC RDMA Read Response First opcode
typedef 8'h0e RC_RDMA_READ_RESPONSE_MIDDLE; // RC RDMA Read Response Middle opcode
typedef 8'h0f RC_RDMA_READ_RESPONSE_LAST; // RC RDMA Read Response Last opcode
typedef 8'h10 RC_RDMA_READ_RESPONSE_ONLY; // RC RDMA Read Response Only opcode
typedef 8'h11 RC_ACKNOWLEDGE; // RC Acknowledge opcode
typedef 8'h12 RC_ATOMIC_ACKNOWLEDGE; // RC Atomic Acknowledge opcode
typedef 8'h13 RC_COMPARE_SWAP; // RC Compare and Swap opcode
typedef 8'h14 RC_FETCH_ADD; // RC Fetch and Add opcode
typedef 8'h16 RC_SEND_LAST_WITH_INVALIDATE; // RC Send Last with Invalidate opcode
typedef 8'h17 RC_SEND_ONLY_WITH_INVALIDATE; // RC Send Only with Invalidate opcode
typedef 8'ha0 XRC_SEND_FIRST; // XRC Send First opcode
typedef 8'ha1 XRC_SEND_MIDDLE; // XRC Send Middle opcode
typedef 8'ha2 XRC_SEND_LAST; // XRC Send Last opcode
typedef 8'ha3 XRC_SEND_LAST_WITH_IMMEDIATE; // XRC Send Last with Immediate opcode
typedef 8'ha4 XRC_SEND_ONLY; // XRC Send Only opcode
typedef 8'ha5 XRC_SEND_ONLY_WITH_IMMEDIATE; // XRC Send Only with Immediate opcode
typedef 8'ha6 XRC_RDMA_WRITE_FIRST; // XRC RDMA Write First opcode
typedef 8'ha7 XRC_RDMA_WRITE_MIDDLE; // XRC RDMA Write Middle opcode
typedef 8'ha8 XRC_RDMA_WRITE_LAST; // XRC RDMA Write Last opcode
typedef 8'ha9 XRC_RDMA_WRITE_LAST_WITH_IMMEDIATE; // XRC RDMA Write Last with Immediate opcode
typedef 8'haa XRC_RDMA_WRITE_ONLY; // XRC RDMA Write Only opcode
typedef 8'hab XRC_RDMA_WRITE_ONLY_WITH_IMMEDIATE; // XRC RDMA Write Only with Immediate opcode
typedef 8'hac XRC_RDMA_READ_REQUEST; // XRC RDMA Read Request opcode
typedef 8'had XRC_RDMA_READ_RESPONSE_FIRST; // XRC RDMA Read Response First opcode
typedef 8'hae XRC_RDMA_READ_RESPONSE_MIDDLE; // XRC RDMA Read Response Middle opcode
typedef 8'haf XRC_RDMA_READ_RESPONSE_LAST; // XRC RDMA Read Response Last opcode
typedef 8'hb0 XRC_RDMA_READ_RESPONSE_ONLY; // XRC RDMA Read Response Only opcode
typedef 8'hb1 XRC_ACKNOWLEDGE; // XRC Acknowledge opcode
typedef 8'hb2 XRC_ATOMIC_ACKNOWLEDGE; // XRC Atomic Acknowledge opcode
typedef 8'hb3 XRC_COMPARE_SWAP; // XRC Compare and Swap opcode
typedef 8'hb4 XRC_FETCH_ADD; // XRC Fetch and Add opcode
typedef 8'hb6 XRC_SEND_LAST_WITH_INVALIDATE; // XRC Send Last with Invalidate opcode
typedef 8'hb7 XRC_SEND_ONLY_WITH_INVALIDATE; // XRC Send Only with Invalidate opcode
typedef 8'h64 UD_SEND_ONLY; // UD Send Only opcode
typedef 8'h65 UD_SEND_ONLY_WITH_IMMEDIATE; // UD Send Only with Immediate opcode
typedef 8'h81 ROCE_CNP; // RoCEv2 Congestion Notification Packet opcode

## Enums
typedef enum {
    TRANS_TYPE_RC  = 3'h0,
    TRANS_TYPE_UC  = 3'h1,
    TRANS_TYPE_RD  = 3'h2,
    TRANS_TYPE_UD  = 3'h3,
    TRANS_TYPE_CNP = 3'h4,
    TRANS_TYPE_XRC = 3'h5,
} TransType deriving(Bits, Bounded, Eq, FShow);
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
    SEND_ONLY_WITH_INVALIDATE      = 5'h17,
} RdmaOpCode deriving(Bits, Bounded, Eq, FShow);
typedef enum {
    AETH_CODE_ACK  = 2'b00,
    AETH_CODE_RNR  = 2'b01,
    AETH_CODE_RSVD = 2'b10,
    AETH_CODE_NAK  = 2'b11,
} AethCode deriving(Bits, Bounded, Eq, FShow);
typedef enum {
    AETH_ACK_VALUE_INVALID_CREDIT_CNT = 5'b11111,
} AethAckValueCreditCnt deriving(Bits, Bounded, Eq);
typedef enum {
    AETH_NAK_SEQ_ERR = 5'h0,
    AETH_NAK_INV_REQ = 5'h1,
    AETH_NAK_RMT_ACC = 5'h2,
    AETH_NAK_RMT_OP  = 5'h3,
    AETH_NAK_INV_RD  = 5'h4,
} AethNakValue deriving(Bits, Bounded, Eq);

## Structs
typedef struct {
    TransType trans; // Transport type
    RdmaOpCode opcode; // RDMA operation code
    Bool solicited; // Solicited event flag
    ReservedZero#(1) migReq; // Migration request (not supported)
    PAD padCnt; // Padding byte count
    ReservedZero#(4) tver; // Transport header version
    PKEY pkey; // Partition key
    ReservedZero#(1) fecn; // Forward ECN (not used in RoCEv2)
    ReservedZero#(1) becn; // Backward ECN (not used in RoCEv2)
    ReservedZero#(6) resv6; // Reserved field (6 bits)
    QPN dqpn; // Destination Queue Pair Number
    Bool ackReq; // Acknowledge request flag
    ReservedZero#(7) resv7; // Reserved field (7 bits)
    PSN psn; // Packet Sequence Number
} BTH deriving(Bits, Bounded, FShow);
typedef SizeOf#(BTH) BTH_WIDTH;
typedef TDiv#(BTH_WIDTH, 8) BTH_BYTE_WIDTH;
typedef struct {
    ReservedZero#(1) rsvd; // Reserved
    AethCode code; // ACK/RNR/NAK code
    AethValue value; // ACK credit count or NAK error code
    MSN msn; // Message Sequence Number
} AETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(AETH) AETH_WIDTH;
typedef TDiv#(AETH_WIDTH, 8) AETH_BYTE_WIDTH;
typedef struct {
    ADDR va; // Virtual address on remote node
    RKEY rkey; // Remote key for access control
    Length dlen; // Data length in bytes
} RETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(RETH) RETH_WIDTH;
typedef TDiv#(RETH_WIDTH, 8) RETH_BYTE_WIDTH;
typedef struct {
    ADDR va; // Virtual address on local node
    LKEY lkey; // Local key for access control
    Length dlen; // Data length in bytes
} LETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(LETH) LETH_WIDTH;
typedef TDiv#(LETH_WIDTH, 8) LETH_BYTE_WIDTH;
typedef struct {
    ADDR va; // Virtual address on remote node
    RKEY rkey; // Remote key
    Long swap; // Swap value (64-bit)
    Long comp; // Compare value (64-bit)
} AtomicEth deriving(Bits, Bounded, FShow);
typedef SizeOf#(AtomicEth) AtomicEth_WIDTH;
typedef TDiv#(AtomicEth_WIDTH, 8) AtomicEth_BYTE_WIDTH;
typedef struct {
    Long orig; // Original value before atomic operation
} AtomicAckEth deriving(Bits, Bounded, FShow);
typedef SizeOf#(AtomicAckEth) AtomicAckEth_WIDTH;
typedef TDiv#(AtomicAckEth_WIDTH, 8) AtomicAckEth_BYTE_WIDTH;
typedef struct {
    IMM data; // Immediate data value
} ImmDt deriving(Bits, Bounded, FShow);
typedef SizeOf#(ImmDt) ImmDt_WIDTH;
typedef TDiv#(ImmDt_WIDTH, 8) ImmDt_BYTE_WIDTH;
typedef struct {
    RKEY rkey; // Remote key to invalidate
} IETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(IETH) IETH_WIDTH;
typedef TDiv#(IETH_WIDTH, 8) IETH_BYTE_WIDTH;
typedef struct {
    QKEY qkey; // Queue key
    ReservedZero#(8) rsvd; // Reserved
    QPN sqpn; // Source Queue Pair Number
} DETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(DETH) DETH_WIDTH;
typedef TDiv#(DETH_WIDTH, 8) DETH_BYTE_WIDTH;
typedef struct {
    ReservedZero#(8) rsvd; // Reserved
    QPN srqn; // Shared Receive Queue Number
} XRCETH deriving(Bits, Bounded, FShow);
typedef SizeOf#(XRCETH) XRCETH_WIDTH;
typedef TDiv#(XRCETH_WIDTH, 8) XRCETH_BYTE_WIDTH;
typedef struct {
    ReservedZero#(LONG_WIDTH) rsvd1; // Reserved
    ReservedZero#(LONG_WIDTH) rsvd2; // Reserved
} PayloadCNP deriving(Bits, Bounded, FShow);
typedef SizeOf#(PayloadCNP) PayloadCNP_WIDTH;
typedef TDiv#(PayloadCNP_WIDTH, 8) PayloadCNP_BYTE_WIDTH;

## Functions

function Integer calcHeaderLenByTransTypeAndRdmaOpCode(TransType transType, RdmaOpCode rdmaOpCode);
// Calculate the total header length in bytes for a given transport type and RDMA opcode combination. Uses a case statement on the concatenation of transport type and opcode. Key rules: - SEND_FIRST/MIDDLE/LAST/ONLY: BTH only (12 bytes) - SEND with IMMEDIATE: BTH + ImmDt (12 + 4 = 16 bytes) - RDMA_WRITE_FIRST/ONLY: BTH + RETH (12 + 16 = 28 bytes) - RDMA_WRITE_MIDDLE/LAST: BTH only (12 bytes) - RDMA_WRITE with IMMEDIATE: BTH + RETH + ImmDt (12 + 16 + 4 = 32 bytes) - RDMA_READ_REQUEST: BTH + RETH (12 + 16 = 28 bytes) - COMPARE_SWAP/FETCH_ADD: BTH + AtomicEth (12 + 28 = 40 bytes) - SEND with INVALIDATE: BTH + IETH (12 + 4 = 16 bytes) - READ_RESPONSE_FIRST/LAST/ONLY: BTH + AETH (12 + 4 = 16 bytes) - READ_RESPONSE_MIDDLE: BTH only (12 bytes) - ACKNOWLEDGE: BTH + AETH (12 + 4 = 16 bytes) - ATOMIC_ACKNOWLEDGE: BTH + AETH + AtomicAckEth (12 + 4 + 8 = 24 bytes) - XRC variants: add XRCETH (4 bytes) to corresponding RC sizes - UD_SEND_ONLY: BTH + DETH (12 + 8 = 20 bytes) - UD with IMMEDIATE: BTH + DETH + ImmDt (12 + 8 + 4 = 24 bytes) - CNP: BTH + PayloadCNP (12 + 16 = 28 bytes) Use the corresponding BYTE_WIDTH constants (BTH_BYTE_WIDTH, RETH_BYTE_WIDTH, etc.) defined via SizeOf# and TDiv# after each struct. Use fromInteger(valueOf(...)) to convert opcode constants to Integer for case matching. Use '{' pack(transType), pack(rdmaOpCode) '}' as the case discriminant. default: return 0.

// Implement using BSV syntax. end with endfunction

function Bool rdmaOpCodeHasPayload(RdmaOpCode opcode);
// Returns True if the given RDMA opcode carries a data payload. Payload-carrying opcodes include: - All SEND variants (SEND_FIRST through SEND_ONLY_WITH_INVALIDATE) - All RDMA_WRITE variants (RDMA_WRITE_FIRST through RDMA_WRITE_ONLY_WITH_IMMEDIATE) - All RDMA_READ_RESPONSE variants (READ_RESPONSE_FIRST through READ_RESPONSE_ONLY) All other opcodes return False (ACKNOWLEDGE, ATOMIC_ACKNOWLEDGE, etc.) Use a case statement with the opcode directly; list all True opcodes and default to False.

// Implement using BSV syntax. end with endfunction


Output ONLY the valid BSV code in a ```bsv block. No explanations.
Include all needed import statements.
The code must compile with: bsc -elab -sim Headers.bsv

Generate BSV now: