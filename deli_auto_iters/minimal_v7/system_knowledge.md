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
