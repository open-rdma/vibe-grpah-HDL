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

## Bit Manipulation
- `{ bitsA, bitsB }`: concatenates bit vectors (bitsA at top/MSB, bitsB at bottom/LSB)
- `truncate(value)`: extracts LSBs to fit target type width
- `>> N`: logical right shift by N positions (data moves toward LSBs)
- `<< N`: logical left shift by N positions (data moves toward MSBs)

## Utility Functions (import PrimUtils)
- **zeroExtend(value)**: Zero-extends a smaller bit value to a larger bit type (zeros added at MSB side)
- **isZero(value)**: Returns Bool, true if value equals zero
- **isZeroByteEn(byteEn)**: Returns Bool, true if all bits in ByteEn are zero
- **isOne(value)**: Returns Bool, true if value equals 1
- **truncate(value)**: Extracts LSBs to fit target type width. Sometimes needs explicit type context; if BSC reports type ambiguity, write: `truncate(expr)` where the result is assigned to a variable with declared type.
- **immAssert**: CRITICAL — takes exactly 3 arguments: `immAssert(condition, "assertion_name_string", $format("format string", args))`. The second argument is a String literal (the assertion name). The third argument is a Fmt value from $format. Never omit the name string.

## Utility Functions (import Utils)
- **calcFragBitNumAndByteNum(ByteEnBitNum fragValidByteNum)**: 
  Returns `Tuple3#(BusBitNum, ByteEnBitNum, BusBitNum)` with:
  - tpl_1: fragValidBitNum = zeroExtend(fragValidByteNum) << 3 (multiply by 8, bytes to bits)
  - tpl_2: fragInvalidByteNum = valueOf(DATA_BUS_BYTE_WIDTH) (32) - fragValidByteNum
  - tpl_3: fragInvalidBitNum = zeroExtend(fragInvalidByteNum) << 3
  Destructure: `let { validBitNum, invalidByteNum, invalidBitNum } = calcFragBitNumAndByteNum(byteNum);`

## Enum Definition Syntax
```
typedef enum {
    STATE_A,
    STATE_B,
    STATE_C
} MyState deriving(Bits, Eq, FShow);
```

## Required Imports for this module
- FIFOF (mkFIFOF)
- GetPut (PipeOut)
- PAClib (toPipeOut)
- PrimUtils (zeroExtend, isZero, isZeroByteEn, isOne, truncate, immAssert)
- Utils (calcFragBitNumAndByteNum)
- DataTypes (DataStream, HeaderMetaData, DataStreamPipeOut, etc.)
- Settings (DATA_BUS_WIDTH, DATA_BUS_BYTE_WIDTH, DATA_BUS_BIT_NUM_WIDTH, DATA_BUS_BYTE_NUM_WIDTH)
