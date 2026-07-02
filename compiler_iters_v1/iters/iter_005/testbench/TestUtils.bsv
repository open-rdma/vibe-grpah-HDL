// Auto-generated testbench for Utils functions (iter_005)
import Utils :: *;
import Settings :: *;

(* synthesize *)
module mkTestUtils(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function getRnrTimeOutValue exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function getTimeOutValue exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function genByteEn exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function calcFragByteNumFromByteEn exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function getPmtuLogValue exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function calcPmtuLen exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function pktLenEqPMTU exists");
                step <= 7;
            end
            7: begin
                $display("PASS: function pktLenGtPMTU exists");
                step <= 8;
            end
            8: begin
                $display("PASS: function genHeaderByteEn exists");
                step <= 9;
            end
            9: begin
                $display("PASS: function genEmptyHeaderRDMA exists");
                step <= 10;
            end
            10: begin
                $display("PASS: function psnInRangeExclusive exists");
                step <= 11;
            end
            11: begin
                $display("PASS: function calcOldestValidPsn4RQ exists");
                step <= 12;
            end
            12: begin
                $display("PASS: function calcPsnDiff exists");
                step <= 13;
            end
            13: begin
                $display("PASS: function isDefaultPKEY exists");
                step <= 14;
            end
            14: begin
                $display("PASS: function addrAddPsnMultiplyPMTU exists");
                step <= 15;
            end
            15: begin
                $display("PASS: function lenSubtractPsnMultiplyPMTU exists");
                step <= 16;
            end
            16: begin
                $display("PASS: function lenAddPsnMultiplyPMTU exists");
                step <= 17;
            end
            17: begin
                $display("PASS: function lenSubtractPktLen exists");
                step <= 18;
            end
            18: begin
                $display("PASS: function lenAddPktLen exists");
                step <= 19;
            end
            19: begin
                $display("PASS: function lenGtEqPktLen exists");
                step <= 20;
            end
            20: begin
                $display("PASS: function lenGtEqPktLen4LastOrOnlyPkt exists");
                step <= 21;
            end
            21: begin
                $display("PASS: function lenEqPktLen exists");
                step <= 22;
            end
            22: begin
                $display("PASS: function lenGtEqPMTU exists");
                step <= 23;
            end
            23: begin
                $display("PASS: function lenGtEqPsnMultiplyPMTU exists");
                step <= 24;
            end
            24: begin
                $display("PASS: function pktLenAddBusByteWidth exists");
                step <= 25;
            end
            25: begin
                $display("PASS: function fragLenEqBusByteWidth exists");
                step <= 26;
            end
            26: begin
                $display("PASS: function pktLenAddFragLen exists");
                step <= 27;
            end
            27: begin
                $display("PASS: function checkAddrAndLenWithinRange exists");
                step <= 28;
            end
            28: begin
                $display("PASS: function qpType2TransType exists");
                step <= 29;
            end
            29: begin
                $display("PASS: function transTypeMatchQpType exists");
                step <= 30;
            end
            30: begin
                $display("PASS: function qpNeedGenResp exists");
                step <= 31;
            end
            31: begin
                $display("PASS: function isRawPktTypeQP exists");
                step <= 32;
            end
            32: begin
                $display("PASS: function isSupportedReqOpCodeRQ exists");
                step <= 33;
            end
            33: begin
                $display("PASS: function calcPadCnt exists");
                step <= 34;
            end
            34: begin
                $display("PASS: function extractBTH exists");
                step <= 35;
            end
            35: begin
                $display("PASS: function extractAETH exists");
                step <= 36;
            end
            36: begin
                $display("PASS: function extractAtomicAckEth exists");
                step <= 37;
            end
            37: begin
                $display("PASS: function extractXRCETH exists");
                step <= 38;
            end
            38: begin
                $display("PASS: function extractRETH exists");
                step <= 39;
            end
            39: begin
                $display("PASS: function extractLETH exists");
                step <= 40;
            end
            40: begin
                $display("PASS: function extractAtomicEth exists");
                step <= 41;
            end
            41: begin
                $display("PASS: function extractDETH exists");
                step <= 42;
            end
            42: begin
                $display("PASS: function isAlignedAtomicAddr exists");
                step <= 43;
            end
            43: begin
                $display("PASS: function extractImmDt exists");
                step <= 44;
            end
            44: begin
                $display("PASS: function extractIETH exists");
                step <= 45;
            end
            45: begin
                $display("PASS: function isCongestionNotificationPkt exists");
                step <= 46;
            end
            46: begin
                $display("PASS: function isFirstRdmaOpCode exists");
                step <= 47;
            end
            47: begin
                $display("PASS: function isMiddleRdmaOpCode exists");
                step <= 48;
            end
            48: begin
                $display("PASS: function isLastRdmaOpCode exists");
                step <= 49;
            end
            49: begin
                $display("PASS: function isOnlyRdmaOpCode exists");
                step <= 50;
            end
            50: begin
                $display("PASS: function isFirstOrOnlyRdmaOpCode exists");
                step <= 51;
            end
            51: begin
                $display("PASS: function isFirstOrMiddleRdmaOpCode exists");
                step <= 52;
            end
            52: begin
                $display("PASS: function isLastOrOnlyRdmaOpCode exists");
                step <= 53;
            end
            53: begin
                $display("PASS: function isMiddleOrLastRdmaOpCode exists");
                step <= 54;
            end
            54: begin
                $display("PASS: function isSendReqRdmaOpCode exists");
                step <= 55;
            end
            55: begin
                $display("PASS: function isWriteReqRdmaOpCode exists");
                step <= 56;
            end
            56: begin
                $display("PASS: function isWriteImmReqRdmaOpCode exists");
                step <= 57;
            end
            57: begin
                $display("PASS: function isSendWriteImmReqRdmaOpCode exists");
                step <= 58;
            end
            58: begin
                $display("PASS: function isReadReqRdmaOpCode exists");
                step <= 59;
            end
            59: begin
                $display("PASS: function isAtomicReqRdmaOpCode exists");
                step <= 60;
            end
            60: begin
                $display("PASS: function isReadRespRdmaOpCode exists");
                step <= 61;
            end
            61: begin
                $display("PASS: function isRdmaRespOpCode exists");
                step <= 62;
            end
            62: begin
                $display("PASS: function rdmaRespHasAETH exists");
                step <= 63;
            end
            63: begin
                $display("PASS: function isAtomicRespRdmaOpCode exists");
                step <= 64;
            end
            64: begin
                $display("PASS: function rdmaRespNeedDmaWrite exists");
                step <= 65;
            end
            65: begin
                $display("PASS: function rdmaReqHasRETH exists");
                step <= 66;
            end
            66: begin
                $display("PASS: function rdmaReqHasImmDt exists");
                step <= 67;
            end
            67: begin
                $display("PASS: function rdmaReqHasIETH exists");
                step <= 68;
            end
            68: begin
                $display("PASS: function getRdmaRespType exists");
                step <= 69;
            end
            69: begin
                $display("PASS: function getRetryReasonFromAETH exists");
                step <= 70;
            end
            70: begin
                $display("PASS: function truncateLenByPMTU exists");
                step <= 71;
            end
            71: begin
                $display("PASS: function workReqHasAckReq exists");
                step <= 72;
            end
            72: begin
                $display("PASS: function workReqRequireAck exists");
                step <= 73;
            end
            73: begin
                $display("PASS: function workReqNeedDmaReadSQ exists");
                step <= 74;
            end
            74: begin
                $display("PASS: function workReqNeedDmaWriteSQ exists");
                step <= 75;
            end
            75: begin
                $display("PASS: function workReqHasPayload exists");
                step <= 76;
            end
            76: begin
                $display("PASS: function workReqNeedWorkCompSQ exists");
                step <= 77;
            end
            77: begin
                $display("PASS: function workReqHasComp exists");
                step <= 78;
            end
            78: begin
                $display("PASS: function workReqHasSwap exists");
                step <= 79;
            end
            79: begin
                $display("PASS: function isSendWorkReq exists");
                step <= 80;
            end
            80: begin
                $display("PASS: function isReadWorkReq exists");
                step <= 81;
            end
            81: begin
                $display("PASS: function isReadRespWorkReq exists");
                step <= 82;
            end
            82: begin
                $display("PASS: function isAtomicWorkReq exists");
                step <= 83;
            end
            83: begin
                $display("PASS: function isReadOrAtomicWorkReq exists");
                step <= 84;
            end
            84: begin
                $display("PASS: function workReqNeedRecvReq exists");
                step <= 85;
            end
            85: begin
                $display("PASS: function workReqHasImmDt exists");
                step <= 86;
            end
            86: begin
                $display("PASS: function workReqHasInv exists");
                step <= 87;
            end
            87: begin
                $display("PASS: function workReqOpCode2WorkCompOpCode4SQ exists");
                step <= 88;
            end
            88: begin
                $display("PASS: function genErrWorkCompStatusFromAethSQ exists");
                step <= 89;
            end
            89: begin
                $display("PASS: function rdmaOpCode2WorkCompOpCode4RQ exists");
                step <= 90;
            end
            90: begin
                $display("PASS: function rdmaOpCode2WorkCompFlagsRQ exists");
                step <= 91;
            end
            91: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
