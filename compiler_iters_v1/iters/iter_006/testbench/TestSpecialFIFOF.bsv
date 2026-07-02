// Meaningful testbench for SpecialFIFOF — tests ScanFIFOF basic operations
import Cntrs :: *;
import FIFOF :: *;
import PAClib :: *;
import Vector :: *;

import SpecialFIFOF :: *;
import Settings :: *;
import PrimUtils :: *;

typedef Bit#(32) TestData;
typedef 4 QSize;

(* synthesize *)
module mkTestSpecialFIFOF(Empty);
    ScanFIFOF#(QSize, TestData) scanQ <- mkScanFIFOF;

    Reg#(Bit#(8)) step <- mkReg(0);
    Reg#(TestData) testVal <- mkReg(0);

    rule test_enqueue(step == 0);
        if (scanQ.fifof.notFull) begin
            scanQ.fifof.enq(32'hDEADBEEF);
            step <= 1;
        end
    endrule

    rule test_dequeue(step == 1);
        let val = scanQ.fifof.first;
        scanQ.fifof.deq;
        if (val == 32'hDEADBEEF) begin
            $display("PASS: ScanFIFOF enqueue/dequeue");
            step <= 2;
        end else begin
            $display("FAIL: ScanFIFOF enqueue/dequeue (got %h, expected DEADBEEF)", val);
            $finish(1);
        end
    endrule

    rule test_size(step == 2);
        let sz = scanQ.size;
        if (sz == 0) begin
            $display("PASS: ScanFIFOF size after dequeue");
            step <= 3;
        end else begin
            $display("FAIL: ScanFIFOF size=%0d, expected 0", sz);
            $finish(1);
        end
    endrule

    rule test_empty(step == 3);
        let empty = scanQ.fifof.notEmpty;
        if (!empty) begin
            $display("PASS: ScanFIFOF isEmpty");
        end else begin
            $display("FAIL: ScanFIFOF isEmpty (got %s)", empty ? "True" : "False");
            $finish(1);
        end
        step <= 4;
    endrule

    rule finish_test(step == 4);
        $display("ALL_TESTS_PASSED");
        $finish(0);
    endrule
endmodule
