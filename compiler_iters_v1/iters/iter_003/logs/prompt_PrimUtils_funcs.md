BSV syntax:
- typedef VALUE NAME; — numeric constant
- typedef Bit#(W) NAME; — bit vector alias
- typedef enum {A=3'h0,B=3'h1} T deriving(Bits,Eq,FShow);
- typedef struct { T1 f; T2 g; } S deriving(Bits,FShow);
- SizeOf#(T); TDiv#(a,b); TExp#(n); TAdd#(a,b); TMul#(a,b)
- import Reserved :: *; for ReservedZero#(n)
- function RTYPE NAME(ARGS); ... endfunction
- interface IFC; method T m(args); endinterface
- module mkM(IFC); ... endmodule
- Reg#(T) r <- mkReg(v); FIFOF#(T) f <- mkFIFOF;


Generate BSV functions for: PrimUtils

Types already defined (import them): PrimUtils

function Bool isZero(Bit#(nSz) bits);
  // Returns True if all bits are zero. Uses reduction OR (|bits), then logical NOT. Implementation: Bool ret = unpack(|bits); return !ret;


function Bool isZeroR(Bit#(nSz) bits);
  // Recursive zero check using divide-and-conquer. Splits bits in half, recursively checks each half. provisos: NumAlias#(TDiv#(nSz, 2), halfSz)


function Bool isZeroByteEn(Bit#(nSz) byteEn);
  // Checks if byte enable is all zeros. Combines MSB and LSB parts before checking.


function Bool isLessOrEqOne(Bit#(nSz) bits);
  // Returns True if the value is 0 or 1. Shifts right by 1 and checks if zero.


function Bool isOne(Bit#(nSz) bits);
  // Returns True exactly when value is 1. Uses isLessOrEqOne AND checks lsb is 1.


function Bool isAllOnesR(Bit#(nSz) bits);
  // Recursive all-ones check. provisos: NumAlias#(TDiv#(nSz, 2), halfSz)


function Bool isLargerThanOne(Bit#(nSz) bits);
  // Returns True if value > 1. Checks bits>>1 is non-zero.


function Tuple2#(Bool, Bool) isZero4LargeBits(Bit#(nSz) bits);
  // For 32-64 bit values. Returns (isHighPartZero, isLowPartZero).


function Bit#(nSz) zeroExtendLSB(Bit#(mSz) bits);
  // Zero-extend by appending 0 to LSB: { bits, 0 }. provisos: Add#(mSz, anysize, nSz)


function Bit#(TSub#(nSz, 1)) removeMSB(Bit#(nSz) bits);
  // Remove most significant bit. provisos: Add#(1, anysize, nSz)


function anytype dontCareValue();
  // Returns don't-care value (?). provisos: Bits#(anytype, tSz)


function anytype unwrapMaybe(Maybe#(anytype) maybe);
  // Unwrap Maybe: returns value if Valid, ? if Invalid. provisos: Bits#(anytype, tSz)


function anytype unwrapMaybeWithDefault(Maybe#(anytype) maybe, anytype defaultVal);
  // Unwrap Maybe with explicit default value. provisos: Bits#(anytype, nSz)


function anytype1 getTupleFirst(Tuple2#(anytype1, anytype2) tupleVal);
  // Return first element of 2-tuple using tpl_1

function anytype2 getTupleSecond(Tuple2#(anytype1, anytype2) tupleVal);
  // Return second element of 2-tuple using tpl_2

function Action immAssert(Bool condition, String assertName, Fmt assertFmtMsg);
  // Immediate assertion: prints position and message, calls $finish(1) on failure.


function Action immFail(String assertName, Fmt assertFmtMsg);
  // Always-fail assertion: prints position and message, calls $finish(1).


function PipeOut#(anytype) toPipeOut(FIFOF#(anytype) queue);
  // Convert FIFOF to PipeOut interface

function FlagsType#(enumType) enum2Flag(enumType inputVal);
  // Convert enum value to FlagsType. provisos: Bits#(enumType, tSz), Flags#(enumType)


function Bool containFlags(FlagsType#(enumType) flags1, FlagsType#(enumType) flags2);
  // Check if flags1 contains all bits of flags2. provisos: Bits#(enumType, tSz), Flags#(enumType)


function Bool containEnum(FlagsType#(enumType) flags, enumType enumVal);
  // Check if flags contain a specific enum value. provisos: Bits#(enumType, tSz), Flags#(enumType)


Output in ```bsv block. Include imports referencing existing types. Generate now: