# 软件迭代优化需求文档

> 基于 nested_v1 / nested_v2 多层级知识合并实验及前后端框架审查，整理出的迭代优化需求。
> 日期：2026-07-01

---

## 一、问题总览

通过两轮实验（nested_v1 3层3模块、nested_v2 4层4模块），共发现 **20 个问题**，其中：

- **前端图形渲染**：连接格式不兼容、缺少信号节点、缺少 transform 可视化
- **YAML 数据格式**：缺少 signals/methods/provisos 等结构化字段
- **后端知识合并**：知识重复、proviso 传播、import 分析、命名规范等
- **知识组织模型**：缺少语言模板层、知识层级混乱、子模块知识泄露

详细问题清单见 `deli_auto_iters/nested_v1/state/problems_and_design.md` 和 `deli_auto_iters/nested_v2/state/findings_and_results.md`。

---

## 二、YAML 数据格式扩展

### 2.1 新增 `signals` 节（内部信号声明）

**现状问题 (P2, P10)**：内部信号通过 `self.signalName` 在 connections 中间接引用，前端和合并脚本无法区分「外部端口」和「内部信号」。连接渲染时 `self` 不是有效节点，连线无法显示。

**需求描述**：在 YAML 顶层新增 `signals` 字段，声明模块所有内部布线信号。

**数据格式**：
```yaml
signals:
  - name: "leftReq"
    type: "Bit#(TDiv#(reqNum, 2))"
    description: "Lower half of request vector"

  - name: "grantReg"
    type: "Reg#(Bit#(reqNum))"
    init: "0"
    description: "Pipeline register holding grant output"
```

**字段说明**：
| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| name | 是 | string | 信号名称（在模块内唯一） |
| type | 是 | string | BSV 类型表达式，如 `Bit#(reqNum)`、`Reg#(Bit#(reqNum))` |
| init | 否 | string | 初始值（寄存器类型时必须） |
| description | 否 | string | 信号用途说明 |

### 2.2 新增 `methods` 节（方法签名声明）

**现状问题 (P13)**：connections 引用 port 名称（如 `grantVec`），但 BSV 代码中使用 method 名称（如 `grant()`）。两端没有显式映射关系。

**需求描述**：在 YAML 顶层新增 `methods` 字段，显式声明接口方法签名及其与端口的映射。

**数据格式**：
```yaml
methods:
  - name: "grant"
    arguments:
      - name: "reqVec"
        type: "Bit#(reqNum)"
    returns: "ActionValue#(Bit#(reqNum))"
    maps_to_port: "grantVec"
    description: "Returns one-hot grant, updates internal priority state"
```

**字段说明**：
| 字段 | 必填 | 类型 | 说明 |
|------|------|------|------|
| name | 是 | string | 方法名称（camelCase） |
| arguments | 否 | array | 参数列表，每项含 name + type |
| returns | 是 | string | 返回值类型 |
| maps_to_port | 否 | string | 关联的输出端口名 |
| description | 否 | string | 方法功能描述 |

### 2.3 新增 `provisos` 节（模块类型约束）

**现状问题 (P8)**：provisos 只在 `meta.knowledge` 中以自然语言描述，合并脚本无法解析和传播。导致父模块编译失败。

**需求描述**：在 YAML 顶层新增 `provisos` 字段，以结构化字符串列表声明模块的类型约束。

**数据格式**：
```yaml
provisos:
  - "Add#(1, _, reqNum)"
  - "NumAlias#(TLog#(reqNum), logReqNum)"
  - "Add#(TLog#(reqNum), 1, TLog#(TAdd#(1, reqNum)))"
```

**合并规则**（在知识合并脚本中实现）：
1. 子模块的 provisos 中的形参替换为父模块传入的实参
2. 过滤 `NumAlias` 条目（子模块本地别名，父模块不需要）
3. 过滤仅含常量表达式的条目（如 `Add#(1, _, 2)`，会导致 BSV 求解器干扰）
4. 去重后合入父模块的 provisos 列表

### 2.4 nodes 节点新增 `parameters` 字段

**现状问题 (P1)**：类型参数通过 `properties: { reqNum: "TDiv#(reqNum, 2)" }` 传递，合并脚本把它当普通字符串，无法做类型替换。

**需求描述**：在 `nodes[]` 条目中新增 `parameters` 字段，与 `properties` 分离。

**数据格式**：
```yaml
nodes:
  - id: "left_arb_inst"
    ref: "library/round_robin_arbiter/round_robin_arbiter.yaml"
    description: "Round-robin arbiter for lower half"
    parameters:
      reqNum: "TDiv#(reqNum, 2)"
    properties: {}
```

**语义**：`parameters` 是类型/泛型参数的绑定（用于 proviso 传播和实例化模板生成），`properties` 是用户自定义属性的键值对（透传到生成 prompt）。

### 2.5 端口类型改为参数化表达式

**现状问题 (P5)**：端口 type 使用 `Bit_N` 等泛型名称，不体现实际参数化宽度。

**需求描述**：端口 type 使用带参数的具体类型表达式。

**变更前**：
```yaml
ports:
  - name: "reqVec"
    type: "Bit_N"
```

**变更后**：
```yaml
ports:
  - name: "reqVec"
    type: "Bit#(reqNum)"
```

### 2.6 端口增加 `category` 取值 `internal`

**现状问题 (P10)**：内部状态寄存器被列在 ports 中（如 `priorityState | internal`），合并脚本输出给父模块时无法过滤。

**需求描述**：`PortData.category` 的合法值从 `'clock' | 'reset' | 'data'` 扩展为 `'clock' | 'reset' | 'data' | 'internal'`。

`category: internal` 的端口：
- 不在前端画布上显示为可连线端口
- 不随子模块接口传递给父模块
- 仅用于知识合并时告知 LLM 内部状态结构

### 2.7 连接增加 `transform` 字段（可显示）

**现状问题 (P11)**：连接描述位操作（如 `truncate(reqVec)`）只在 description 中以自然语言存在，合并脚本无法解析。

**需求描述**：`Connection` 接口增加可选 `transform` 字段。

**数据格式**：
```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    transform: "truncate(reqVec)"
    to: [{ signal: "leftReq" }]
    description: "Extract lower half"
```

此字段同时服务于：
- 前端：在连线上显示 transform 标签
- 后端知识合并：解析 transform 类型推导 proviso

---

## 三、前端图形渲染改进（方案 B）

### 3.1 新增 Signal 节点类型

**现状问题**：`signal:` 引用在 `_addConnection` 中找不到对应节点（nodeMap 中没有 signal 条目），连接被静默丢弃。

**需求描述**：注册新的 LiteGraph 节点类型 `rtl/signal`，用于表示模块内部信号。

**节点行为**：
```
┌──────────────┐
│  ◄── leftReq ───    ← 输入侧（从 graph_input 或子模块 output 来）
│  leftReq ──────►    ← 输出侧（接到子模块 input 或 graph_output）
│    Bit#(TDiv#(reqNum, 2))
└──────────────┘
```

- 标题显示信号名称
- 副标题显示类型（如 `Bit#(TDiv#(reqNum, 2))`）
- 有一个 input slot 和一个 output slot（同名），作为数据中转
- 颜色/样式与 `rtl/module` 区分（建议浅灰色或虚线边框）
- 不可双击打开子图
- 可通过工具栏按钮显隐

**渲染规则**：
- 连接 `signal: "foo"` 等价于连接 `node: "foo"`（signal 节点以信号名为 title）
- `_addConnection` 的 `nodeMap` 中需包含 signal 节点

**修改文件**：
- 新建 `frontend/src/nodes/signal-node.ts`
- `frontend/src/core/graph-manager.ts`：`_addConnection`、`_populateGraph`、`toYAML`、`_ensureBoundaryNodes`
- `frontend/src/types/graph-types.ts`：扩展 `ConnectionTarget`

