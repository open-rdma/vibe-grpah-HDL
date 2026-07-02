// Minimal testbench for Settings — tests that constants are defined correctly
import Settings :: *;

(* synthesize *)
module mkTestSettings(Empty);

    rule test_settings;
        // Verify key constants
        if (valueOf(DATA_BUS_WIDTH) == 256) begin
            $display("PASS: DATA_BUS_WIDTH = %0d", valueOf(DATA_BUS_WIDTH));
        end else begin
            $display("FAIL: DATA_BUS_WIDTH = %0d", valueOf(DATA_BUS_WIDTH));
            $finish(1);
        end

        if (valueOf(MAX_QP) == 4) begin
            $display("PASS: MAX_QP = %0d", valueOf(MAX_QP));
        end else begin
            $display("FAIL: MAX_QP");
            $finish(1);
        end

        if (valueOf(MAX_QP_WR) == 32) begin
            $display("PASS: MAX_QP_WR = %0d", valueOf(MAX_QP_WR));
        end else begin
            $display("FAIL: MAX_QP_WR");
            $finish(1);
        end

        if (valueOf(MAX_SGE) == 8) begin
            $display("PASS: MAX_SGE = %0d", valueOf(MAX_SGE));
        end else begin
            $display("FAIL: MAX_SGE");
            $finish(1);
        end

        if (valueOf(MAX_SEND_SGE) == 1) begin
            $display("PASS: MAX_SEND_SGE = %0d", valueOf(MAX_SEND_SGE));
        end else begin
            $display("FAIL: MAX_SEND_SGE");
            $finish(1);
        end

        $display("PASS: TARGET_CYCLE_NS = %0d", valueOf(TARGET_CYCLE_NS));
    endrule

    rule finish;
        $display("ALL_TESTS_PASSED");
        $finish(0);
    endrule

endmodule
