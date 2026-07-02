# bsv→yaml→bsv 转换实验测试集

> 所属知识库：`prompt_v2.md` | 加载时机：选择测试目标、规划测试顺序时

---

## 附录A：测试样本清单

以下20个测试样本从 blue-rdma 目录下的 Bluespec SystemVerilog 源代码和测试用例中挑选，按**从简单到复杂**的顺序排列。该顺序遵循模块依赖关系——前一个模块是被后续模块依赖的基础，因此实验应按此顺序逐步推进。

### 测试选择原则

1. **依赖优先**：被其他模块依赖的基础模块先测试，依赖方后测试
2. **复杂度递增**：从纯类型定义→简单函数→单模块→多子模块→集成模块
3. **可验证性**：每个测试样本都有对应的 testbench 可用于验证生成代码的正确性
4. **代表性**：涵盖不同类型（纯定义、工具函数、状态机、流水线、缓存、协议处理、集成）

### 模块依赖关系图

```
Settings.bsv ─────────────────────────────────────────────────────┐
Headers.bsv ──────────────────────────────────────────────────────┤
PrimUtils.bsv ────────────────────────────────────────────────────┤
SpecialFIFOF.bsv (→PrimUtils) ────────────────────────────────────┤
DataTypes.bsv (→Settings, Headers, PrimUtils, SpecialFIFOF) ──────┤
Utils.bsv (→DataTypes, Headers, PrimUtils, Settings) ─────────────┤
Arbitration.bsv (→PrimUtils, Utils) ──────────────────────────────┤
WorkCompGen.bsv (→DataTypes, Headers, PrimUtils) ─────────────────┤
ExtractAndPrependPipeOut.bsv (→DataTypes, Headers, PrimUtils) ────┤
DupReadAtomicCache.bsv (→DataTypes, Headers, PrimUtils, Utils) ───┤
InputPktHandle.bsv (→DataTypes, Headers, PrimUtils, Utils) ───────┤
SendQ.bsv (→DataTypes, Headers, PrimUtils, Utils) ────────────────┤
ReqGenSQ.bsv (→DataTypes, Headers, PrimUtils, Utils, SpecialFIFOF)┤
RetryHandleSQ.bsv (→DataTypes, Headers, PrimUtils, Utils) ────────┤
QueuePair.bsv (→DataTypes, Headers, PrimUtils, ...子模块) ────────┤
RespHandleSQ.bsv (→DataTypes, Headers, PrimUtils, ...子模块) ─────┤
PayloadConAndGen.bsv (→DataTypes, Headers, PrimUtils, ...子模块) ─┤
PayloadGen.bsv (→DataTypes, Headers, PrimUtils, ...子模块) ───────┤
ReqHandleRQ.bsv (→DataTypes, Headers, PrimUtils, ...子模块) ──────┤
MetaData.bsv (→Controller, QueuePair, Arbitration, DataTypes...) ─┤
Controller.bsv (→DataTypes, Headers, PrimUtils, Utils) ───────────┤
TransportLayer.bsv (→所有上述模块) ───────────────────────────────┘
```

---

### Phase 1 — 纯类型定义（无行为逻辑，验证YAML对类型系统的表达能力）

**T01: Settings.bsv**
- 源文件: `blue-rdma/src/Settings.bsv` (74行)
- 测试文件: 无独立testbench（被所有其他模块引用，通过下游testbench间接验证）
- 复杂度: ★☆☆☆☆
- 模块类型: 纯 `typedef` 常量定义（数值参数、位宽等）
- 无 interface/module/rule
- 验证方式: 生成的 typedef 被下游模块引用后能通过编译即可
- 关键挑战: YAML 如何表达 BSV 的数值类型宏（`TAdd#()`, `TLog#()`, `TDiv#()` 等）

**T02: Headers.bsv**
- 源文件: `blue-rdma/src/Headers.bsv` (432行)
- 测试文件: 无独立testbench（间接验证）
- 复杂度: ★★☆☆☆
- 模块类型: 类型定义 + 纯函数（enum、struct、辅助函数）
- 包含 `RdmaOpCode` enum、`BTH`/`AETH`/`RETH` 等 RDMA 协议头结构体
- 包含 `calcHeaderLenByTransTypeAndRdmaOpCode()` 和 `rdmaOpCodeHasPayload()` 纯函数
- 验证方式: 生成的函数逻辑被下游模块调用后正确
- 关键挑战: YAML 如何表达 enum 变体、struct 字段、纯函数逻辑

