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


Generate BSV functions for: InputPktHandle

Types already defined (import them): InputPktHandle

function Bool checkZeroFields4BTH(BTH bth);
  // Reference implementation:
  // function Bool checkZeroFields4BTH(BTH bth);
    let bthRsvdCheck =
        isZero(pack(bth.tver))  &&
        isZero(pack(bth.fecn))  &&
        isZero(pack(bth.becn))  &&
        isZero(pack(bth.resv6)) &&
        isZero(pack(bth.resv7));
    return bthRsvdCheck;
endfunction

function Bool padCntCheckReqHeader(BTH bth);
  // Reference implementation:
  // function Bool padCntCheckReqHeader(BTH bth);
    let zeroPadCntCheck = isZero(bth.padCnt);

    return case (bth.opcode)
        SEND_FIRST, SEND_MIDDLE            : zeroPadCntCheck;
        SEND_LAST, SEND_ONLY               ,
        SEND_LAST_WITH_IMMEDIATE           ,
        SEND_ONLY_WITH_IMMEDIATE           ,
        SEND_LAST_WITH_INVALIDATE          ,
        SEND_ONLY_WITH_INVALIDATE          : True;

        RDMA_WRITE_FIRST, RDMA_WRITE_MIDDLE: zeroPadCntCheck;
        RDMA_WRITE_LAST

function Bool padCntCheckRespHeader(BTH bth, AETH aeth);
  // Reference implementation:
  // function Bool padCntCheckRespHeader(BTH bth, AETH aeth);
    let zeroPadCntCheck = isZero(bth.padCnt);

    case (bth.opcode)
        RDMA_READ_RESPONSE_MIDDLE: return zeroPadCntCheck;
        RDMA_READ_RESPONSE_LAST  ,
        RDMA_READ_RESPONSE_ONLY  : return aeth.code == AETH_CODE_ACK;
        RDMA_READ_RESPONSE_FIRST ,
        ATOMIC_ACKNOWLEDGE       : return aeth.code == AETH_CODE_ACK && zeroPadCntCheck;
        ACKNOWLEDGE              : case (aeth.code)
            AETH_CODE_ACK,
       

function Bool validateHeader(TransType transType, QKEY qkey, CntrlStatus cntrlStatus, Bool isRespPkt);
  // Reference implementation:
  // function Bool validateHeader(TransType transType, QKEY qkey, CntrlStatus cntrlStatus, Bool isRespPkt);
    let transTypeMatch = transTypeMatchQpType(transType, cntrlStatus.getTypeQP, isRespPkt);
    let qpStateMatch = cntrlStatus.comm.isERR ||
        (isRespPkt ? cntrlStatus.comm.isRTS : cntrlStatus.comm.isNonErr);
    // UD has no responses
    let qKeyMatch = transType == TRANS_TYPE_UD ? qkey == cntrlStatus.comm.getQKEY : True;
    // TODO: verify RoCEv2 only use default PKEY
    // let pKeyM

function ? unknown();
  // Reference implementation:
  //     function Bool fifofNotEmpty(FIFOF#(anytype) fifof) = fifof.notEmpty;
    function Bool fifofNotFull(FIFOF#(anytype) fifof) = fifof.notFull;
    function Bool fifofVecAll(
        function Bool mapFunc(FIFOF#(anytype) fifof),
        Vector#(vSz, FIFOF#(anytype)) fifofVec
    ) provisos(Add#(1, anysize, vSz));
        let fifofMapVec = map(mapFunc, fifofVec);
        let result = fold(\&& , fifofMapVec);
        return result;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function InputRdmaPktBuf genInputRdmaPktBuf(Integer idx);
        return interface InputRdmaPktBuf;
            interface reqPktPipeOut = interface RdmaPktMetaDataAndPayloadPipeOut;
                interface pktMetaData = toPipeOut(reqPktMetaDataOutVec[idx]);
                interface payload     = toPipeOut(reqPayloadOutVec[idx]);
            endinterface;

            interface respPktPipeOut = interface RdmaPktMetaDataAndPayloadPipeOut;
                interface pktMetaData = toPipeOut(re

Output in ```bsv block. Include imports referencing existing types. Generate now: