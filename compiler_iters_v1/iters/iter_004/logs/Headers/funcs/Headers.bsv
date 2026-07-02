function Integer calcHeaderLenByTransTypeAndRdmaOpCode(
    TransType transType, RdmaOpCode rdmaOpCode
);
    return case ({ pack(transType), pack(rdmaOpCode) })
        // RC requests
        fromInteger(valueOf(RC_SEND_FIRST))                    : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_MIDDLE))                   : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_LAST))                     : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_LAST_WITH_IMMEDIATE))      : valueOf(BTH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_ONLY))                     : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_ONLY_WITH_IMMEDIATE))      : valueOf(BTH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_FIRST))              : valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_MIDDLE))             : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_LAST))               : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_LAST_WITH_IMMEDIATE)): valueOf(BTH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_ONLY))               : valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_WRITE_ONLY_WITH_IMMEDIATE)): valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_READ_REQUEST))             : valueOf(BTH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_COMPARE_SWAP))                  : valueOf(BTH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_FETCH_ADD))                     : valueOf(BTH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_LAST_WITH_INVALIDATE))     : valueOf(BTH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_SEND_ONLY_WITH_INVALIDATE))     : valueOf(BTH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);

        // RC and XRC responses
        fromInteger(valueOf(RC_RDMA_READ_RESPONSE_FIRST)),  fromInteger(valueOf(XRC_RDMA_READ_RESPONSE_FIRST))  : valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_READ_RESPONSE_MIDDLE)), fromInteger(valueOf(XRC_RDMA_READ_RESPONSE_MIDDLE)) : valueOf(BTH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_READ_RESPONSE_LAST)),   fromInteger(valueOf(XRC_RDMA_READ_RESPONSE_LAST))   : valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_RDMA_READ_RESPONSE_ONLY)),   fromInteger(valueOf(XRC_RDMA_READ_RESPONSE_ONLY))   : valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_ACKNOWLEDGE)),               fromInteger(valueOf(XRC_ACKNOWLEDGE))               : valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH);
        fromInteger(valueOf(RC_ATOMIC_ACKNOWLEDGE)),        fromInteger(valueOf(XRC_ATOMIC_ACKNOWLEDGE))        : valueOf(BTH_BYTE_WIDTH) + valueOf(AETH_BYTE_WIDTH) + valueOf(ATOMIC_ACK_ETH_BYTE_WIDTH);

        // XRC requests
        fromInteger(valueOf(XRC_SEND_FIRST))                    : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_MIDDLE))                   : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_LAST))                     : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_LAST_WITH_IMMEDIATE))      : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_ONLY))                     : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_ONLY_WITH_IMMEDIATE))      : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_FIRST))              : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_MIDDLE))             : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_LAST))               : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_LAST_WITH_IMMEDIATE)): valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_ONLY))               : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_WRITE_ONLY_WITH_IMMEDIATE)): valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);
        fromInteger(valueOf(XRC_RDMA_READ_REQUEST))             : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(RETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_COMPARE_SWAP))                  : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_FETCH_ADD))                     : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(ATOMIC_ETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_LAST_WITH_INVALIDATE))     : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);
        fromInteger(valueOf(XRC_SEND_ONLY_WITH_INVALIDATE))     : valueOf(BTH_BYTE_WIDTH) + valueOf(XRCETH_BYTE_WIDTH) + valueOf(IETH_BYTE_WIDTH);

        // UD requests
        fromInteger(valueOf(UD_SEND_ONLY))                      : valueOf(BTH_BYTE_WIDTH) + valueOf(DETH_BYTE_WIDTH);
        fromInteger(valueOf(UD_SEND_ONLY_WITH_IMMEDIATE))       : valueOf(BTH_BYTE_WIDTH) + valueOf(DETH_BYTE_WIDTH) + valueOf(IMM_DT_BYTE_WIDTH);

        // CNP
        fromInteger(valueOf(CNP))                               : valueOf(BTH_BYTE_WIDTH) + valueOf(PAYLOAD_CNP_BYTE_WIDTH);

        default: 0;
    endcase;
endfunction


function Bool rdmaOpCodeHasPayload(RdmaOpCode opcode);
    return case (opcode)
        // SEND variants
        RC_SEND_FIRST,
        RC_SEND_MIDDLE,
        RC_SEND_LAST,
        RC_SEND_LAST_WITH_IMMEDIATE,
        RC_SEND_ONLY,
        RC_SEND_ONLY_WITH_IMMEDIATE,
        RC_SEND_LAST_WITH_INVALIDATE,
        RC_SEND_ONLY_WITH_INVALIDATE,
        // RDMA_WRITE variants
        RC_RDMA_WRITE_FIRST,
        RC_RDMA_WRITE_MIDDLE,
        RC_RDMA_WRITE_LAST,
        RC_RDMA_WRITE_LAST_WITH_IMMEDIATE,
        RC_RDMA_WRITE_ONLY,
        RC_RDMA_WRITE_ONLY_WITH_IMMEDIATE,
        // RDMA_READ_RESPONSE variants (RC)
        RC_RDMA_READ_RESPONSE_FIRST,
        RC_RDMA_READ_RESPONSE_MIDDLE,
        RC_RDMA_READ_RESPONSE_LAST,
        RC_RDMA_READ_RESPONSE_ONLY,
        // XRC SEND variants
        XRC_SEND_FIRST,
        XRC_SEND_MIDDLE,
        XRC_SEND_LAST,
        XRC_SEND_LAST_WITH_IMMEDIATE,
        XRC_SEND_ONLY,
        XRC_SEND_ONLY_WITH_IMMEDIATE,
        XRC_SEND_LAST_WITH_INVALIDATE,
        XRC_SEND_ONLY_WITH_INVALIDATE,
        // XRC RDMA_WRITE variants
        XRC_RDMA_WRITE_FIRST,
        XRC_RDMA_WRITE_MIDDLE,
        XRC_RDMA_WRITE_LAST,
        XRC_RDMA_WRITE_LAST_WITH_IMMEDIATE,
        XRC_RDMA_WRITE_ONLY,
        XRC_RDMA_WRITE_ONLY_WITH_IMMEDIATE,
        // XRC RDMA_READ_RESPONSE variants
        XRC_RDMA_READ_RESPONSE_FIRST,
        XRC_RDMA_READ_RESPONSE_MIDDLE,
        XRC_RDMA_READ_RESPONSE_LAST,
        XRC_RDMA_READ_RESPONSE_ONLY,
        // UD SEND variants
        UD_SEND_ONLY,
        UD_SEND_ONLY_WITH_IMMEDIATE: True;
        default: False;
    endcase;
endfunction
