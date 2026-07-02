Generate the Bluespec SystemVerilog file for: PrimUtils
Module type: typedef_and_functions

## BSV Quick Reference
- typedef VALUE NAME; — numeric constant (e.g., `typedef 32 X;` or `typedef TAdd#(a,b) Y;`)
- typedef Bit#(W) NAME; — bit vector type alias
- typedef enum {A=3'h0, B=3'h1} T deriving(Bits,Eq,FShow); — enumeration
- typedef struct { T1 f1; T2 f2; } S deriving(Bits,FShow); — struct
- SizeOf#(T) — bit width; TDiv#(a,b) — division; TExp#(n) — 2^n
- valueOf(X) — numeric value of typedef
- ReservedZero#(n) — n-bit reserved field (requires `import Reserved :: *;`)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method RTYPE NAME(ARGS); endinterface
- module mkNAME(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;
- Reg#(T) r[N] <- mkCReg(N, v);
- Bool, Bit#(n), Maybe#(T) with tagged Valid v / tagged Invalid
- case (expr) matches tagged Valid .v: ... endcase
- pack(v) / unpack(b) convert to/from bits


## Requirements
Collection of primitive utility functions and types including: - Bit manipulation: isZero, isOne, isAllOnes, isLessOrEqOne, isLargerThanOne - Recursive bit check variants: isZeroR, isOneR, isAllOnesR - Byte enable checks: isZeroByteEn - Tuple accessors: getTupleFirst through getTupleSixth - Assertions: immAssert (compile-time), immFail - PipeOut conversion: toPipeOut - Generic FlagsType with FShow instance - CountCF: conflict-free credit counter module (CF = Conflict Free)


## Type Definitions (output EXACTLY these)
typedef 2 TWO; // TWO
typedef 4 FOUR; // FOUR

## Structs
typedef struct {
    Bit#(SizeOf#(enumType)) flags; // 
} FlagsType deriving(Bits, Bitwise, Eq);
typedef SizeOf#(FlagsType) FlagsType_WIDTH;
typedef TDiv#(FlagsType_WIDTH, 8) FlagsType_BYTE_WIDTH;

## Functions

function Bool isZero(Bit#(nSz) bits);
// Returns True if all bits are zero. Uses reduction OR (|bits), then logical NOT. Implementation: Bool ret = unpack(|bits); return !ret;

// Implement using BSV syntax. end with endfunction

function Bool isZeroR(Bit#(nSz) bits);
// Recursive zero check using divide-and-conquer. Splits bits in half, recursively checks each half. provisos: NumAlias#(TDiv#(nSz, 2), halfSz)

// Implement using BSV syntax. end with endfunction

function Bool isZeroByteEn(Bit#(nSz) byteEn);
// Checks if byte enable is all zeros. Combines MSB and LSB parts before checking.

// Implement using BSV syntax. end with endfunction

function Bool isLessOrEqOne(Bit#(nSz) bits);
// Returns True if the value is 0 or 1. Shifts right by 1 and checks if zero.

// Implement using BSV syntax. end with endfunction

function Bool isOne(Bit#(nSz) bits);
// Returns True exactly when value is 1. Uses isLessOrEqOne AND checks lsb is 1.

// Implement using BSV syntax. end with endfunction

function Bool isAllOnesR(Bit#(nSz) bits);
// Recursive all-ones check. provisos: NumAlias#(TDiv#(nSz, 2), halfSz)

// Implement using BSV syntax. end with endfunction

function Bool isLargerThanOne(Bit#(nSz) bits);
// Returns True if value > 1. Checks bits>>1 is non-zero.

// Implement using BSV syntax. end with endfunction

function Tuple2#(Bool, Bool) isZero4LargeBits(Bit#(nSz) bits);
// For 32-64 bit values. Returns (isHighPartZero, isLowPartZero).

// Implement using BSV syntax. end with endfunction

function Bit#(nSz) zeroExtendLSB(Bit#(mSz) bits);
// Zero-extend by appending 0 to LSB: { bits, 0 }. provisos: Add#(mSz, anysize, nSz)

// Implement using BSV syntax. end with endfunction

function Bit#(TSub#(nSz, 1)) removeMSB(Bit#(nSz) bits);
// Remove most significant bit. provisos: Add#(1, anysize, nSz)

// Implement using BSV syntax. end with endfunction

function anytype dontCareValue();
// Returns don't-care value (?). provisos: Bits#(anytype, tSz)

// Implement using BSV syntax. end with endfunction

function anytype unwrapMaybe(Maybe#(anytype) maybe);
// Unwrap Maybe: returns value if Valid, ? if Invalid. provisos: Bits#(anytype, tSz)

// Implement using BSV syntax. end with endfunction

function anytype unwrapMaybeWithDefault(Maybe#(anytype) maybe, anytype defaultVal);
// Unwrap Maybe with explicit default value. provisos: Bits#(anytype, nSz)

// Implement using BSV syntax. end with endfunction

function anytype1 getTupleFirst(Tuple2#(anytype1, anytype2) tupleVal);
// Return first element of 2-tuple using tpl_1
// Implement using BSV syntax. end with endfunction

function anytype2 getTupleSecond(Tuple2#(anytype1, anytype2) tupleVal);
// Return second element of 2-tuple using tpl_2
// Implement using BSV syntax. end with endfunction

function Action immAssert(Bool condition, String assertName, Fmt assertFmtMsg);
// Immediate assertion: prints position and message, calls $finish(1) on failure.

// Implement using BSV syntax. end with endfunction

function Action immFail(String assertName, Fmt assertFmtMsg);
// Always-fail assertion: prints position and message, calls $finish(1).

// Implement using BSV syntax. end with endfunction

function PipeOut#(anytype) toPipeOut(FIFOF#(anytype) queue);
// Convert FIFOF to PipeOut interface
// Implement using BSV syntax. end with endfunction

function FlagsType#(enumType) enum2Flag(enumType inputVal);
// Convert enum value to FlagsType. provisos: Bits#(enumType, tSz), Flags#(enumType)

// Implement using BSV syntax. end with endfunction

function Bool containFlags(FlagsType#(enumType) flags1, FlagsType#(enumType) flags2);
// Check if flags1 contains all bits of flags2. provisos: Bits#(enumType, tSz), Flags#(enumType)

// Implement using BSV syntax. end with endfunction

function Bool containEnum(FlagsType#(enumType) flags, enumType enumVal);
// Check if flags contain a specific enum value. provisos: Bits#(enumType, tSz), Flags#(enumType)

// Implement using BSV syntax. end with endfunction

## Module: mkCountCF
Interface: CountCF
  method Action incrOne();
  method Action decrOne();
  method Action _write(anytype write_val);
  method anytype _read();

## Implementation
CountCF is a conflict-free counter module. It supports concurrent increment, decrement, and write operations without scheduling conflicts.
Implementation approach: 1. Use mkCReg(2, ...) for all control state (writeReg, incrReg, decrReg) 2. Use mkFIFOF for incrQ and decrQ to buffer requests 3. Four rules with proper scheduling attributes:
   - write: (* no_implicit_conditions, fire_when_enabled *) - priority over incr/decr
   - increment: enqueues incr request, uses incrQ
   - decrement: enqueues decr request, uses decrQ
   - incrAndDecr: applies pending incr/decr to cntReg

The Module is parameterized by anytype with Arith# and Bits# provisos.


State elements:
  cntReg: Reg#(anytype) = resetVal
  incrQ: FIFOF#(Bool) = ?
  decrQ: FIFOF#(Bool) = ?
  writeReg: Reg#(Maybe#(anytype))[2] = mkCReg(2, tagged Invalid)
  incrReg: Reg#(Bool)[2] = mkCReg(2, False)
  decrReg: Reg#(Bool)[2] = mkCReg(2, False)

Rules:
  write: When writeReg[1] has valid value, write it to cntReg and clear all pending incr/decr
  increment: Dequeue from incrQ and set incrReg[0]
  decrement: Dequeue from decrQ and set decrReg[0]
  incrAndDecr: Apply pending incr/decr to cntReg based on incrReg[1] and decrReg[1] flags


Output ONLY the valid BSV code in a ```bsv block. No explanations.
Include all needed import statements.
The code must compile with: bsc -elab -sim PrimUtils.bsv

Generate BSV now: