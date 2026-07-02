#!/bin/bash
# Quick compile test for all generated BSV modules
# Records FPC (First-Pass Compilation) results

BSC=/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin/bsc
GEN_DIR=/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/generated
BUILD_BASE=/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/build
BLUE_SRC=/data/mmh/vibe-grpah-HDL/blue-rdma/src
RESULTS=/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/logs/compile_results.txt

mkdir -p $(dirname $RESULTS)
echo "=== Iteration 001 Compile Results ===" > $RESULTS
echo "Time: $(date -Iseconds)" >> $RESULTS
echo "" >> $RESULTS

MODULES=(
    "Settings"
    "Headers"
    "PrimUtils"
    "DataTypes"
    "Utils"
    "SpecialFIFOF"
    "Arbitration"
    "WorkCompGen"
    "ExtractAndPrependPipeOut"
    "DupReadAtomicCache"
    "InputPktHandle"
    "SendQ"
    "ReqGenSQ"
    "QueuePair"
    "RetryHandleSQ"
    "RespHandleSQ"
    "PayloadConAndGen"
    "PayloadGen"
    "ReqHandleRQ"
    "MetaData"
    "Controller"
    "TransportLayer"
)

PASS=0
FAIL=0
TOTAL=0

for MOD in "${MODULES[@]}"; do
    BSV_FILE="$GEN_DIR/${MOD}.bsv"
    BUILD_DIR="$BUILD_BASE/${MOD}"

    if [ ! -f "$BSV_FILE" ]; then
        echo "$MOD: SKIP (no BSV file)" | tee -a $RESULTS
        continue
    fi

    TOTAL=$((TOTAL + 1))
    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR"

    # Compile with original source path for imports
    OUTPUT=$($BSC -elab -sim -u \
        -p "+:$BLUE_SRC" \
        -p "+:$GEN_DIR" \
        -bdir "$BUILD_DIR" \
        -info-dir "$BUILD_DIR" \
        -simdir "$BUILD_DIR" \
        -check-assert \
        -steps 6000000 \
        +RTS -K4095M -RTS \
        "$BSV_FILE" 2>&1)
    EXIT_CODE=$?

    if [ $EXIT_CODE -eq 0 ] && ! echo "$OUTPUT" | grep -q "^Error"; then
        echo "$MOD: PASS" | tee -a $RESULTS
        PASS=$((PASS + 1))
    else
        # Extract first error
        FIRST_ERR=$(echo "$OUTPUT" | grep "^Error" | head -1 | cut -c1-200)
        echo "$MOD: FAIL - $FIRST_ERR" | tee -a $RESULTS
        FAIL=$((FAIL + 1))
    fi
done

echo "" | tee -a $RESULTS
echo "=== Summary: $PASS/$TOTAL passed (FPC = $(echo "scale=2; $PASS / $TOTAL" | bc)) ===" | tee -a $RESULTS

# Also save as JSON
JSON_FILE=/data/mmh/vibe-grpah-HDL/compiler_iters_v1/iters/iter_001/logs/compile_results.json
echo "{" > $JSON_FILE
echo "  \"iteration\": \"iter_001\"," >> $JSON_FILE
echo "  \"timestamp\": \"$(date -Iseconds)\"," >> $JSON_FILE
echo "  \"total_modules\": $TOTAL," >> $JSON_FILE
echo "  \"passed\": $PASS," >> $JSON_FILE
echo "  \"failed\": $FAIL," >> $JSON_FILE
echo "  \"fpc_rate\": $(echo "scale=4; $PASS / $TOTAL" | bc)" >> $JSON_FILE
echo "}" >> $JSON_FILE
