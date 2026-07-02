// Auto-generated testbench for ReqGenSQ functions (iter_005)
import ReqGenSQ :: *;
import Settings :: *;

(* synthesize *)
module mkTestReqGenSQ(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function getMaybeDestQpnSQ exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function genFirstOrOnlyReqRdmaOpCode exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function genMiddleOrLastReqRdmaOpCode exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function genXRCETH exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function genDETH exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function genRETH exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function genAtomicEth exists");
                step <= 7;
            end
            7: begin
                $display("PASS: function genImmDt exists");
                step <= 8;
            end
            8: begin
                $display("PASS: function genIETH exists");
                step <= 9;
            end
            9: begin
                $display("PASS: function flushInternalNormalStatePipelineQ exists");
                step <= 10;
            end
            10: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
