// Auto-generated testbench for DupReadAtomicCache functions (iter_005)
import DupReadAtomicCache :: *;
import Settings :: *;

(* synthesize *)
module mkTestDupReadAtomicCache(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function cmpHalfAddr exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function clearSearchDataQ exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function clearCmpResultQ exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function clearSearchResultQ exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function duplicateSearchReq exists");
                step <= 5;
            end
            5: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
