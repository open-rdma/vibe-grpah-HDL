# Bluespec SystemVerilog Language Template

This is a SHARED template for all BSV projects. It describes BSV language constructs and patterns. Project-specific knowledge (available packages, project constraints) goes in project-level files.

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

## Function Definitions

```bsv
function RetType funcName(ArgType arg);
    // local variables with let
    let result = some_expression;
    return result;
endfunction
```

Functions are combinational (no state, no clock). Use for pure computation. For stateful operations, use modules and methods.

## Package Structure

```bsv
package PackageName;

import SomePackage::*;    // only import what you USE

// interface definitions
// module definitions
// function definitions

endpackage
```

## Numeric Type Constraints (Provisos)

### Common patterns
- `Add#(1, _, n)` — n must be at least 1
- `Add#(m, k, n)` — n = m + k (e.g., two halves make a whole)
- `NumAlias#(TLog#(n), logSz)` — create alias for log2(n)
- `Add#(TLog#(n), 1, TLog#(TAdd#(1, n)))` — n must be a power of 2

### Bit manipulation provisos
When splitting/joining bit vectors:
- `truncate(Bit#(N))` → `Bit#(M)` requires `Add#(M, _, N)`
- `zeroExtend(Bit#(M))` → `Bit#(N)` requires `Add#(M, _, N)`
- `{Bit#(A), Bit#(B)}` → `Bit#(N)` requires `Add#(A, B, N)`
- `truncateLSB(Bit#(N))` → `Bit#(M)` requires `Add#(M, _, N)`

### Template for modules with child instances
When your module instantiates a child that has its own provisos (listed in the child's interface contract), you MUST add those provisos with your type parameters substituted. See the child interface section in your prompt for the full list of required derived provisos.

## import Decision Table

Import ONLY packages your module actually uses:

| Import | When to use |
|--------|-------------|
| `FIFOF::*` | Module instantiates FIFOF#(T) |
| `GetPut::*` | Module uses Get/Put typeclasses |
| `Vector::*` | Module uses Vector#(n, T), replicateM, or vector operations |
| `PAClib::*` | Module uses PipeOut, mkFork, or PAClib pipeline primitives |
| `PrimUtils::*` | Module uses CReg, toPipeOut, or other PrimUtils utilities |

**Built-in types (no import needed):** `Bit#(n)`, `Bool`, `Integer`, `Reg#(T)`, `Maybe#(T)`, `Tuple2#(A,B)`

If your module is purely combinational (no registers, no FIFOs), you likely need ZERO imports beyond what child modules provide.

## ActionValue Method Pattern

```bsv
method ActionValue#(RetType) methodName(ArgType arg);
    actionvalue
        // compute result
        // update state with <=
        return result;
    endactionvalue
endmethod
```

## Value Method Pattern (Combinational)

```bsv
method RetType methodName(ArgType arg);
    return expression;
endmethod
```
