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


Generate BSV functions for: RetryHandleSQ

Types already defined (import them): RetryHandleSQ

function ? unknown();
  // Reference implementation:
  //     function Bool retryCntExceedLimit(RetryReason retryReason);
        return case (retryReason)
            RETRY_REASON_RNR     : isZero(rnrCntReg);
            RETRY_REASON_SEQ_ERR ,
            RETRY_REASON_IMPLICIT,
            RETRY_REASON_TIMEOUT : isZero(retryCntReg);
            // RETRY_REASON_NOT_RETRY
            default              : False;
        endcase;
    endfunction

function ? unknown();
  // Reference implementation:
  //     function Action decRetryCntByReason(RetryReason retryReason);
        action
            case (retryReason)
                RETRY_REASON_SEQ_ERR ,
                RETRY_REASON_IMPLICIT,
                RETRY_REASON_TIMEOUT : begin
                    if (!disableRetryCntReg) begin
                        if (!isZero(retryCntReg)) begin
                            retryCntReg <= retryCntReg - 1;
                        end
                    end
                end
                RETRY_REAS

function ? unknown();
  // Reference implementation:
  //     function Action resetRetryCntInternal();
        action
            retryCntReg        <= cntrlStatus.comm.getMaxRetryCnt;
            rnrCntReg          <= cntrlStatus.comm.getMaxRnrCnt;
            disableRetryCntReg <= cntrlStatus.comm.getMaxRetryCnt == fromInteger(valueOf(INFINITE_RETRY));
            // $display(
            //     "time=%0t: resetRetryCntInternal cntrlStatus.comm.getMaxRetryCnt=%0d",
            //     $time, cntrlStatus.comm.getMaxRetryCnt
            // );
        en

function ? unknown();
  // Reference implementation:
  //     function Action resetTimeOutCntInternal();
        action
            timeOutCntReg       <= fromInteger(getTimeOutValue(cntrlStatus.comm.getMaxTimeOut));
            disableTimeOutReg   <= isZero(cntrlStatus.comm.getMaxTimeOut);
            // isTimeOutCntZeroReg <= False;
            isTimeOutCntHighPartZeroReg <= False;
            isTimeOutCntLowPartZeroReg  <= False;
            // timeOutNotificationQ.clear;
            // $display(
            //     "time=%0t: resetTimeOutCntInternal

Output in ```bsv block. Include imports referencing existing types. Generate now: