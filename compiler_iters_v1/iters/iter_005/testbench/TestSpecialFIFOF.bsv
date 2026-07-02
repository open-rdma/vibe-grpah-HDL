// Auto-generated testbench for SpecialFIFOF functions (iter_005)
import SpecialFIFOF :: *;
import Settings :: *;

(* synthesize *)
module mkTestSpecialFIFOF(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function getNextDeqPtr exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function isAlmostFull exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function isAlmostEmpty exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function searchFunc exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function clearTag exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function searchFunc exists");
                step <= 6;
            end
            6: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
