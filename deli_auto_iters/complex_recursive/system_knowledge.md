# Bluespec SystemVerilog Coding Conventions

## Standard Library

### FIFOF (import FIFOF)
```
FIFOF#(T) queue <- mkFIFOF;
// Methods: queue.enq(val), queue.deq(), queue.first, queue.clear(), queue.notEmpty, queue.notFull
```

### Reg (built-in)
```
Reg#(T) reg <- mkReg(initVal);  // initialized register
Reg#(T) reg <- mkRegU;          // uninitialized register
```

### PipeOut (import GetPut)
```
// Methods: T first(), Action deq(), Bool notEmpty()
```

### toPipeOut (import PAClib)
Converts FIFOF#(T) to PipeOut#(T). Usage: `toPipeOut(fifoQueue)`

### toGet (import PAClib)
Converts PipeOut#(T) to Get#(T). Usage: `toGet(pipeOut)`

### toPut (import PAClib)
Converts FIFOF#(T) to Put#(T). Usage: `toPut(fifoQueue)`

### mkConnectionWithAction (import PAClib)
Connects a Get source to a Put sink, with an action callback per transfer.
```
mkConnectionWithAction(toGet(sourcePipeOut), toPut(sinkFIFO), actionFunc);
```
The actionFunc receives the data being transferred and can perform side effects.

## Function Definition Syntax
```
function Action actionFunc(DataType param);
    action
        // imperative actions
    endaction
endfunction
```

## Utility Functions (import PrimUtils)
- **zeroExtend(value)**: Zero-extends a smaller bit value to a larger bit type. Usage: `zeroExtend(smallValue)`
- **zeroExtendLSB(value)**: Zero-extends a bit value on the LSB side. Usage: `zeroExtendLSB(smallValue)`
- **truncate(value)**: Extracts the LSBs of the value to fit the target type width. Usage: `truncate(largeValue)`
- **truncateLSB(value)**: Extracts the MSBs of the value to fit the target type width. Discards LSBs. Usage: `truncateLSB(largeValue)`
- **isZero(value)**: Returns Bool, true if value equals zero. Usage: `isZero(numericValue)`
- **immAssert(cond, name, message)**: Immediate assertion. Usage: `immAssert(condition, "assertion_name", $format("fmt", args))`

## Utility Functions (import Utils)
- **calcHeaderInvalidFragByteAndBitNum(HeaderFragNum headerValidFragNum)**: 
  Returns `Tuple2#(HeaderByteNum, HeaderBitNum)` with:
  - First element: `zeroExtend(headerInvalidFragNum) << valueOf(DATA_BUS_BYTE_NUM_WIDTH)` where `headerInvalidFragNum = valueOf(HEADER_MAX_FRAG_NUM) - headerValidFragNum`
  - Second element: `zeroExtend(headerInvalidFragNum) << valueOf(DATA_BUS_BIT_NUM_WIDTH)`
  Use `tpl_1(result)` to get first element, `tpl_2(result)` for second.
  Or destructure: `let { byteNum, bitNum } = calcHeaderInvalidFragByteAndBitNum(fragNum);`