### 3.2 ConnectionTarget 支持 signal 引用

**现状问题**：`ConnectionTarget` 只有 `{ node, port }` 两个字段。

**需求描述**：扩展 `ConnectionTarget` 支持 signal 引用。

**类型定义变更** (`graph-types.ts`)：
```typescript
export interface ConnectionTarget {
  node?: string;    // "graph_input" | "graph_output" | child_instance_id
  port?: string;    // port name on the node
  signal?: string;  // signal name (for internal wiring)
}
```

**约束**：每个 ConnectionTarget 中 `node` 和 `signal` 互斥（有且仅有一个）。

**修改文件**：
- `frontend/src/types/graph-types.ts`
- `frontend/src/core/graph-manager.ts`：`_addConnection`、`toYAML`、`fromYAML`
- `frontend/src/core/connection-validator.ts`：增加 signal 相关的校验

### 3.3 连接线显示 transform 标签

**需求描述**：当 connection 有 `transform` 字段时，在 LiteGraph 连接线上渲染标签文本。

**实现方式**：
- 利用 LiteGraph 的 link 渲染钩子或自定义 link 渲染
- 标签内容为 transform 字段值（如 `truncate(reqVec)`、`zeroExtend(leftGrant)`）
- 标签字体小号、灰色、置于连线中点

**修改文件**：
- 可能在 `frontend/src/nodes/rtl-module.ts` 或新建 link renderer
- `frontend/src/types/graph-types.ts`：`Connection` 增加 `transform?: string`

### 3.4 类型系统增强

**现状问题**：类型验证只做相等比较（`typeSystem.areCompatible`），不支持参数化类型的包含关系判断。

**需求描述**：
1. 支持参数化类型注册：`Bit#(N)`、`Vector#(N, T)` 等
2. 兼容性检查支持参数替换：`Bit#(reqNum)` 与 `Bit#(TDiv#(reqNum, 2))` 是不同的具体类型但在同一宽度族中
3. 类型编辑器中可以定义参数化类型模板

**修改文件**：
- `frontend/src/core/type-system.ts`
- `frontend/src/ui/type-editor.ts`

### 3.5 属性面板扩展

**需求描述**：属性面板增加以下可编辑区域：

**模块属性面板**：
- `meta.knowledge` → 多行文本框（Markdown 编辑）
- `provisos` → 字符串列表编辑器
- `signals` → 表格编辑器（name / type / init / description）
- `methods` → 表格编辑器（name / returns / arguments / description）

**端口属性面板**：
- `type` → 增加类型选择器（引用类型系统）
- `category` → 下拉框增加 `internal` 选项

**连接属性面板**：
- `transform` → 文本框
- `description` → 文本框（已有）

**修改文件**：
- `frontend/src/ui/property-panel.ts`

---

## 四、后端知识合并 Pipeline 改进

### 4.1 正式化 7 层知识合并算法

**现状**：知识合并逻辑在 `backend/aaa/merge_knowledge.py` 中（实验性），未集成到 Web API。与 `frontend/src/core/knowledge-merger.ts`（仅做模板拼接）的功能不重叠。

**需求描述**：将 7 层知识合并算法集成到后端 API，作为 build pipeline 的核心步骤。

**7 层模型**：
```
LAYER 0 — 语言模板（templates/<lang>/template.md）
  共享的编码规范、语法模式、常见 pitfalls（如 BSV 的 valueOf、禁止 Verilog 语法）
  
LAYER 1 — 项目级知识（project.yaml + system_knowledge.md）
  项目描述、目标语言、可用库、项目特定约束
  
LAYER 2 — 模块接口（meta.name + ports + methods）
  外部端口、方法签名、包名
  
LAYER 3 — 模块行为知识（meta.knowledge + provisos + signals）
  实现算法、类型约束、内部信号
  
LAYER 4 — 子模块接口契约（子模块的 ports + methods + provisos，不含 behavioral knowledge）
  实例化模板、参数绑定、派生 provisos
  
LAYER 5 — 连接计算描述（connections with transforms）
  信号→信号的数据流，位操作变换描述
  
LAYER 6 — 完整 Proviso 闭包
  自有 provisos + 子模块派生 provisos（NumAlias 过滤、常量过滤、去重）
  
LAYER 7 — Import 指导
  决策表 + 信号类型分析（非知识文本关键词匹配）+ 子模块包导入提醒
```

