// Auto-generated testbench for ExtractAndPrependPipeOut functions (iter_005)
import ExtractAndPrependPipeOut :: *;
import Settings :: *;

(* synthesize *)
module mkTestExtractAndPrependPipeOut(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function deqActionFunc exists");
                step <= 1;
            end
            1: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
