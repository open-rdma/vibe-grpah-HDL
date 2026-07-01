# 软件迭代优化需求文档

> 基于 nested_v1 / nested_v2 多层级知识合并实验及前后端框架审查，整理出的迭代优化需求。
> 日期：2026-07-01
> 修订：根据用户反馈，移除 signals 预定义，重新设计语言无关的类型系统

---

## 一、问题总览

通过两轮实验（nested_v1 3层3模块、nested_v2 4层4模块），共发现 **20 个问题**，其中：

- **前端图形渲染**：连接格式不兼容、缺少类型可视化
- **YAML 数据格式**：类型定义绑定特定 RTL 语言语法、缺少 methods/provisos 等结构化字段
- **后端知识合并**：知识重复、proviso 传播、import 分析、命名规范等
- **知识组织模型**：缺少语言模板层、知识层级混乱、子模块知识泄露

详细问题清单见 `deli_auto_iters/nested_v1/state/problems_and_design.md` 和 `deli_auto_iters/nested_v2/state/findings_and_results.md`。

---

## 二、类型系统设计（核心新增）

### 设计原则

**类型 ID 是自然语言描述的"唯一标识符"，不是真实的数据类型。** 类型定义只起到标签的作用——用户用自然语言描述一个数据类型的大致样子，给这个描述起一个唯一的名字（类型 ID），然后在其他地方引用这个名字。具体的目标 RTL 语言类型由大模型在生成阶段负责翻译。

核心原则：
1. **语言无关**：YAML 中不出现任何目标 RTL 语言的语法（如 `Bit#(N)`、`logic[7:0]` 等）
2. **描述驱动**：每个类型用自然语言描述其数据结构，类型 ID 只是这段描述的"标签"
3. **端口必显式**：模块端口涉及跨模块连线类型检查，必须引用显式的类型 ID
4. **两步生成**：先翻译类型定义到目标语言，再引用翻译后的类型生成代码

### 2.1 类型定义格式

类型统一定义在项目的类型文件（如 `types.yaml`）中，每个类型包含：

```yaml
types:
  - id: "request_vector"
    description: >
      一个位宽为 reqNum 的向量，每个 bit 对应一个请求客户端。
      bit 0 具有最高优先级。reqNum 是模块的泛型参数，由上层实例化时指定。
    category: "vector"
    
  - id: "grant_result"
    description: >
      与 request_vector 位宽相同的 one-hot 向量，只有一个 bit 为 1，
      表示被授予访问权限的客户端。
    category: "vector"
    
  - id: "priority_state"
    description: >
      一个可读写的寄存器，存储当前优先级掩码。
      位宽与 request_vector 相同。每个 cycle 可以更新。
      初始值为全 0（无请求被屏蔽）。
    category: "register"
    
  - id: "half_width_vector"
    description: >
      位宽为 reqNum/2（向上取整）的向量。用于将原始请求向量
      拆分后的子向量。基础类型与 request_vector 相同。
    category: "vector"
    
  - id: "two_bit_vector"
    description: >
      固定位宽为 2 的向量，用于表示两个子仲裁器的结果。
    category: "vector"
```

**字段说明**：
| 字段 | 必填 | 说明 |
|------|------|------|
| id | 是 | 类型的唯一标识符，在项目内唯一。命名应语义化（如 `request_vector`，而非 `Bit_N`） |
| description | 是 | 自然语言描述，说明数据结构、位宽、字段含义、约束等。这是大模型翻译类型的唯一依据 |
| category | 否 | 大类标签：`vector`、`register`、`struct`、`enum`、`fifo`、`pipeline` 等。辅助前端分类展示 |

### 2.2 端口引用类型 ID

模块端口不再直接写类型表达式，而是引用类型 ID：

```yaml
ports:
  - name: "reqVec"
    direction: "input"
    type: "request_vector"       # 引用类型 ID，而非 Bit#(reqNum)
    description: "来自上游的请求向量"
    
  - name: "grantVec"
    direction: "output"
    type: "grant_result"         # 引用类型 ID
    description: "仲裁结果，one-hot 编码"
```

连接校验时：两端端口引用了相同的 type ID → 类型兼容 ✅；引用了不同的 type ID → 类型不兼容 ❌（除非显式标记 `allow_cross_domain: true` 或有 transform 说明）。