**修改文件**：
- `backend/aaa/merge_knowledge.py` → 移入 `backend/services/knowledge_merge.py`（正式化）
- `backend/api/build.py` → 增加 `/build/merge-knowledge` API 端点
- `frontend/src/core/knowledge-merger.ts` → 保留前端轻量模板变量替换功能

### 4.2 Proviso 传播与过滤

**需求描述**：知识合并脚本须实现以下 proviso 处理逻辑：

1. **参数替换**：子模块 provisos 中的形参替换为父模块传入的实参
2. **NumAlias 过滤**（P14）：`NumAlias#(...)` 条目不传播到父模块（本地别名，传播导致命名冲突）
3. **常量过滤**（P15）：仅含常量数值的 proviso（如 `Add#(1, _, 2)`）不传播（会导致 BSV 求解器推导出错误约束）
4. **去重**：同名同参 proviso 只保留一份

**修改文件**：
- `backend/services/knowledge_merge.py`

### 4.3 Import 分析改为类型驱动

**现状问题 (P18)**：当前 import 分析对 `meta.knowledge` 文本做关键词匹配（如检测 "FIFOF" → 推荐 `import FIFOF::*`），但知识文本提到 FIFOF 仅作为假设性描述（"完整实现会用到 FIFOF"），导致误推荐。

**需求描述**：Import 分析仅基于：
1. `signals[].type` 中出现的类型名（如 `FIFOF#(T)` → 需要 `import FIFOF::*`）
2. `nodes[].ref` 引用的子模块名（需要 `import ChildPackage::*`）
3. `methods[].returns` 和 `methods[].arguments[].type` 中使用的类型

不再对 `meta.knowledge` 文本做关键词匹配。

**修改文件**：
- `backend/services/knowledge_merge.py`：LAYER 7 逻辑

### 4.4 模块命名规范化

**现状问题 (P17)**：YAML `meta.name` 使用 snake_case（`priority_encoder`），合并脚本直接拼接 `mk{module_name}` 产生 `mkpriority_encoder`，但 BSV 模块名应为 PascalCase（`mkPriorityEncoder`）。

**需求描述**：合并脚本在生成模块名时，将 snake_case 转为 PascalCase。

**规则**：`"priority_encoder"` → 按下划线分词 `["priority", "encoder"]` → 每词首字母大写 `["Priority", "Encoder"]` → 拼接 `"PriorityEncoder"` → 加前缀 `"mkPriorityEncoder"`

**修改文件**：
- `backend/services/knowledge_merge.py`

### 4.5 语言模板分离

**现状问题 (P4)**：BSV 编程规范写在每个项目的 `system_knowledge.md` 中，导致重复和不一致。

**需求描述**：在项目根目录或全局配置目录创建 `templates/<language>/` 目录结构：
```
templates/
  bluespec_sv/
    template.md     # BSV 语法、proviso 模式、常见 pitfalls
    types.yaml      # 内置类型定义
  verilog/
    template.md
    types.yaml
```

`project.yaml` 中通过 `properties.target: "bluespec_sv"` 指定使用哪个语言模板。

**模板内容应包括**：
- 模块/接口语法
- 函数定义语法
- 包结构
- 数字类型约束（provisos）
- 位操作 provisos（truncate, zeroExtend, concatenate）
- **Import 决策表**（何时需要哪个包）
- **常见 pitfalls**：
  - `valueOf(reqNum)` 用于值级位选择，`reqNum` 仅用于类型表达式
  - BSV 整数直接写 `0`、`1`，不是 Verilog 的 `1'b0`、`1'b1`
  - 轻量级模块语法（无内部状态时方法可直接写在 module 体中）

