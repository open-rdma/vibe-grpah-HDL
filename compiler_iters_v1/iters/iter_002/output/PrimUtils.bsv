import FIFOF :: *;
import PAClib :: *;

// ============================================================================
// Constants
// ============================================================================

typedef 2 TWO;
typedef 4 FOUR;

// ============================================================================
// FlagsType struct
// ============================================================================

typedef struct {
   Bit#(SizeOf#(enumType)) flags;
} FlagsType#(type enumType) deriving (Bits, Bitwise, Eq);

instance FShow#(FlagsType#(enumType));
   function Fmt fshow(FlagsType#(enumType) f);
      Fmt result = $format("FlagsType { flags: %b =", f.flags);
      for (Integer i = 0; i < valueOf(SizeOf#(enumType)); i = i + 1) begin
         if (f.flags[i] == 1'b1)
            result = result + $format(" enum%d", i);
      end
      result = result + $format(" }");
      return result;
   endfunction
endinstance

// ============================================================================
// Flags typeclass
// ============================================================================

typeclass Flags#(type enumType);
   function Bool isOneHotOrZero(enumType e);
endtypeclass

// ============================================================================
// Conversion functions
// ============================================================================

function FlagsType#(enumType) enum2Flag(enumType e) = unpack(pack(e));

function Bool containFlags(FlagsType#(t) f1, FlagsType#(t) f2);
   return (f1.flags & f2.flags) == f2.flags;
endfunction

function Bool containEnum(FlagsType#(t) f, t e);
   return !isZero(f.flags & enum2Flag(e).flags);
endfunction

// ============================================================================
// Bit manipulation utility functions
// ============================================================================

function Bool isZero(Bit#(nSz) bits);
   return !(|bits);
endfunction

function Bool isZeroR(Bit#(nSz) v)
   provisos (Div#(nSz, 2, halfSz), Add#(halfSz, rest, nSz));
   if (valueOf(nSz) <= 1)
      return isZero(v);
   else begin
      Bit#(halfSz) lo = v[halfSz-1:0];
      Bit#(rest) hi = v[nSz-1:halfSz];
      return isZeroR(lo) && isZeroR(hi);
   end
endfunction

function Bool isZeroByteEn(Bit#(nSz) byteEn);
   return isZero(byteEn);
endfunction

function Bool isLessOrEqOne(Bit#(nSz) bits)
   provisos (Add#(1, anysize, nSz));
   return isZero(bits >> 1);
endfunction

function Bool isLessOrEqOneR(Bit#(nSz) bits)
   provisos (Add#(1, anysize, nSz), Div#(nSz, 2, halfSz), Add#(halfSz, rest, nSz));
   return isZeroR(bits >> 1);
endfunction

function Bool isOne(Bit#(nSz) bits)
   provisos (Add#(1, anysize, nSz));
   return isLessOrEqOne(bits) && (bits[0] == 1);
endfunction

function Bool isOneR(Bit#(nSz) bits)
   provisos (Add#(1, anysize, nSz), Div#(nSz, 2, halfSz), Add#(halfSz, rest, nSz));
   return isLessOrEqOneR(bits) && (bits[0] == 1);
endfunction

function Bool isTwo(Bit#(nSz) bits)
   provisos (Add#(2, anysize, nSz));
   return isZero(bits >> 2) && (bits[1] == 1) && (bits[0] == 0);
endfunction

function Bool isTwoR(Bit#(nSz) bits)
   provisos (Add#(2, anysize, nSz));
   return isZero(bits >> 2) && (bits[1] == 1) && (bits[0] == 0);
endfunction

function Bool isAllOnesR(Bit#(nSz) bits)
   provisos (Div#(nSz, 2, halfSz), Add#(halfSz, rest, nSz));
   if (valueOf(nSz) <= 1)
      return &bits;
   else begin
      Bit#(halfSz) lo = bits[halfSz-1:0];
      Bit#(rest) hi = bits[nSz-1:halfSz];
      return isAllOnesR(lo) && isAllOnesR(hi);
   end
endfunction

function Bool isLargerThanOne(Bit#(nSz) bits);
   return !isZero(bits >> 1);
endfunction

function Tuple2#(Bool, Bool) isZero4LargeBits(Bit#(nSz) bits)
   provisos (Div#(nSz, 2, halfSz), Add#(halfSz, otherHalf, nSz));
   Bit#(halfSz) lo = bits[halfSz-1:0];
   Bit#(otherHalf) hi = bits[nSz-1:halfSz];
   return tuple2(isZero(lo), isZero(hi));
endfunction

function Bit#(TAdd#(nSz, 1)) zeroExtendLSB(Bit#(nSz) bits);
   return {bits, 1'b0};
endfunction

function Bit#(TSub#(nSz, 1)) removeMSB(Bit#(nSz) bits)
   provisos (Add#(1, anysize, nSz));
   return truncateLSB(bits << 1);
endfunction

function t dontCareValue(t x);
   return ?;
endfunction

function t unwrapMaybe(Maybe#(t) m);
   return fromMaybe(?, m);
endfunction

function t unwrapMaybeWithDefault(t def, Maybe#(t) m);
   return fromMaybe(def, m);
endfunction

// ============================================================================
// Tuple element accessors
// ============================================================================

function a getTupleFirst(Tuple2#(a, b) t) = tpl_1(t);
function b getTupleSecond(Tuple2#(a, b) t) = tpl_2(t);
function b getTupleThird(Tuple3#(a, b, c) t) = tpl_3(t);
function c getTupleFourth(Tuple4#(a, b, c, d) t) = tpl_4(t);
function d getTupleFifth(Tuple5#(a, b, c, d, e) t) = tpl_5(t);
function e getTupleSixth(Tuple6#(a, b, c, d, e, f) t) = tpl_6(t);

// ============================================================================
// Identity function
// ============================================================================

function t identityFunc(t x) = x;

// ============================================================================
// Assertion helpers
// ============================================================================

function Action immAssert(Bool cond, String position, String name, String msg);
   action
      if (!cond) begin
         $display("ASSERT FAILED [%s] %s: %s", position, name, msg);
         $finish(1);
      end
   endaction
endfunction

function Action immFail(String position, String name, String msg);
   action
      $display("FAIL [%s] %s: %s", position, name, msg);
      $finish(1);
   endaction
endfunction

// ============================================================================
// PipeOut helper
// ============================================================================

function PipeOut#(t) toPipeOut(FIFOF#(t) ff) = f_FIFOF_to_PipeOut(ff);

// ============================================================================
// CountCF interface and module
// ============================================================================

interface CountCF#(type anytype);
   method Action incrOne();
   method Action decrOne();
   method Action _write(anytype val);
   method anytype _read();
endinterface

module mkCountCF(CountCF#(anytype))
   provisos (Arith#(anytype), Bits#(anytype, nSz), Literal#(anytype));

   // Main counter register
   Reg#(anytype) cntReg <- mkReg(0);

   // FIFOs for increment/decrement requests
   FIFOF#(void) incrQ <- mkFIFOF();
   FIFOF#(void) decrQ <- mkFIFOF();

   // CReg for write value (priority mechanism)
   CReg#(2, Maybe#(anytype)) writeReg <- mkCReg(tagged Invalid);

   // CReg for tracking increment/decrement
   CReg#(2, Bool) incrReg <- mkCReg(False);
   CReg#(2, Bool) decrReg <- mkCReg(False);

   // -- Rules --

   // write rule: When writeReg has valid value, write it to cntReg, clear FIFOs
   (* no_implicit_conditions, fire_when_enabled *)
   rule do_write (writeReg[0] matches tagged Valid .val);
      cntReg <= val;
      writeReg[0] <= tagged Invalid;
      incrQ.clear();
      decrQ.clear();
   endrule

   // increment rule: Sets incrReg when there is no pending write
   (* fire_when_enabled *)
   rule do_increment (!isValid(writeReg[0]) && incrQ.notEmpty());
      incrQ.deq();
      incrReg[0] <= True;
   endrule

   // decrement rule: Sets decrReg when there is no pending write
   (* fire_when_enabled *)
   rule do_decrement (!isValid(writeReg[0]) && decrQ.notEmpty());
      decrQ.deq();
      decrReg[0] <= True;
   endrule

   // incrAndDecr rule: Updates cntReg (+1/-1) based on incrReg/decrReg
   (* no_implicit_conditions, fire_when_enabled *)
   rule do_incrAndDecr;
      anytype newCnt = cntReg;
      if (incrReg[1]) newCnt = newCnt + 1;
      if (decrReg[1]) newCnt = newCnt - 1;
      cntReg <= newCnt;
      incrReg[0] <= False;
      decrReg[0] <= False;
   endrule

   // -- Interface methods --

   method Action incrOne();
      incrQ.enq(?);
   endmethod

   method Action decrOne();
      decrQ.enq(?);
   endmethod

   method Action _write(anytype val);
      writeReg[0] <= tagged Valid val;
   endmethod

   method anytype _read();
      return cntReg;
   endmethod

endmodule