### 2.3 两步生成流程

使用大模型生成 RTL 时，分两步执行：

**步骤 1 — 类型翻译**：
- 扫描项目中所有被引用的类型定义（`types.yaml` 中的条目）
- 将自然语言描述翻译为目标 RTL 语言的具体类型定义
- 输出中间产物（如 `typedefs.bsv`、`typedefs.vh` 等）
- 例如：`request_vector` → `typedef Bit#(reqNum) RequestVector;`

**步骤 2 — 模块代码生成**：
- 大模型引用步骤 1 中已经翻译好的类型定义
- 在生成模块代码时，端口类型直接使用翻译后的类型名
- 内部信号类型由大模型根据功能描述自行决定（用户不预定义内部信号）

```text
生成流程:
  项目 YAML + types.yaml
    → [Step 1: LLM 翻译类型] → typedefs.bsv (目标语言类型文件)
    → [Step 2: LLM 生成模块] → 各模块 .bsv 文件 (引用 typedefs.bsv 中的类型)
```

---

## 三、YAML 数据格式修改

### 3.1 （移除）不再添加 `signals` 节

**原方案**：在 YAML 中新增 `signals` 节，让用户预定义模块内部信号（名称、类型、初始值等）。

**用户反馈**：内部信号应该是大模型在理解用户自然语言描述的意图后，自己生成的。如果要求用户提前想清楚内部信号设计，就是给用户增加了工作量，削弱了大模型的主观能动性。

**修改方案**：
- 删除原 2.1 节的 signals 新增需求
- 内部信号完全由大模型在生成代码时自行推断和设计
- 如果用户对具体实现方式有特殊要求（如 "必须用寄存器打一拍"），应在模块的功能描述（`meta.knowledge`）中以自然语言描述，而不是要求用户结构化定义信号
- 连接关系只描述模块端口之间的数据流向，不深入到内部信号级别

**连带删除**：
- 原 2.6 节（端口增加 `internal` category）— 无内部端口概念后不再需要
- 原 3.1 节（Signal 节点类型）— 前端不需要表示内部信号节点
- 原 3.2 节中 ConnectionTarget 的 `signal` 字段 — 连接只发生在模块端口之间

### 3.2 新增 `methods` 节（方法签名声明）

**现状问题 (P13)**：connections 引用 port 名称，但目标代码中使用 method 名称，两端无显式映射。

**需求描述**：在 YAML 顶层新增 `methods` 字段，显式声明接口方法签名及其与端口的映射。

**数据格式**：
```yaml
methods:
  - name: "grant"
    description: "接收请求向量，返回 one-hot 授权结果，同时更新内部优先级状态"
    arguments:
      - name: "reqVec"
        type: "request_vector"
    returns: "grant_result"
    maps_to_port: "grantVec"
```

**字段说明**：
| 字段 | 必填 | 说明 |
|------|------|------|
| name | 是 | 方法名称 |
| description | 否 | 方法功能描述 |
| arguments | 否 | 参数列表，每项含 name + type（引用类型 ID） |
| returns | 是 | 返回值类型（引用类型 ID） |
| maps_to_port | 否 | 关联的输出端口名 |

### 3.3 `provisos` 节改为自然语言约束

**现状问题 (P8)**：provisos 以 BSV 语法写在 `meta.knowledge` 中（如 `Add#(1, _, reqNum)`），合并脚本无法解析传播。且语法绑定 BSV，违反语言无关原则。

**修改方案**：provisos 以自然语言描述约束条件，而非写 BSV 类型表达式。

**变更前**（绑定 BSV 语法）：
```yaml
provisos:
  - "Add#(1, _, reqNum)"
  - "NumAlias#(TLog#(reqNum), logReqNum)"
```

**变更后**（自然语言约束）：
```yaml
provisos:
  - "reqNum 至少为 1（即模块至少处理 1 个请求客户端）"
  - "logReqNum 定义为 ceil(log2(reqNum))，即表示 reqNum 所需的位数"
```

这些自然语言约束在知识合并时随子模块接口传递给父模块（作为 LAYER 4 的一部分）。合并脚本不再做字符串替换式的 proviso 传播，而是：
- 将子模块的约束描述原文传递给父模块
- 同时传递父模块对子模块的参数绑定（自然语言描述）
- 由大模型在生成父模块代码时，理解和推导完整的约束集合

