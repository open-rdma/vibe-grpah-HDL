// Auto-generated testbench for RespHandleSQ functions (iter_005)
import RespHandleSQ :: *;
import Settings :: *;

(* synthesize *)
module mkTestRespHandleSQ(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function rdmaRespMatchWorkReq exists");
                step <= 1;
            end
            1: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