- **genByteEn(ByteEnBitNum fragValidByteNum)**: 
  Returns a ByteEn (Bit#(32)) with the lowest `fragValidByteNum` bits set to 1. 
  Implementation: `reverseBits((1 << fragValidByteNum) - 1)`

## Module Parameters
Modules can take parameters that are NOT ports — they're compile-time or structural:
```
module mkModule#(ParamType param)(InterfaceType);
```

## Struct Field Access
```
structVal.fieldName
structVal.subStruct.fieldName  // nested access
```

## Struct Construction
```
MyStruct {
    field1: value1,
    field2: value2
}
```

## Bit Concatenation
```
{ highBits, lowBits }  // concatenates bit vectors
```

## Port Categories
- `clock`: Clock source
- `reset`: Reset signal  
- `data`: All other signals

## Required Imports for this module
- FIFOF (mkFIFOF)
- GetPut (PipeOut)
- PAClib (toPipeOut)
- PrimUtils (zeroExtend, truncate, truncateLSB, immAssert, isZero)
- Utils (calcHeaderInvalidFragByteAndBitNum, genByteEn)
- DataTypes (DataStream, HeaderRDMA, HeaderMetaData, DataStreamPipeOut)
- Headers (PSN)
- Settings (DATA_BUS_WIDTH, DATA_BUS_BYTE_WIDTH, HEADER_MAX_FRAG_NUM)

## Additional Utility Functions (import Utils)
- **calcFragBitNumAndByteNum(ByteEnBitNum lastFragValidByteNum)**:
  Returns `Tuple3#(BusBitNum, ByteEnBitNum, BusBitNum)` with:
  - First: `(fromInteger(valueOf(DATA_BUS_BYTE_WIDTH)) - zeroExtend(lastFragValidByteNum)) * fromInteger(valueOf(BYTE_WIDTH))`
  - Second: `fromInteger(valueOf(DATA_BUS_BYTE_WIDTH)) - zeroExtend(lastFragValidByteNum)`
  - Third: same as first
  Let {validBitNum, invalidByteNum, invalidBitNum} = result for destructure.

- **isAllOnesR(Bit#(n) value)**: Returns Bool true if value bitwise ANDs to all ones
- **isOne(Bit#(n) value)**: Returns Bool true if value equals 1
- **isZeroByteEn(ByteEn byteEn)**: Returns Bool true if byteEn has zero valid bytes

## Additional Types (import DataTypes)
- **BusBitNum**: Bit#(9). Number of bits in a bus width.
- **ByteEnBitNum**: Bit#(6). Number of valid bytes in a fragment.

## Pipeline Enum (local)
- **ExtractOrPrependHeaderStage**: enum { HEADER_META_DATA_POP, HEADER_OUTPUT, DATA_OUTPUT, EXTRA_LAST_FRAG_OUTPUT } deriving (Bits, Eq, FShow)

## Pipeline Interfaces (local)
- **HeaderDataStreamAndMetaDataPipeOut**: 
  - interface DataStreamPipeOut headerDataStream;
  - interface PipeOut#(HeaderMetaData) headerMetaData;
- **HeaderAndPayloadSeperateDataStreamPipeOut**:
  - interface DataStreamPipeOut header;
  - interface DataStreamPipeOut payload;

## Recursive Module Patterns
BSV supports recursive module instantiation, where a module calls itself with smaller parameters.

### mkBinaryTreeFork Pattern
Recursively forks 1 PipeOut to vSz identical outputs:
- Base case (vSz==2): duplicate each input to 2 FIFOs
- Recursive case (vSz>2): instantiate self with vSz/2, then duplicate each half output to 2 result FIFOs
- Uses clearAll Bool parameter to discard/clear all FIFOs
- Requires: vSz is power of 2 (provable via TLog)

### mkRecursiveSearch Pattern
Recursive tournament: reduces vSz Maybe inputs to 1 Maybe output:
- Base case (vSz==1): passthrough
- Recursive case: pair up inputs (idx, idx+1), prefer Valid over Invalid, enq to next layer, recurse with vSz/2
- Result: first Valid value wins, Invalid if all Invalid

## CacheFIFO Interface (from SpecialFIFOF)
```bsv
interface CacheIfc#(type anytype);
    method Action push(anytype pushVal);
    method Action clear();
endinterface

interface SearchIfc#(type anytype);
    method Action searchReq(anytype item2Search);
    method ActionValue#(Maybe#(anytype)) searchResp();
endinterface

interface CacheFIFO#(numeric type qSz, type anytype);
    interface CacheIfc#(anytype) cacheIfc;
    interface SearchIfc#(anytype) searchIfc;
endinterface
```
qSz must be a power of 2.

## Additional Types
- **PSN**: Bit#(24). Packet sequence number (from Headers).
- **PMTU**: Enum (IBV_MTU_256, IBV_MTU_512, IBV_MTU_1024, IBV_MTU_2048, IBV_MTU_4096) deriving (Bits, Eq)
- **RETH**: RDMA Extended Transport Header struct with fields: rkey (Bit#(32)), va (ADDR), dlen (Bit#(RDMA_MAX_LEN_WIDTH))
- **ADDR**: Bit#(64). Address type.
- **RdmaOpCode**: Enum of RDMA operation codes from Headers.
- **AtomicEth**: Struct with rkey, va, swap, comp fields.
- **AtomicAckEth**: Struct for atomic acknowledgment.
- **PKT_NUM_WIDTH**: Numeric type from Settings.
- **MAX_QP_RD_ATOM**: Numeric type from Settings (usually 4 or 8, must be power of 2).
- **TWO**: = 2 (numeric type from Settings).

## PMTU-dependent Functions
- **psnInRangeExclusive(PSN psn, PSN start, PSN end)**: Returns Bool. True if psn > start && psn < end (modulo 2^24 wrap-around).

## Pattern: Module with Function Arguments
```bsv
module mkModuleName#(
    function Type1 func1(ArgType1 arg),
    function Type2 func2(ArgType2 arg),
    function Type3 func3(ArgType3 arg)
)(InterfaceType);
```
Function arguments are passed without binding — they're pure functions used in rule bodies.

## CReg Pattern
CReg allows multiple rules to read/write the same register:
```bsv
Reg#(T) regName[n] <- mkCReg(n, initVal);
// regName[0] for method port, regName[1] for internal rules
```

## replicateM Pattern
```bsv
Vector#(N, Reg#(T)) vec <- replicateM(mkRegU);   // N uninit registers
Vector#(N, FIFOF#(T)) vec <- replicateM(mkFIFOF); // N FIFOs
```

## toPipeOut with Vector
```bsv
Vector#(N, PipeOut#(T)) pipeVec = map(toPipeOut, fifoVec);
```

## fromMaybe
```bsv
let val = fromMaybe(defaultVal, maybeVal);
// Extracts from Maybe; defaultVal used if Invalid (compile-time only)
```