### 3.4 nodes 节点新增 `parameters` 字段

**现状问题 (P1)**：类型参数通过 `properties` 传递，合并脚本无法区分类型参数和自定义属性。

**修改方案**：在 `nodes[]` 中新增 `parameters` 字段，与 `properties` 分离。参数值使用自然语言描述，不绑定特定 RTL 语法。

**数据格式**：
```yaml
nodes:
  - id: "left_arb_inst"
    ref: "library/round_robin_arbiter/round_robin_arbiter.yaml"
    description: "负责处理低半部分请求的轮询仲裁器"
    parameters:
      reqNum: "父模块 reqNum 的一半（向上取整）"
    properties: {}
```

**语义区分**：
- `parameters`：类型/泛型参数绑定，影响子模块的实例化方式。由大模型理解后决定具体的目标语言写法
- `properties`：用户自定义键值对，透传到生成 prompt（如 `clock_freq_mhz: "200"`）

### 3.5 连接增加 `transform` 和 `description` 字段

**现状问题 (P11)**：连接描述位操作（如拆分、合并、截断）只在 description 中以自然语言存在，不够结构化。

**修改方案**：`Connection` 接口保留 `description` 字段用于描述数据变换，连接之间引用显式的类型 ID 以便做类型推导。

**数据格式**：
```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    to: [{ node: "left_arb_inst", port: "reqVec" }]
    description: >
      取 reqVec 的低半部分（bit[reqNum/2-1:0]），
      送给左子仲裁器处理。使用截断操作提取低位。
      from 类型: request_vector, to 类型: half_width_vector
```

连接只发生在有明确类型 ID 的模块端口之间（graph_input、graph_output、子模块实例）。不出现 `self.xxx` 或 `signal: xxx` 引用。

---

## 四、前端图形渲染改进

### 4.1 （移除）不再新增 Signal 节点

原方案 B 中规划的 `rtl/signal` 节点类型不再需要。内部信号由大模型自行生成，不在画布上表示。

### 4.2 连接线显示 description 标签

**需求描述**：当 connection 有 `description` 字段时，在画布连接线上以标签形式展示。

**实现方式**：
- 利用 LiteGraph 的 link 渲染钩子
- 标签内容截取 description 的前若干字（如首 30 字符）
- 鼠标悬停显示完整 description
- 标签字体小号、灰色、置于连线中点

**修改文件**：
- `frontend/src/nodes/rtl-module.ts` 或新建 link renderer
- `frontend/src/types/graph-types.ts`：`Connection` 类型确认 `description` 字段

### 4.3 类型系统前端增强

**需求描述**：将类型系统从"简单的字符串相等比较"升级为"类型 ID 驱动的类型注册与引用系统"。

**核心变更**：
1. 类型编辑器支持按项目加载/编辑类型定义（自然语言描述 + 类型 ID）
2. 端口属性面板中，端口 type 字段改为类型 ID 下拉选择器（从 types.yaml 加载）
3. 兼容性检查：两端端口引用相同 type ID → 兼容；否则不兼容
4. 不在前端做参数化类型的包含关系判断（这属于大模型的职责）

**Visual Design**：
- 类型编辑器可展示为两栏布局：左边类型 ID 列表，右边自然语言描述编辑区
- 支持新增/编辑/删除类型定义
- 端口配置时，type 字段显示为下拉搜索框，可快速筛选已定义的类型

**修改文件**：
- `frontend/src/core/type-system.ts`
- `frontend/src/ui/type-editor.ts`
- `frontend/src/ui/property-panel.ts`
- `frontend/src/types/graph-types.ts`

### 4.4 属性面板扩展

**需求描述**：属性面板增加以下可编辑区域：

**模块（Graph）属性面板**：
- `meta.knowledge` → Markdown 多行文本框
- `provisos` → 字符串列表编辑器（自然语言约束）
- `methods` → 表格编辑器（name / description / arguments / returns / maps_to_port）

**节点（Node）属性面板**：
- `parameters` → 键值对编辑器（参数名 → 自然语言描述）
- `description` → 文本区
- 端口列表 → 只读表格，type 列显示类型 ID

**端口（Port）属性面板**：
- `type` → 下拉搜索框，引用类型系统的类型 ID
- `direction` → 下拉框（input/output）
- `description` → 文本框