### 4.6 构建 API 增强

**需求描述**：`/build` API 接受以下参数扩展：

```json
{
  "scope": "single",        // single | tree | full
  "mode": "fresh",          // fresh | incremental
  "target_module": "top/arbiter_tree.yaml",
  "merge_knowledge": true,  // 是否使用多层知识合并
  "include_testbench": false
}
```

当 `merge_knowledge: true` 时，后端先运行知识合并生成最终 prompt，再调用 LLM agent。

**依赖顺序**：构建时应按依赖拓扑序（叶子→根）逐个生成，每个模块生成后编译验证，再生成依赖它的父模块。

---

## 五、知识组织模型定义

### 5.1 知识层级

```
Level 0 — 语言模板 (Language Template)
  位置: templates/<lang>/template.md + types.yaml
  内容: 语法规范、编码约定、常见 pitfalls、导入决策表、内置类型
  作用域: 所有同语言项目共享
  示例: BSV 的 module 语法、valueOf 陷阱、proviso 模式

Level 1 — 项目知识 (Project Knowledge)
  位置: <project>/project.yaml + system_knowledge.md
  内容: 项目描述、目标语言、可用库、项目特定约束
  作用域: 单个 project 内所有模块
  示例: blue-rdma 项目中可用的 PAClib、PrimUtils 库

Level 2 — 模块知识 (Module Knowledge)
  位置: <module>.yaml 的 meta + ports + signals + methods + provisos
  内容: 模块行为描述、接口契约、内部信号、类型约束
  作用域: 当前模块及其子模块（子模块仅获取接口契约部分）
  示例: mkRoundRobinArbiter 的轮询仲裁算法

Level 3 — 子模块接口契约 (Child Interface Contract)
  位置: 知识合并时从子模块 YAML 提取
  内容: 子模块的外部 ports + methods + 派生 provisos（不含 behavioral knowledge）
  作用域: 父模块的生成 prompt
  示例: ArbiterTree 看到的 RoundRobinArbiter 仅有 grant() 方法签名和端口
```

### 5.2 知识合并模式

| 模式 | 用途 | 合并范围 |
|------|------|---------|
| `generate` | 生成新代码 | L0 → L1 → L2（当前模块）→ L3（子模块接口） |
| `review` | 审查已有代码 | generate 的所有层 + 子模块 behavioral knowledge + 已生成代码 |
| `test` | 生成测试 | generate 的所有层 + test_method 字段 |

### 5.3 知识共享规则

| 规则 | 说明 |
|------|------|
| 不重复原则 | 语言通用知识写在 L0 模板中，项目特定知识写在 L1，模块专有知识写在 L2 |
| 接口隔离 | L3 仅包含子模块的接口契约，不泄露实现细节 |
| 知识下沉 | 多个子模块共享的知识（如协作协议）写到父模块的 knowledge 中 |
| 知识上升 | 项目内通用的约定（如命名规范）写到 system_knowledge.md 中 |

---

## 六、连接校验增强

### 6.1 方向校验

**现状问题 (P7)**：不验证 source port 和 target port 的方向兼容性。

**需求描述**：`ConnectionValidator` 增加方向检查：
- `output` → `input` ✅
- `output` → `output` ❌
- `input` → `input` ❌
- `input` → `output` ❌
- signal 作为中转：`*` → signal → `*` ✅（signal 两侧方向均允许）

### 6.2 类型传播校验

**描述**：当连接带 `transform` 时，验证 transform 的输入类型、输出类型与源端口、目标端口兼容。

**示例**：`truncate(Bit#(reqNum))` → `Bit#(TDiv#(reqNum, 2))` → 目标端口类型应为 `Bit#(TDiv#(reqNum, 2))`。

