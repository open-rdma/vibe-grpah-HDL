package SpecialFIFOF;

// === Deterministic type extraction from SpecialFIFOF.bsv ===

import Cntrs :: *;
import FIFOF :: *;
import PAClib :: *;
import PrimUtils :: *;
import Vector :: *;

typedef enum {
    SCAN_Q_FIFOF_MODE,
    SCAN_Q_PRE_SCAN_MODE,
    SCAN_Q_SCAN_MODE
} ScanState deriving(Bits, Eq, FShow);

interface ScanCntrl#(type anytype);
    method anytype getHead();
    method Action modifyHead(anytype head);
    method Action preScanStart();
    method Action scanStart();
    method Action scanStop();
    method Action preScanRestart();
    method Action clear();
    method Bool hasScanOut();
    method Bool isScanDone();
    method Bool deqPulse();
    
endinterface
interface ScanFIFOF#(numeric type qSz, type anytype);
    interface FIFOF#(anytype) fifof;
    interface ScanCntrl#(anytype) scanCntrl;
    interface PipeOut#(anytype) scanPipeOut;
    method UInt#(TLog#(TAdd#(1, qSz))) size();
endinterface
interface SearchIfc2#(type anytype);
    method Maybe#(anytype) search(function Bool searchFunc(anytype fifoItem));
endinterface
interface SearchFIFOF#(numeric type qSz, type anytype);
    interface FIFOF#(anytype) fifof;
    interface SearchIfc2#(anytype) searchIfc;
endinterface
interface SearchIfc#(type anytype);
    method Action searchReq(anytype item2Search);
    method ActionValue#(Maybe#(anytype)) searchResp();
endinterface
interface CacheIfc#(type anytype);
    method Action push(anytype inputVal);
    method Action clear();
endinterface
interface CacheFIFO#(numeric type qSz, type anytype);
    interface CacheIfc#(anytype) cacheIfc;
    interface SearchIfc#(anytype) searchIfc;
endinterface


endpackage