**连接（Connection）属性面板**（新增 — 点击连线时显示）：
- `from` / `to` → 只读
- `description` → 文本框（描述数据传输/变换）

**修改文件**：
- `frontend/src/ui/property-panel.ts`

---

## 五、后端知识合并 Pipeline 改进

### 5.1 正式化多层知识合并算法

**现状**：知识合并逻辑在实验脚本中（`deli_auto_iters/nested_v2/merge_knowledge.py`），未集成到 Web API。

**需求描述**：将知识合并算法移入 `backend/services/`，作为 build pipeline 的核心步骤。

**合并层级**（修订版，移除 signals 层）：

```
LAYER 0 — 语言模板
  位置: templates/<lang>/template.md
  内容: 语法规范、编码约定、常见 pitfalls、导入决策表
  作用域: 所有同语言项目共享
  示例: BSV 的 module/endmodule 语法、valueOf 陷阱、禁止 Verilog 语法

LAYER 1 — 项目知识
  位置: <project>/project.yaml + system_knowledge.md
  内容: 项目描述、目标语言、可用库、项目特定约束
  作用域: 单个 project 内所有模块

LAYER 2 — 模块接口
  内容: meta.name、ports（引用类型 ID）、methods（签名+描述）
  来源: 当前模块 YAML

LAYER 3 — 模块行为知识
  内容: meta.knowledge（实现算法） + provisos（自然语言约束）
  来源: 当前模块 YAML
  注意: 不包含预定义的内部信号——内部信号由大模型自行生成

LAYER 4 — 子模块接口契约
  内容（每个子模块）:
    - 子模块名 + 功能描述
    - 外部端口列表（引用类型 ID）
    - 方法签名
    - 自然语言约束（provisos）
    - 参数绑定说明（父模块传入的参数值，自然语言描述）
    - 实例化说明
  注意: 不包含子模块的行为知识（meta.knowledge）——接口隔离

LAYER 5 — 连接计算描述
  内容: 模块端口之间的数据流描述、变换说明
  来源: 当前模块 YAML 的 connections + description

LAYER 6 — 约束汇总
  内容: 模块自身约束 + 子模块约束（原文传递） + 连接引入的约束
  由大模型在生成时理解和推导完整的约束集合
  合并脚本不做字符串替换式传播

LAYER 7 — Import 指导
  内容: 决策表 + 子模块包导入提醒
  基于信号类型分析（非知识文本关键词匹配）
```

**修改文件**：
- `backend/services/knowledge_merge.py`（新建，从 `deli_auto_iters/nested_v2/merge_knowledge.py` 移植并修改）
- `backend/api/build.py`：集成知识合并

### 5.2 约束（Proviso）处理改为自然语言传递

**修订**：原方案要求合并脚本做参数替换式的 proviso 传播。修改为：

1. 子模块的 provisos（自然语言描述）原文传递给父模块
2. 附加父模块对子模块的参数绑定说明（自然语言）
3. 由大模型在生成父模块代码时，综合理解和推导完整约束
4. 合并脚本负责收集和呈现，不负责"推导"

如此设计的原因：
- 自然语言约束无法做机械的字符串替换
- 约束推导是语义理解任务，适合由大模型完成
- 保持合并脚本的简单性和语言无关性

### 5.3 Import 分析改为类型驱动

**现状问题 (P18)**：对 `meta.knowledge` 文本做关键词匹配产生假阳性（如 "完整实现会用到 FIFOF" → 误推荐 `import FIFOF::*`）。

**修改方案**：Import 分析仅基于：
1. Ports 中引用的类型 ID → 查找该类型定义的 category → 如 `fifo` category → 推荐 FIFOF 相关导入
2. `nodes[].ref` 引用的子模块名 → 推荐 `import ChildPackage::*`
3. `methods[].returns` 和 `methods[].arguments[].type` 中引用的类型 ID

不再对 `meta.knowledge` 文本做关键词匹配。

**修改文件**：
- `backend/services/knowledge_merge.py`：LAYER 7 逻辑

### 5.4 模块命名规范化

**现状问题 (P17)**：YAML `meta.name` 使用 snake_case，合并脚本直接拼接产生 `mkpriority_encoder` 而非 `mkPriorityEncoder`。

