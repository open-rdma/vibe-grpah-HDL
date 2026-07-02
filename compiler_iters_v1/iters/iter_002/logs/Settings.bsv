typedef 2 TARGET_CYCLE_NS; // Target clock cycle time in nanoseconds
typedef 2 MIN_PKT_NUM_IN_RECV_BUF; // Minimum number of packets that can be buffered in receive buffer
typedef TMul#(2, MAX_QP_WR) MAX_PENDING_WORK_COMP_NUM; // Maximum pending work completion entries, calculated as 2 * MAX_QP_WR
typedef 256 DATA_BUS_WIDTH; // Width of the data bus in bits, must be power of 2
typedef TExp#(31) MAX_MR_SIZE; // Maximum memory region size (2GB = 2^31)
typedef TExp#(21) PAGE_SIZE_CAP; // Maximum page size capacity (2MB = 2^21)
typedef 4 MAX_QP; // Maximum number of Queue Pairs
typedef 32 MAX_QP_WR; // Maximum Work Requests per Queue Pair
typedef 8 MAX_SGE; // Maximum Scatter-Gather Elements per Work Request
typedef 8 MAX_CQ; // Maximum number of Completion Queues
typedef MAX_QP_WR MAX_CQE; // Maximum Completion Queue Entries (equals MAX_QP_WR)
typedef 256 MAX_MR; // Maximum number of Memory Regions
typedef 2 MAX_PD; // Maximum number of Protection Domains
typedef TDiv#(MAX_QP_WR, 2) MAX_QP_RD_ATOM; // Maximum number of outstanding RDMA Read and Atomic operations per QP. Equals MAX_QP_WR / 2
typedef TDiv#(MAX_QP_WR, 2) MAX_QP_DST_RD_ATOM; // Maximum number of destination RDMA Read and Atomic operations per QP. Equals MAX_QP_WR / 2
typedef 0 MAX_SRQ; // Maximum number of Shared Receive Queues (0 = not supported)
typedef MAX_QP_WR MAX_SRQ_WR; // Maximum Work Requests per Shared Receive Queue
typedef MAX_SGE MAX_SRQ_SGE; // Maximum Scatter-Gather Elements per SRQ Work Request
typedef 1 MAX_SEND_SGE; // Maximum scatter-gather elements for send operations
typedef 1 MAX_RECV_SGE; // Maximum scatter-gather elements for receive operations
typedef 0 MAX_INLINE_DATA; // Maximum inline data size in bytes (0 = no inline data support)
