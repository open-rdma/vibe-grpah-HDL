import ClientServer :: *;
import FIFOF :: *;
import GetPut :: *;
import PAClib :: *;
import Vector :: *;

// Import the GENERATED module (interface Gen + module Gen)
// Must be imported FIRST to avoid interface name conflicts
import Header2DataStream :: *;
// Import original for mkDataStream2Header and type definitions
import ExtractAndPrependPipeOut :: *;
import Headers :: *;
import DataTypes :: *;
import Settings :: *;
import SimDma :: *;
import PrimUtils :: *;
import Utils :: *;
import Utils4Test :: *;

(* doc = "testcase" *)
module mkTestGeneratedHeader2DataStream(Empty);
    let alwaysHasPayload = False;
    let minHeaderLen = 1;
    let maxHeaderLen = fromInteger(valueOf(HEADER_MAX_BYTE_LENGTH));

    Vector#(3, PipeOut#(HeaderMetaData)) headerMetaDataPipeOutVec <-
        mkRandomHeaderMetaPipeOut(minHeaderLen, maxHeaderLen, alwaysHasPayload);
    let headerMetaDataPipeOut4Dma = headerMetaDataPipeOutVec[0];
    let headerMetaDataPipeOut4Conv <- mkBufferN(2, headerMetaDataPipeOutVec[1]);
    let headerMetaDataPipeOut4Ref  <- mkBufferN(2, headerMetaDataPipeOutVec[2]);

    let pktLenPipeOut <- mkFunc2Pipe(headerMetaData2PktLen, headerMetaDataPipeOut4Dma);
    Vector#(2, DataStreamPipeOut) dataStreamPipeOutVec <-
        mkFixedPktLenDataStreamPipeOut(pktLenPipeOut);
    let dataStreamPipeOut4Conv = dataStreamPipeOutVec[0];
    let dataStreamPipeOut4Ref <- mkBufferN(2, dataStreamPipeOutVec[1]);

    // Use the ORIGINAL mkDataStream2Header from ExtractAndPrependPipeOut
    let ds2hPipeOut <- mkDataStream2Header(
        dataStreamPipeOut4Conv, headerMetaDataPipeOut4Conv
    );
    Reg#(Bool) clearReg <- mkReg(True);

    // Use the GENERATED mkHeader2DataStreamGen
    let h2dsPipeOut <- mkHeader2DataStreamGen(clearReg, ds2hPipeOut);

    let countDown <- mkCountDown(valueOf(MAX_CMP_CNT));

    rule clearAll if (clearReg);
        clearReg <= False;
    endrule

    rule compareHeaderMetaData;
        let headerMetaData = h2dsPipeOut.headerMetaData.first;
        h2dsPipeOut.headerMetaData.deq;

        let refHeaderMetaData = headerMetaDataPipeOut4Ref.first;
        headerMetaDataPipeOut4Ref.deq;

        immAssert(
            headerMetaData == refHeaderMetaData,
            "headerMetaData assertion @ mkTestGeneratedHeader2DataStream",
            $format(
                "headerMetaData=", headerMetaData,
                " should == refHeaderMetaData=", refHeaderMetaData
            )
        );
    endrule

    rule compareHeaderDataStream;
        let headerDataStream = h2dsPipeOut.headerDataStream.first;
        h2dsPipeOut.headerDataStream.deq;

        let refDataStream = dataStreamPipeOut4Ref.first;
        dataStreamPipeOut4Ref.deq;

        immAssert(
            headerDataStream == refDataStream,
            "headerDataStream assertion @ mkTestGeneratedHeader2DataStream",
            $format(
                "headerDataStream=", fshow(headerDataStream),
                " should == refDataStream=", fshow(refDataStream)
            )
        );

        countDown.decr;
    endrule
endmodule

// Helper function matching the one from TestExtractAndPrependPipeOut.bsv
function PktLen headerMetaData2PktLen(HeaderMetaData hmd) = zeroExtend(hmd.headerLen);