**修改方案**：合并脚本将 snake_case 转为 PascalCase：
- `"priority_encoder"` → `["priority", "encoder"]` → 首字母大写 → `"PriorityEncoder"` → `"mkPriorityEncoder"`

**修改文件**：
- `backend/services/knowledge_merge.py`

### 5.5 语言模板目录结构

```
templates/
  bluespec_sv/
    template.md        # BSV 语法、proviso 模式、常见 pitfalls
  verilog/
    template.md
    types.yaml
  systemc/
    template.md
```

`project.yaml` 中通过 `target_language: "bluespec_sv"` 指定模板。

**模板内容**：
- 模块/接口/包语法
- 类型翻译指导（如何将自然语言类型描述映射为 BSV 类型）
- 常见 pitfalls（valueOf、禁止 Verilog 语法、轻量级模块规则）
- Import 决策表（何时导入哪个包）
- 约束推导指导（如何从自然语言约束推导 BSV provisos）

### 5.6 构建 API 支持两步生成

**需求描述**：`/build` API 支持两步生成流程：

```json
{
  "scope": "full",
  "mode": "fresh",
  "target_module": "top/arbiter_tree.yaml",
  "merge_knowledge": true,
  "include_testbench": false,
  "two_phase": true
}
```

当 `two_phase: true` 时：
1. **Phase 1 — 类型翻译**：扫描项目所有被引用的类型定义 → 调用 LLM 翻译 → 生成 `typedefs.bsv`（或其他目标语言的类型文件）
2. **Phase 2 — 模块生成**：按依赖拓扑序（叶子→根），逐个生成模块代码，每个模块引用 Phase 1 的类型文件

**依赖顺序**：按拓扑序从叶子到根逐个生成，每层生成后编译验证，再生成上层模块。

---

## 六、知识组织模型

### 6.1 知识层级（修订版）

```
Level 0 — 语言模板 (Language Template)
  位置: templates/<lang>/template.md
  内容: 语法规范、编码约定、常见 pitfalls、导入决策表、类型翻译指导
  作用域: 所有同语言项目共享

Level 1 — 项目知识 (Project Knowledge)
  位置: <project>/project.yaml + system_knowledge.md + types.yaml
  内容: 项目描述、目标语言、可用库、项目特定约束、类型定义（自然语言描述）
  作用域: 单个 project 内所有模块

Level 2 — 模块接口契约 (Module Interface Contract)
  位置: <module>.yaml 的 meta.name + ports + methods
  内容: 模块名称、端口（引用类型 ID）、方法签名
  作用域: 当前模块 + 父模块（父模块看到子模块的此层）

Level 3 — 模块行为知识 (Module Behavioral Knowledge)
  位置: <module>.yaml 的 meta.knowledge + provisos
  内容: 实现算法描述、自然语言约束、特殊实现要求
  作用域: 仅当前模块（不传递给父模块）
```

### 6.2 知识合并模式

| 模式 | 用途 | 合并范围 |
|------|------|---------|
| `generate` | 生成新代码 | L0 → L1 → L2（当前模块）→ L3（当前模块）→ 子模块 L2（接口契约） |
| `incremental` | 增量更新 | generate 的所有层 + 已生成的代码 |
| `test` | 生成测试 | generate 的所有层 + test_method 字段 |

### 6.3 知识共享规则

| 规则 | 说明 |
|------|------|
| 不重复原则 | 语言通用知识在 L0 模板，项目特定知识在 L1，模块专有知识在 L2/L3 |
| 接口隔离 | 父模块仅获取子模块的 L2（接口契约），不获取 L3（行为知识/实现细节） |
| 知识下沉 | 多个子模块需要共享的知识（如协作协议）写到父模块的 L3 中 |
| 知识上升 | 项目内通用的约定写到 system_knowledge.md（L1） |

---

## 七、连接校验增强

### 7.1 方向校验

**现状问题 (P7)**：不验证 source port 和 target port 的方向兼容性。

**需求描述**：`ConnectionValidator` 增加方向检查：
- `output` → `input` ✅
- `output` → `output` ❌
- `input` → `input` ❌
- `input` → `output` ❌

### 7.2 类型 ID 匹配校验

**描述**：连接两端的端口引用相同 type ID → 类型兼容 ✅。引用不同 type ID → 不兼容 ❌。

