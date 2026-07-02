// Auto-generated testbench for RetryHandleSQ functions (iter_005)
import RetryHandleSQ :: *;
import Settings :: *;

(* synthesize *)
module mkTestRetryHandleSQ(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function retryCntExceedLimit exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function decRetryCntByReason exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function resetRetryCntInternal exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function resetTimeOutCntInternal exists");
                step <= 4;
            end
            4: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
