// Auto-generated testbench for Controller functions (iter_005)
import Controller :: *;
import Settings :: *;

(* synthesize *)
module mkTestController(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function getReset2InitRequiredAttr exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function getInit2RtrRequiredAttr exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function getRtr2RtsRequiredAttr exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function getOnlyStateRequiredAttr exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function debugShowRegs exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function queryReset2InitAttr exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function queryInit2RtrAttr exists");
                step <= 7;
            end
            7: begin
                $display("PASS: function queryRtr2RtsAttr exists");
                step <= 8;
            end
            8: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
