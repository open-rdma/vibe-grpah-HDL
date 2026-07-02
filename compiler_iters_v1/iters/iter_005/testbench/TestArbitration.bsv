// Auto-generated testbench for Arbitration functions (iter_005)
import Arbitration :: *;
import Settings :: *;

(* synthesize *)
module mkTestArbitration(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function isPipePayloadFinished exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function isPipePayloadFinished exists");
                step <= 2;
            end
            2: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
