// Minimal testbench for Headers
import Headers :: *;
import Settings :: *;

(* synthesize *)
module mkTestHeaders(Empty);

    Reg#(Bit#(8)) step <- mkReg(0);

    rule do_tests;
        case (step)
            0: begin
                // Test opcode constants
                if (valueOf(RC_SEND_FIRST) == 0 && valueOf(RC_SEND_ONLY) == 4)
                    $display("PASS: opcode constants");
                else begin
                    $display("FAIL: opcode constants (RC_SEND_FIRST=%0d RC_SEND_ONLY=%0d)", valueOf(RC_SEND_FIRST), valueOf(RC_SEND_ONLY));
                    $finish(1);
                end
                step <= 1;
            end
            1: begin
                // Test TransType enum
                TransType t = TRANS_TYPE_RC;
                if (pack(t) == 3'h0)
                    $display("PASS: TransType");
                else begin
                    $display("FAIL: TransType");
                    $finish(1);
                end
                step <= 2;
            end
            2: begin
                // Test RdmaOpCode enum
                RdmaOpCode op = SEND_ONLY;
                if (pack(op) == 5'h04)
                    $display("PASS: RdmaOpCode");
                else begin
                    $display("FAIL: RdmaOpCode");
                    $finish(1);
                end
                step <= 3;
            end
            3: begin
                // Test RETH struct
                RETH reth = RETH{va: 64'hDEADBEEF, rkey: 32'hABCD, dlen: 1024};
                if (reth.dlen == 1024)
                    $display("PASS: RETH struct");
                else begin
                    $display("FAIL: RETH struct");
                    $finish(1);
                end
                step <= 4;
            end
            4: begin
                // Test calcHeaderLen
                Integer len1 = calcHeaderLenByTransTypeAndRdmaOpCode(TRANS_TYPE_RC, SEND_ONLY);
                if (len1 == 12)
                    $display("PASS: calcHeaderLen SEND_ONLY=%0d", len1);
                else begin
                    $display("FAIL: calcHeaderLen SEND_ONLY=%0d (expected 12)", len1);
                    $finish(1);
                end
                step <= 5;
            end
            5: begin
                Integer len2 = calcHeaderLenByTransTypeAndRdmaOpCode(TRANS_TYPE_RC, RDMA_WRITE_ONLY);
                if (len2 == 28)
                    $display("PASS: calcHeaderLen RDMA_WRITE_ONLY=%0d", len2);
                else begin
                    $display("FAIL: calcHeaderLen RDMA_WRITE_ONLY=%0d (expected 28)", len2);
                    $finish(1);
                end
                step <= 6;
            end
            6: begin
                // Test hasPayload
                if (rdmaOpCodeHasPayload(SEND_ONLY) && !rdmaOpCodeHasPayload(RDMA_READ_REQUEST))
                    $display("PASS: rdmaOpCodeHasPayload");
                else begin
                    $display("FAIL: rdmaOpCodeHasPayload");
                    $finish(1);
                end
                step <= 7;
            end
            7: begin
                $display("ALL_TESTS_PASSED");
                $finish(0);
            end
        endcase
    endrule

endmodule
