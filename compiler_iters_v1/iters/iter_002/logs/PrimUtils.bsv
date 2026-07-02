package PrimUtils;

import GetPut  :: *;
import FIFOF   :: *;
import Assert  :: *;

// ============================================================
// Type Definitions
// ============================================================

typedef 2  TWO;
typedef 4  FOUR;

// ============================================================
// FlagsType
// ============================================================

typedef struct {
    Bit#(SizeOf#(enumType)) flags;
} FlagsType#(type enumType) deriving (Bits, Bitwise, Eq);

typedef SizeOf#(FlagsType#(enumType))        FlagsType_WIDTH#(type enumType);
typedef TDiv#(FlagsType_WIDTH#(enumType), 8) FlagsType_BYTE_WIDTH#(type enumType);

// ============================================================
// Interface: CountCF
// ============================================================

interface CountCF#(type anytype);
    method Action incrOne();
    method Action decrOne();
    method Action _write(anytype write_val);
    method anytype _read();
endinterface

// ============================================================
// Bit Manipulation Functions
// ============================================================

function Bool isZero(Bit#(nSz) bits);
    Bool ret = unpack(|bits);
    return !ret;
endfunction

function Bool isZeroR(Bit#(nSz) bits)
    provisos (NumAlias#(TDiv#(nSz, 2), halfSz));
    if (valueOf(nSz) == 1) begin
        return !unpack(bits[0]);
    end
    else begin
        Bit#(halfSz) msb = bits[valueOf(nSz)-1:valueOf(halfSz)];
        Bit#(halfSz) lsb = bits[valueOf(halfSz)-1:0];
        return isZeroR(msb) && isZeroR(lsb);
    end
endfunction

function Bool isZeroByteEn(Bit#(nSz) byteEn);
    return isZero(byteEn);
endfunction

function Bool isLessOrEqOne(Bit#(nSz) bits);
    return isZero(bits >> 1);
endfunction

function Bool isOne(Bit#(nSz) bits);
    return isLessOrEqOne(bits) && unpack(bits[0]);
endfunction

function Bool isOneR(Bit#(nSz) bits)
    provisos (NumAlias#(TDiv#(nSz, 2), halfSz));
    if (valueOf(nSz) == 1) begin
        return unpack(bits[0]);
    end
    else begin
        Bit#(halfSz) msb = bits[valueOf(nSz)-1:valueOf(halfSz)];
        Bit#(halfSz) lsb = bits[valueOf(halfSz)-1:0];
        return isZeroR(msb) && isOneR(lsb);
    end
endfunction

function Bool isAllOnes(Bit#(nSz) bits);
    return unpack(&bits);
endfunction

function Bool isAllOnesR(Bit#(nSz) bits)
    provisos (NumAlias#(TDiv#(nSz, 2), halfSz));
    if (valueOf(nSz) == 1) begin
        return unpack(bits[0]);
    end
    else begin
        Bit#(halfSz) msb = bits[valueOf(nSz)-1:valueOf(halfSz)];
        Bit#(halfSz) lsb = bits[valueOf(halfSz)-1:0];
        return isAllOnesR(msb) && isAllOnesR(lsb);
    end
endfunction

function Bool isLargerThanOne(Bit#(nSz) bits);
    return !isZero(bits >> 1);
endfunction

function Tuple2#(Bool, Bool) isZero4LargeBits(Bit#(nSz) bits);
    Bit#(TDiv#(nSz, 2)) msbPart = bits[valueOf(nSz)-1:valueOf(TDiv#(nSz, 2))];
    Bit#(TDiv#(nSz, 2)) lsbPart = bits[valueOf(TDiv#(nSz, 2))-1:0];
    return tuple2(isZero(msbPart), isZero(lsbPart));
endfunction

function Bit#(nSz) zeroExtendLSB(Bit#(mSz) bits)
    provisos (Add#(mSz, anysize, nSz));
    return {bits, 0};
endfunction

function Bit#(TSub#(nSz, 1)) removeMSB(Bit#(nSz) bits)
    provisos (Add#(1, anysize, nSz));
    return bits[valueOf(nSz)-2:0];
endfunction

function anytype dontCareValue()
    provisos (Bits#(anytype, tSz));
    return ?;
endfunction

function anytype unwrapMaybe(Maybe#(anytype) maybe)
    provisos (Bits#(anytype, tSz));
    if (maybe matches tagged Valid .v)
        return v;
    else
        return ?;
endfunction

function anytype unwrapMaybeWithDefault(Maybe#(anytype) maybe, anytype defaultVal)
    provisos (Bits#(anytype, nSz));
    if (maybe matches tagged Valid .v)
        return v;
    else
        return defaultVal;
endfunction

// ============================================================
// Tuple Accessor Functions
// ============================================================

function anytype getTupleFirst(Tuple2#(anytype, anytype) tupleVal);
    return tpl_1(tupleVal);
endfunction

function anytype getTupleSecond(Tuple2#(anytype, anytype) tupleVal);
    return tpl_2(tupleVal);
endfunction

function anytype getTupleThird(Tuple3#(anytype, anytype, anytype) tupleVal);
    return tpl_3(tupleVal);
endfunction

function anytype getTupleFourth(Tuple4#(anytype, anytype, anytype, anytype) tupleVal);
    return tpl_4(tupleVal);
endfunction

function anytype getTupleFifth(Tuple5#(anytype, anytype, anytype, anytype, anytype) tupleVal);
    return tpl_5(tupleVal);
endfunction

function anytype getTupleSixth(Tuple6#(anytype, anytype, anytype, anytype, anytype, anytype) tupleVal);
    return tpl_6(tupleVal);
endfunction

// ============================================================
// Assertion Functions
// ============================================================

function Action immAssert(Bool condition, String assertName, Fmt assertFmtMsg);
    return (action
        if (!condition) begin
            $display("IMM ASSERT FAILED: %s - ", assertName, assertFmtMsg);
            $finish(1);
        end
    endaction);
endfunction

function Action immFail(String assertName, Fmt assertFmtMsg);
    return (action
        $display("IMM FAIL: %s - ", assertName, assertFmtMsg);
        $finish(1);
    endaction);
endfunction

// ============================================================
// PipeOut Conversion
// ============================================================

function PipeOut#(anytype) toPipeOut(FIFOF#(anytype) queue);
    return (interface PipeOut;
        method anytype first();
            return queue.first;
        endmethod
        method Action deq();
            queue.deq;
        endmethod
        method Bool notEmpty();
            return queue.notEmpty;
        endmethod
    endinterface);
endfunction

// ============================================================
// FlagsType Helper Functions
// ============================================================

function FlagsType#(enumType) enum2Flag(enumType inputVal)
    provisos (Bits#(enumType, tSz));
    return FlagsType#(enumType) {flags: pack(inputVal)};
endfunction

function Bool containFlags(FlagsType#(enumType) flags1, FlagsType#(enumType) flags2)
    provisos (Bits#(enumType, tSz));
    return (flags1.flags & flags2.flags) == flags2.flags;
endfunction

function Bool containEnum(FlagsType#(enumType) flags, enumType enumVal)
    provisos (Bits#(enumType, tSz));
    FlagsType#(enumType) flagVal = enum2Flag(enumVal);
    return containFlags(flags, flagVal);
endfunction

// ============================================================
// Module: mkCountCF - Conflict-Free Credit Counter
// ============================================================

module mkCountCF#(anytype resetVal)(CountCF#(anytype))
    provisos (Arith#(anytype), Bits#(anytype, tSz));

    Reg#(anytype) cntReg <- mkReg(resetVal);

    FIFOF#(Bool) incrQ <- mkFIFOF;
    FIFOF#(Bool) decrQ <- mkFIFOF;

    Reg#(Maybe#(anytype)) writeReg[2] <- mkCReg(2, tagged Invalid);
    Reg#(Bool)            incrReg[2]  <- mkCReg(2, False);
    Reg#(Bool)            decrReg[2]  <- mkCReg(2, False);

    (* no_implicit_conditions, fire_when_enabled *)
    rule write;
        if (writeReg[1] matches tagged Valid .val) begin
            cntReg        <= val;
            writeReg[1]   <= tagged Invalid;
            incrQ.clear;
            decrQ.clear;
            incrReg[1]    <= False;
            decrReg[1]    <= False;
        end
    endrule

    rule increment;
        incrQ.deq;
        incrReg[0] <= True;
    endrule

    rule decrement;
        decrQ.deq;
        decrReg[0] <= True;
    endrule

    (* fire_when_enabled *)
    rule incrAndDecr;
        anytype newVal = cntReg;
        if (incrReg[1]) newVal = newVal + 1;
        if (decrReg[1]) newVal = newVal - 1;
        cntReg     <= newVal;
        incrReg[1] <= False;
        decrReg[1] <= False;
    endrule

    method Action incrOne();
        incrQ.enq(True);
    endmethod

    method Action decrOne();
        decrQ.enq(True);
    endmethod

    method Action _write(anytype write_val);
        writeReg[0] <= tagged Valid write_val;
    endmethod

    method anytype _read();
        return cntReg;
    endmethod
endmodule

endpackage : PrimUtils
