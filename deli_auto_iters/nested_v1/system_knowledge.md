# Bluespec SystemVerilog Coding Conventions (Project-Level Knowledge)

## Module / Interface Syntax

```bsv
interface MyInterface#(numeric type n, type t);
    method Action myMethod(t val);
    method t _read();
endinterface

module mkMyModule#(parameterType param)(MyInterface#(n, t)) provisos(
    Bits#(t, tSz),          // t must have Bits instance
    Add#(1, _, n)           // n >= 1
);
    // internal state...
endmodule
```

## Standard Library Usage

### FIFOF (import FIFOF::*)
```
FIFOF#(T) queue <- mkFIFOF;
// Methods: queue.enq(val), queue.deq(), queue.first, queue.clear(), queue.notEmpty, queue.notFull
```

### Reg (import Reg::* or built-in)
```
Reg#(T) reg <- mkReg(initVal);  // initialized
Reg#(T) reg <- mkRegU;          // uninitialized
```

### PipeOut (import PAClib::*)
```
// Interface: T first(), Action deq(), Bool notEmpty()
```

### PrimUtils (import PrimUtils::*)
```
// CReg: Reg#(T) name[n] <- mkCReg(n, initVal)  — concurrent register access
// toPipeOut: converts FIFOF#(T) to PipeOut#(T)
```

### Vector (import Vector::*)
```
Vector#(n, T) vec <- replicateM(mkSomething);  // create n copies
map(func, vec);                                 // apply function element-wise
vec[i]                                           // element access (i is Integer)
```

## Function Definitions

```bsv
function RetType funcName(ArgType arg);
    // local variables with let
    let result = some_expression;
    return result;
endfunction
```

## Numeric Type Constraints

- `Add#(1, _, n)` — n must be at least 1
- `Add#(1, _, TLog#(n))` — n must be at least 2 (log2(n) >= 1)
- `NumAlias#(TLog#(n), logSz)` — create alias for log2(n)

## Package Structure

```bsv
package PackageName;

import SomeLib::*;

// interfaces, modules, functions...

endpackage
```

## IMPORTANT: Standing Packages Available

The following packages are always available when generating BSV for blue-rdma projects:
- Standard: FIFOF, GetPut, Vector, Reg( built-in)
- blue-rdma: PAClib, PrimUtils (provides CReg, mkCReg, toPipeOut)

All generated modules are self-contained, using only basic types (Bit#(N), Bool, Maybe).
No external blue-rdma type dependencies.