---

### Phase 2 — 简单工具模块（独立可测，逻辑简单）

**T03: Utils.bsv (PSN函数)**
- 源文件: `blue-rdma/src/Utils.bsv` (1788行)
- 测试文件: `blue-rdma/test/TestUtils.bsv` (183行, 1个testcase: `mkTestPsnFunc`)
- 复杂度: ★★☆☆☆
- 模块类型: 工具函数集合
- 测试仅覆盖 PSN 比较/运算相关函数（`psnComp`, `psnInc`, `psnDec` 等）
- 验证方式: testbench 验证 PSN 计算正确性
- 关键挑战: 从大文件中提取被测试的子集函数，YAML 描述纯函数逻辑

**T04: SpecialFIFOF.bsv**
- 源文件: `blue-rdma/src/SpecialFIFOF.bsv` (740行)
- 测试文件: `blue-rdma/test/TestSpecialFIFOF.bsv` (470行, 4个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 自定义 FIFO 数据结构（带 interface/module/rule）
- 包含 `mkScanFIFOF`、`mkSearchFIFOF`、`mkCacheFIFO2` 三个模块，每个都有状态机
- Testcases: `mkTestCacheFIFO2`, `mkTestScanFIFOF`, `mkTestSearchFIFOF`, `mkTestVectorSearch`
- 验证方式: 每个子模块有独立 testbench
- 关键挑战: YAML 表达状态机逻辑（FSM）、多规则调度、interface 方法定义

---

### Phase 3 — 仲裁与工作完成生成（中等单模块）

**T05: Arbitration.bsv**
- 源文件: `blue-rdma/src/Arbitration.bsv` (456行)
- 测试文件: `blue-rdma/test/TestArbitration.bsv` (365行, 3个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 仲裁器（含泛型参数化模块）
- 包含 `mkPipeOutArbiter`、`mkServerArbiter`、`mkClientArbiter`
- 涉及 round-robin 仲裁算法、流水线处理
- Testcases: `mkTestPipeOutArbiter`, `mkTestServerArbiter`, `mkTestClientArbiter`
- 关键挑战: 泛型模块的 YAML 表达、仲裁算法的自然语言描述

**T06: WorkCompGen.bsv**
- 源文件: `blue-rdma/src/WorkCompGen.bsv` (701行)
- 测试文件: `blue-rdma/test/TestWorkCompGen.bsv` (413行, 4个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 工作完成通知生成器（RDMA CQ/WC 语义）
- 区分 RQ 路径和 SQ 路径，正常/错误两种情形
- Testcases: `mkTestWorkCompGenNormalCaseRQ`, `mkTestWorkCompGenErrFlushCaseRQ`, `mkTestWorkCompGenNormalCaseSQ`, `mkTestWorkCompGenErrFlushCaseSQ`
- 关键挑战: RDMA 领域知识如何在 YAML 中表达

---

### Phase 4 — 流水线与包处理模块（中等复杂度，Pipeline模式）

**T07: ExtractAndPrependPipeOut.bsv**
- 源文件: `blue-rdma/src/ExtractAndPrependPipeOut.bsv` (748行)
- 测试文件: `blue-rdma/test/TestExtractAndPrependPipeOut.bsv` (329行, 5个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 数据流处理管线（Header提取/插入/转换）
- 涉及 `DataStream` <-> `HeaderRDMA` 双向转换、字节对齐
- Testcases: `mkTestHeaderAndDataStreamConversion`, `mkTestPrependHeaderBeforeEmptyDataStream`, `mkTestExtractHeaderWithPayloadLessThanOneFrag`, `mkTestExtractHeaderLongerThanDataStream`, `mkTestExtractAndPrependHeader`
- 关键挑战: 字节操作逻辑在YAML中的声明式描述

**T08: DupReadAtomicCache.bsv**
- 源文件: `blue-rdma/src/DupReadAtomicCache.bsv` (802行)
- 测试文件: `blue-rdma/test/TestDupReadAtomicCache.bsv` (363行, 2个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 缓存模块（去重+原子操作缓存）
- Testcases: `mkTestDupReadAtomicCache`, `mkTestCacheFIFO`
- 关键挑战: 缓存查找/更新逻辑、去重算法

**T09: InputPktHandle.bsv**
- 源文件: `blue-rdma/src/InputPktHandle.bsv` (917行)
- 测试文件: `blue-rdma/test/TestInputPktHandle.bsv` (251行, 4个testcase)
- 复杂度: ★★★★☆
- 模块类型: 输入包处理（Header验证、包长度计算、CNP处理）
- Testcases: `mkTestCalculateRandomPktLen`, `mkTestCalculatePktLenEqPMTU`, `mkTestCalculateZeroPktLen`, `mkTestReceiveCNP`
- 关键挑战: 包协议解析逻辑、多条件分支

---

### Phase 5 — 发送队列与请求生成（多子模块协作）

**T10: SendQ.bsv**
- 源文件: `blue-rdma/src/SendQ.bsv` (1088行)
- 测试文件: `blue-rdma/test/TestSendQ.bsv` (673行, 4个testcase)
- 复杂度: ★★★★☆
- 模块类型: 发送队列管理（Work Request 队列化）
- 包含 raw packet、normal、no-payload、zero-payload 等场景
- Testcases: `mkTestSendQueueRawPktCase`, `mkTestSendQueueNormalCase`, `mkTestSendQueueNoPayloadCase`, `mkTestSendQueueZeroPayloadLenCase`
- 关键挑战: 队列管理状态机、SQ 语义

**T11: ReqGenSQ.bsv**
- 源文件: `blue-rdma/src/ReqGenSQ.bsv` (1163行)
- 测试文件: `blue-rdma/test/TestReqGenSQ.bsv` (398行, 3个testcase)
- 复杂度: ★★★★☆
- 模块类型: SQ请求生成器（将WorkReq转换为RDMA请求包）
- Testcases: `mkTestReqGenNormalCase`, `mkTestReqGenZeroLenCase`, `mkTestReqGenDmaReadErrCase`
- 关键挑战: 复杂的数据转换管线、DMA读写协调

---

### Phase 6 — QP管理与重试处理（核心协议逻辑）

**T12: QueuePair.bsv**
- 源文件: `blue-rdma/src/QueuePair.bsv` (652行)
- 测试文件: `blue-rdma/test/TestQueuePair.bsv` (747行, 7个testcase)
- 复杂度: ★★★★☆
- 模块类型: QP（Queue Pair）核心管理模块（RDMA最核心概念）
- 内部实例化多个子模块（SQ, RQ, Retry, RespHandle 等）
- 7个testcases覆盖创建、销毁、状态转换、错误处理、正常操作
- 关键挑战: 多子模块实例化的YAML表达、跨模块连线、QP状态机

**T13: RetryHandleSQ.bsv**
- 源文件: `blue-rdma/src/RetryHandleSQ.bsv` (740行)
- 测试文件: `blue-rdma/test/TestRetryHandleSQ.bsv` (1076行, 7个testcase)
- 复杂度: ★★★★☆
- 模块类型: SQ重试处理器（RNR、超时、序列错误重试）
- 7个testcases覆盖各种重试场景和嵌套重试
- 关键挑战: 重试逻辑的计时器、状态机、嵌套重试

**T14: RespHandleSQ.bsv**
- 源文件: `blue-rdma/src/RespHandleSQ.bsv` (1695行)
- 测试文件: `blue-rdma/test/TestRespHandleSQ.bsv` (910行, 10个testcase)
- 复杂度: ★★★★★
- 模块类型: SQ响应处理器（ACK/NAK处理、完成通知生成）
- 10个testcases：正常响应、重复响应、Ghost响应、各类错误
- 关键挑战: 复杂的响应分类和状态转换

---

### Phase 7 — 负载处理（大模块，复杂数据通路）

**T15: PayloadConAndGen.bsv**
- 源文件: `blue-rdma/src/PayloadConAndGen.bsv` (1234行)
- 测试文件: `blue-rdma/test/TestPayloadConAndGen.bsv` (957行, 7个testcase)
- 复杂度: ★★★★☆
- 模块类型: 负载构造与生成（Payload Construction & Generation）
- 7个testcases：正常负载、分段填充、DMA控制(正常/取消)、地址分块
- 关键挑战: DMA读写控制、负载分段/填充逻辑

**T16: PayloadGen.bsv**
- 源文件: `blue-rdma/src/PayloadGen.bsv` (2633行)
- 测试文件: `blue-rdma/test/TestPayloadGen.bsv` (2086行, 13个testcase)
- 复杂度: ★★★★★
- 模块类型: 最复杂的负载生成模块（SGE scatter/gather、PMTU分段、DMA控制）
- 13个testcases：包数计算、地址分块、DMA scatter/gather、分段调整
- 关键挑战: 大规模数据处理管线、SGE分段合并、复杂边界条件

**T17: ReqHandleRQ.bsv**
- 源文件: `blue-rdma/src/ReqHandleRQ.bsv` (3691行)
- 测试文件: `blue-rdma/test/TestReqHandleRQ.bsv` (1688行, 9个testcase)
- 复杂度: ★★★★★
- 模块类型: 代码行数最大的单模块——RQ请求处理器
- 9个testcases：正常请求、重复请求、无ACK请求、超限读写原子请求、各类错误
- 关键挑战: 非常长且复杂的控制逻辑、多层嵌套条件

---

### Phase 8 — 元数据基础设施（多层嵌套图结构）

**T18: MetaData.bsv**
- 源文件: `blue-rdma/src/MetaData.bsv` (1020行)
- 测试文件: `blue-rdma/test/TestMetaData.bsv` (1995行, 7个testcase)
- 复杂度: ★★★★★
- 模块类型: 资源元数据管理系统（MR内存注册、PD保护域、QP管理、TLB缓存）
- 内部形成嵌套层级：`MetaDataSrv → MetaDataPDs → MetaDataMRs → TagVecSrv`
- 同时包含 `BramCache → CascadeCache → TLB` 缓存层级
- 7个testcases覆盖 MR/PD/QP 的 CRUD、权限检查、缓存/TLB
- 关键挑战: **天然的多层级嵌套图结构**——这是验证YAML嵌套图表达能力的最佳样本

---

### Phase 9 — 顶层集成（全系统验证）

**T19: Controller.bsv**
- 源文件: `blue-rdma/src/Controller.bsv` (1056行)
- 测试文件: `blue-rdma/test/TestController.bsv` (85行, 1个testcase: `mkTestCntrlInVec`)
- 复杂度: ★★★★☆
- 模块类型: QP控制器（QP状态转换、属性验证）
- Testcase 较少但模块本身是QP管理的关键路径
- 关键挑战: QP状态机的YAML描述、属性掩码验证逻辑

**T20: TransportLayer.bsv（集成测试）**
- 源文件: `blue-rdma/src/TransportLayer.bsv` (185行)
- 测试文件: `blue-rdma/test/TestTransportLayer.bsv` (1298行, 2个testcase)
- 复杂度: ★★★★★
- 模块类型: **全系统集成模块**——实例化所有子模块并互联
- 实例化 `MAX_QP` 个 QueuePair + Metadata 子系统 + 包处理管线
- Testcases: `mkTestTransportLayerNormalCase`, `mkTestTransportLayerErrorCase`
- 关键挑战: **整个嵌套图结构的端到端验证**——所有子模块的YAML→BSV转换必须正确

---

### 测试推进策略

| 阶段 | 测试编号 | 累积依赖 | 实验目标 |
|------|---------|---------|---------|
| Phase 1 | T01-T02 | 无 | 验证YAML对BSV类型系统的表达能力 |
| Phase 2 | T03-T04 | +PrimUtils | 验证YAML对简单逻辑模块的表达 |
| Phase 3 | T05-T06 | +Utils, SpecialFIFOF | 验证YAML对仲裁/通知模式的表达 |
| Phase 4 | T07-T09 | +Arbitration, WorkCompGen | 验证YAML对流水线/包处理的表达 |
| Phase 5 | T10-T11 | +Extract, DupCache, InputPkt | 验证YAML对队列管理的表达 |
| Phase 6 | T12-T14 | +SendQ, ReqGenSQ | 验证YAML对QP+重试+响应逻辑的表达 |
| Phase 7 | T15-T17 | +QueuePair, Retry, RespHandle | 验证YAML对复杂数据通路的表达 |
| Phase 8 | T18 | +Payload, ReqHandle | 验证YAML对嵌套图层级结构的表达 |
| Phase 9 | T19-T20 | +MetaData, Controller | 端到端全系统验证 |
