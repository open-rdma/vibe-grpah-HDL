# Task Spec: RTL Knowledge Representation Validation

## Goal
Experimentally validate whether the "multi-level nested graph structure + natural language description" knowledge representation approach can guide an LLM to generate correct Bluespec SystemVerilog RTL code that is functionally equivalent to the original hand-written code.

## Success Criteria
1. For at least one simple leaf module: generate code from knowledge representation that passes the original testbench
2. For at least one composite module (with submodules): same as above
3. Identify what information cannot be adequately expressed in the current knowledge format
4. Propose improvements to the knowledge representation scheme

## Methodology
1. Extract knowledge from original BSV source code into graph+natural-language representation
2. Have an independent verification agent generate new BSV code from that knowledge only
3. Test generated code against original testbench using run_one.sh
4. If pass: mark success, move to next complexity level
5. If fail: analyze root cause, refine knowledge representation, retry

## Module Complexity Hierarchy (from blue-rdma/)
### Level 0: Pure definitions (no modules to generate)
- Settings.bsv, Headers.bsv, DataTypes.bsv

### Level 1: Simple leaf modules (FSM only, FIFOs/Regs, no submodules)
- mkHeader2DataStream (ExtractAndPrependPipeOut.bsv) - header → data stream fragments
- mkDataStream2Header (ExtractAndPrependPipeOut.bsv) - data stream → header
- mkCountCF (PrimUtils.bsv) - concurrent counter

### Level 2: Medium leaf modules (complex FSM, FIFOs/Regs only)
- mkPrependHeader2PipeOut (ExtractAndPrependPipeOut.bsv)
- mkExtractHeaderFromDataStreamPipeOut (ExtractAndPrependPipeOut.bsv)
- mkScanFIFOF (SpecialFIFOF.bsv)

### Level 3: Composite modules (instantiates other modules)
- mkCombineHeaderAndPayload → uses mkHeader2DataStream + mkPrependHeader2PipeOut
- mkDupReadAtomicCache → uses mkCacheFIFO
- mkServerArbiter (Arbitration.bsv)

### Level 4: Complex multi-level modules
- Controller.bsv, QueuePair.bsv, InputPktHandle.bsv

## Starting Point
Begin with mkHeader2DataStream (Level 1, ~110 lines, single FSM with 2 states).
Test: mkTestHeaderAndDataStreamConversion (uses mkDataStream2Header → mkHeader2DataStream round-trip)