宽松规则：如果连接带 `description` 字段描述了类型变换（如 "截取低半部分"），则可允许连接不同类型 ID 的端口（warning 而非 blocking）。

---

## 八、实施优先级

### P0（阻塞级 — 影响基本功能）
1. **类型系统设计**（第二章）：类型 ID + 自然语言描述，定义在 types.yaml
2. **端口类型改为引用类型 ID**（3.2 节配合）：端口 type 字段引用类型系统的 ID

### P1（高优先级 — 实验验证需要）
3. **5.1 + 5.5**：正式化多层知识合并 + 语言模板分离
4. **3.3 + 5.2**：provisos 改为自然语言约束 + 自然语言传递
5. **3.4**：nodes 增加 parameters 字段（自然语言描述）

### P2（中优先级 — 体验完善）
6. **4.3**：类型系统前端增强（类型 ID 选择器）
7. **3.2**：新增 methods 节
8. **4.2**：连接线显示 description 标签
9. **5.3**：Import 分析改为类型驱动
10. **4.4**：属性面板扩展（methods/provisos/parameters 编辑器）

### P3（优化项 — 长期质量）
11. **5.6**：构建 API 支持两步生成
12. **7.1 + 7.2**：连接校验增强
13. **5.4**：模块命名规范化
14. **3.5**：连接 description 字段标准化

---

## 九、修改文件清单汇总

### 新增文件
| 文件 | 说明 |
|------|------|
| `backend/services/knowledge_merge.py` | 正式化多层知识合并服务（含两步生成协调逻辑） |
| `templates/bluespec_sv/template.md` | BSV 语言模板（类型翻译指导 + 语法 + pitfalls + 约束推导指导） |

### 修改文件
| 文件 | 涉及需求 |
|------|---------|
| `frontend/src/types/graph-types.ts` | 类型定义 TypeDefinition 结构更新（id + description + category），PortData 的 type 改为引用类型 ID，GraphData 增加 methods/provisos，GraphNodeData 增加 parameters，Connection 增加 description 字段 |
| `frontend/src/core/graph-manager.ts` | toYAML / _populateGraph / _addConnection 适配新数据格式 |
| `frontend/src/core/type-system.ts` | 从"字符串比较"升级为"类型 ID 注册与查询系统" |
| `frontend/src/core/connection-validator.ts` | 方向校验 + 类型 ID 匹配校验 |
| `frontend/src/core/knowledge-merger.ts` | 保留前端轻量模板变量替换 |
| `frontend/src/ui/property-panel.ts` | 增加 methods/provisos/parameters 编辑区域；端口 type 改为类型 ID 选择器；新增连线属性面板 |
| `frontend/src/ui/type-editor.ts` | 支持编辑自然语言类型描述 |
| `frontend/src/nodes/rtl-module.ts` | 适配 properties → parameters 分离、连接线 description 标签渲染 |
| `frontend/src/nodes/boundary-nodes.ts` | 适配端口 type 为类型 ID |
| `backend/api/build.py` | 两步生成支持、知识合并集成 |
| `backend/api/graph.py` | 增加 merge-knowledge 端点 |
| `backend/app.py` | 注册新路由 |
| `backend/services/llm_agent.py` | 接收合并后的 prompt |
| `backend/services/file_manager.py` | 可能需要支持 types.yaml 读写 |

---

## 十、测试验证标准

完成迭代后，使用以下测试用例验证：

1. **类型系统测试**：在 types.yaml 中定义若干类型，验证前端端口配置可下拉选择类型 ID，验证同 ID 端口可连线、不同 ID 端口不可连线
2. **连接渲染测试**：加载嵌套模块图，验证所有模块端口之间的连接正确显示（不再出现 `self.xxx` 或 `signal:` 引用）
3. **Description 标签测试**：验证带 description 的连接在连线上显示截断标签，悬停展示全文
4. **两步生成测试**：对一个多层级项目执行两步生成，验证 Phase 1 生成类型文件、Phase 2 引用类型文件
5. **知识合并测试**：对 nested_v2 4 层模块调用知识合并 API，验证子模块行为知识不出现在父模块 prompt 中，验证约束以自然语言传递
6. **编译回归测试**：生成的代码全部编译通过，类型定义正确翻译为目标语言
7. **Import 最小化测试**：验证叶子模块零 imports，中层模块仅导入直接依赖的子模块包
