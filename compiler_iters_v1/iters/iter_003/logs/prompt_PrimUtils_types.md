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


Generate BSV types for: PrimUtils

Typedefs:
  typedef 2 TWO;
  typedef 4 FOUR;

Structs:
  typedef struct {
    Bit#(SizeOf#(enumType)) flags;
  } FlagsType deriving(Bits, Bitwise, Eq);
  typedef SizeOf#(FlagsType) FlagsType_WIDTH;
  typedef TDiv#(FlagsType_WIDTH, 8) FlagsType_BYTE_WIDTH;

Output in ```bsv block. Include imports. Generate now: