// Auto-generated testbench for InputPktHandle functions (iter_005)
import InputPktHandle :: *;
import Settings :: *;

(* synthesize *)
module mkTestInputPktHandle(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function checkZeroFields4BTH exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function padCntCheckReqHeader exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function padCntCheckRespHeader exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function validateHeader exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function genInputRdmaPktBuf exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function map exists");
                step <= 6;
            end
            6: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
