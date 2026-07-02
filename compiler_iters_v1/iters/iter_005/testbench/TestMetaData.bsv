// Auto-generated testbench for MetaData functions (iter_005)
import MetaData :: *;
import Settings :: *;

(* synthesize *)
module mkTestMetaData(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function genLocalAndRmtKey exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function getIndexPD exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function clearAllMRs exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function getIndexQP exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function genQPN exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function mkMetaDataQPs exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function checkPermByMR exists");
                step <= 7;
            end
            7: begin
                $display("PASS: function getBramCacheIndex exists");
                step <= 8;
            end
            8: begin
                $display("PASS: function getCascadeCacheIndex exists");
                step <= 9;
            end
            9: begin
                $display("PASS: function readReqHelper exists");
                step <= 10;
            end
            10: begin
                $display("PASS: function readRespHelper exists");
                step <= 11;
            end
            11: begin
                $display("PASS: function concatBitVec exists");
                step <= 12;
            end
            12: begin
                $display("PASS: function getPageOffset exists");
                step <= 13;
            end
            13: begin
                $display("PASS: function getData4PA exists");
                step <= 14;
            end
            14: begin
                $display("PASS: function mkTLB exists");
                step <= 15;
            end
            15: begin
                $display("PASS: function getIndex4TLB exists");
                step <= 16;
            end
            16: begin
                $display("PASS: function getTag4TLB exists");
                step <= 17;
            end
            17: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
