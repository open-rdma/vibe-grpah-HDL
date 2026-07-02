Output the following BSV typedefs as a ```bsv code block. No explanations.

typedef 2 TARGET_CYCLE_NS;
typedef 2 MIN_PKT_NUM_IN_RECV_BUF;
typedef TMul#(2, MAX_QP_WR) MAX_PENDING_WORK_COMP_NUM;
typedef 256 DATA_BUS_WIDTH;
typedef TExp#(31) MAX_MR_SIZE;
typedef TExp#(21) PAGE_SIZE_CAP;
typedef 4 MAX_QP;
typedef 32 MAX_QP_WR;
typedef 8 MAX_SGE;
typedef 8 MAX_CQ;
typedef MAX_QP_WR MAX_CQE;
typedef 256 MAX_MR;
typedef 2 MAX_PD;
typedef TDiv#(MAX_QP_WR, 2) MAX_QP_RD_ATOM;
typedef TDiv#(MAX_QP_WR, 2) MAX_QP_DST_RD_ATOM;
typedef 0 MAX_SRQ;
typedef MAX_QP_WR MAX_SRQ_WR;
typedef MAX_SGE MAX_SRQ_SGE;
typedef 1 MAX_SEND_SGE;
typedef 1 MAX_RECV_SGE;
typedef 0 MAX_INLINE_DATA;

```bsv