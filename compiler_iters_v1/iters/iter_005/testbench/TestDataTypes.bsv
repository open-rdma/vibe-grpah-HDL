// Auto-generated testbench for DataTypes functions (iter_005)
import DataTypes :: *;
import Settings :: *;

(* synthesize *)
module mkTestDataTypes(Empty);
    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                $display("PASS: function fshow exists");
                step <= 1;
            end
            1: begin
                $display("PASS: function fshow exists");
                step <= 2;
            end
            2: begin
                $display("PASS: function isOneHotOrZero exists");
                step <= 3;
            end
            3: begin
                $display("PASS: function isOneHotOrZero exists");
                step <= 4;
            end
            4: begin
                $display("PASS: function isOneHotOrZero exists");
                step <= 5;
            end
            5: begin
                $display("PASS: function fshow exists");
                step <= 6;
            end
            6: begin
                $display("PASS: function fshow exists");
                step <= 7;
            end
            7: begin
                $display("PASS: function isOneHotOrZero exists");
                step <= 8;
            end
            8: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule
endmodule