具体校验逻辑可通过配置开关控制（初期可仅做 warning 不做 blocking）。

---

## 七、实施优先级建议

### P0（阻塞性 — 影响基本功能）
1. **3.2 + 3.1**：ConnectionTarget 支持 signal → 修复连接无法显示
2. **2.1**：新增 signals 节 → 消除 self.xxx 歧义

### P1（高优先级 — 实验验证需要）
3. **4.1**：正式化 7 层知识合并 → build pipeline 可用
4. **2.3 + 4.2**：provisos 节 + 传播过滤 → 修复编译失败
5. **4.5**：语言模板分离 → 知识去重

### P2（中优先级 — 体验完善）
6. **2.4**：nodes 增加 parameters 字段
7. **2.5**：端口类型参数化
8. **3.3**：连接线显示 transform 标签
9. **4.3**：Import 分析改为类型驱动
10. **3.5**：属性面板扩展（signals/methods/provisos 编辑器）

### P3（优化项 — 长期质量）
11. **3.4**：类型系统增强（参数化类型兼容性）
12. **6.1 + 6.2**：连接校验增强
13. **4.6**：构建 API 增强（依赖顺序、增量模式）
14. **2.6**：端口 category 扩展 internal
15. **2.7**：连接 transform 字段标准化
16. **4.4**：模块命名规范化

---

## 八、修改文件清单汇总

### 新增文件
| 文件 | 说明 |
|------|------|
| `frontend/src/nodes/signal-node.ts` | Signal 节点类型注册 |
| `templates/bluespec_sv/template.md` | BSV 语言模板（从各项目 system_knowledge.md 提炼） |
| `templates/bluespec_sv/types.yaml` | BSV 内置类型定义 |
| `backend/services/knowledge_merge.py` | 正式化 7 层知识合并服务 |

### 修改文件
| 文件 | 涉及需求 |
|------|---------|
| `frontend/src/types/graph-types.ts` | 2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 3.2, 3.3 |
| `frontend/src/core/graph-manager.ts` | 3.1, 3.2, 3.3 (_addConnection_, toYAML, _populateGraph) |
| `frontend/src/core/connection-validator.ts` | 3.2, 6.1, 6.2 |
| `frontend/src/core/type-system.ts` | 3.4 |
| `frontend/src/core/knowledge-merger.ts` | 4.1（保留前端轻量功能） |
| `frontend/src/nodes/boundary-nodes.ts` | 3.1（可能需要配合 signal 节点刷新） |
| `frontend/src/nodes/rtl-module.ts` | 3.5（属性编辑） |
| `frontend/src/ui/property-panel.ts` | 3.5 |
| `frontend/src/ui/type-editor.ts` | 3.4 |
| `backend/api/build.py` | 4.6 |
| `backend/api/graph.py` | 4.1（增加 merge-knowledge 端点） |
| `backend/app.py` | 4.1（注册新路由） |
| `backend/services/llm_agent.py` | 4.6（接收合并后的 prompt） |

---

## 九、测试验证标准

完成迭代后，使用以下测试用例验证：

1. **连接渲染测试**：加载 `nested_v2/top/pipelined_arbiter.yaml`，验证所有 5 条连接均正确显示（当前仅 1 条能显示）
2. **Signal 节点测试**：在画布上创建/删除 signal 节点，验证连线正确
3. **Transform 显示测试**：验证带 transform 的连接在连线上显示标签
4. **知识合并测试**：对 nested_v2 4 层模块分别调用知识合并 API，验证输出 prompt 正确性
5. **Proviso 闭包测试**：验证 ArbiterTree 的合并 prompt 不包含 NumAlias 和常量 provisos
6. **编译回归测试**：使用合并后的 prompt 重新生成 4 个 BSV 模块，验证全部编译通过
7. **Import 最小化测试**：验证 PriorityEncoder 生成代码零 imports，RoundRobinArbiter 仅 import PriorityEncoder
