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

### mkConnectionWithAction (import Utils, NOT PAClib)
CRITICAL: This function is defined in the Utils package (Utils.bsv), NOT in PAClib.
Connects a Get source to a Put sink, with an action callback per transfer.
Takes 3 arguments: Get#(T), Put#(T), function Action f(T val). Returns Empty.
Instantiate WITHOUT binding (no let/<- needed since it returns Empty):
```
mkConnectionWithAction(toGet(sourcePipeOut), toPut(sinkFIFO), actionFunc);
```
The actionFunc receives the data being transferred and can perform side effects.

### toPipeOut (import PAClib)
Converts FIFOF#(T) to PipeOut#(T). Usage: `toPipeOut(fifoQueue)`

### toGet (import PAClib)
Converts PipeOut#(T) to Get#(T). Usage: `toGet(pipeOut)`

### toPut (import PAClib)
Converts FIFOF#(T) to Put#(T). Usage: `toPut(fifoQueue)`

## Function Definition Syntax
```
function Action actionFunc(DataType param);
    action
        // imperative actions
    endaction
endfunction
```

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

## Port Categories
- `clock`: Clock source
- `reset`: Reset signal  
- `data`: All other signals

## Required Imports for this module
- FIFOF (mkFIFOF)
- GetPut
- PAClib (toPipeOut, toGet, toPut, mkConnectionWithAction)
- Controller (CntrlStatus type)
- ExtractAndPrependPipeOut (mkHeader2DataStream, mkPrependHeader2PipeOut)
- Headers (PSN type)
- DataTypes (DataStream, HeaderRDMA, HeaderMetaData, DataStreamPipeOut)
