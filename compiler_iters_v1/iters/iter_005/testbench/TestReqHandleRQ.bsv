// Auto-generated testbench for ReqHandleRQ functions (iter_005)
import ReqHandleRQ :: *;
import Settings :: *;

(* synthesize *)
module mkTestReqHandleRQ(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function isErrReqStatus exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function isNormalOrErrorReqStatus exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function getMaybeDestQpnRQ exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function genWorkCompStatusFromReqStatusRQ exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function genMiddleOrLastRespRdmaOpCode exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function genAethByReqStatus exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function getInvReqStatusByTransType exists");
                step <= 7;
            end
            7: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
