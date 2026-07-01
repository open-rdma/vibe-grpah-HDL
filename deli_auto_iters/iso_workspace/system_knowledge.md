# Bluespec SystemVerilog Coding Conventions

## Standard Library Modules

### FIFOF (import FIFOF)
```bsv
FIFOF#(T) queue <- mkFIFOF;
// Methods: queue.enq(val), queue.deq(), queue.first, queue.clear(), queue.notEmpty, queue.notFull
```

### Reg (built-in)
```bsv
Reg#(T) reg <- mkReg(initVal);     // initialized register
Reg#(T) reg <- mkRegU;             // uninitialized register (dont-care init)
// Methods: reg._read, reg._write(val)
```

### PipeOut (import GetPut or built-in)
Method-based interface:
- method T first() — return current value without consuming
- method Action deq() — consume current value  
- method Bool notEmpty() — whether data is available

### toPipeOut (import PAClib or PrimUtils)
Converts a FIFOF#(T) to PipeOut#(T). Usage: `toPipeOut(fifoQueue)`

## Bit Manipulation Functions
- `truncate(wideValue)` — narrow a wide value by taking low bits
- `truncateLSB(wideValue)` — narrow by taking high bits, equivalent to `value >> N`
- `zeroExtend(narrowValue)` — widen by adding zero MSB
- `pack(value)` — convert any type to Bit representation
- `unpack(bits)` — convert Bit back to type

## Shift Operators
- `<<` — logical left shift
- `>>` — logical right shift
- `value << n` shifts left by n bits

## Rule Pragmas
- `(* no_implicit_conditions, fire_when_enabled *)` — rule fires whenever guard is true, no implicit FIFO conditions
- `(* fire_when_enabled *)` — rule fires when explicit guard is true, with implicit conditions

## Module Instantiation
```bsv
module mkModuleName#(parameters)(InterfaceName);
  // internal state
  // rules
  // interface methods
endmodule
```

## Interface Definition
```bsv
interface InterfaceName;
  interface SubInterface1 sub1;
  interface SubInterface2 sub2;
endinterface
```

## Key Numeric Constants (from Settings)
- DATA_BUS_WIDTH = 256
- DATA_BUS_BYTE_WIDTH = DATA_BUS_WIDTH / 8 = 32
- HEADER_MAX_FRAG_NUM = 2 (for 256-bit bus)
- HEADER_MAX_DATA_WIDTH = DATA_BUS_WIDTH * HEADER_MAX_FRAG_NUM = 512
- HEADER_MAX_BYTE_EN_WIDTH = DATA_BUS_BYTE_WIDTH * HEADER_MAX_FRAG_NUM = 64
- HEADER_MAX_BYTE_NUM_WIDTH = log2(HEADER_MAX_BYTE_EN_WIDTH + 1) = 7
- HEADER_FRAG_NUM_WIDTH = log2(HEADER_MAX_FRAG_NUM + 1) = 2
- DATA_BUS_BYTE_NUM_WIDTH = log2(DATA_BUS_BYTE_WIDTH) + 1 = 6
- DATA_BUS_BIT_NUM_WIDTH = log2(DATA_BUS_WIDTH) + 1 = 9

## Standard Bluespec Imports
```bsv
import FIFOF :: *;
import GetPut :: *;
```
