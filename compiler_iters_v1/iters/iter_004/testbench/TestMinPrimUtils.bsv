// Minimal testbench for PrimUtils
import PrimUtils :: *;
import Settings :: *;

(* synthesize *)
module mkTestPrimUtils(Empty);

    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                Bit#(8) z = 0;
                Bit#(8) o = 1;
                Bit#(8) ff = 8'hFF;
                if (isZero(z) && !isZero(o) && !isZero(ff))
                    $display("PASS: isZero");
                else begin
                    $display("FAIL: isZero");
                    $finish(1);
                end
                step <= 1;
            end
            1: begin
                Bit#(8) a = 0;
                Bit#(8) b = 1;
                Bit#(8) c = 2;
                if (isLessOrEqOne(a) && isLessOrEqOne(b) && !isLessOrEqOne(c))
                    $display("PASS: isLessOrEqOne");
                else begin
                    $display("FAIL: isLessOrEqOne");
                    $finish(1);
                end
                step <= 2;
            end
            2: begin
                Bit#(8) a = 0;
                Bit#(8) b = 1;
                Bit#(8) c = 2;
                if (isOne(b) && !isOne(a) && !isOne(c))
                    $display("PASS: isOne");
                else begin
                    $display("FAIL: isOne");
                    $finish(1);
                end
                step <= 3;
            end
            3: begin
                Bit#(8) a = 0;
                Bit#(8) b = 1;
                Bit#(8) c = 2;
                if (isTwo(c) && !isTwo(b) && !isTwo(a))
                    $display("PASS: isTwo");
                else begin
                    $display("FAIL: isTwo");
                    $finish(1);
                end
                step <= 4;
            end
            4: begin
                Bit#(8) v0 = 0;
                Bit#(8) v1 = 1;
                Bit#(8) v2 = 2;
                if (isLargerThanOne(v2) && !isLargerThanOne(v0) && !isLargerThanOne(v1))
                    $display("PASS: isLargerThanOne");
                else begin
                    $display("FAIL: isLargerThanOne");
                    $finish(1);
                end
                step <= 5;
            end
            5: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule

endmodule
