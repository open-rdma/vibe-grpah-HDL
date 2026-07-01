# 自然语言→RTL 编译器系统 功能需求规格


## 一、系统总目标

实现一种**由大语言模型作为核心能力的"自然语言→RTL的编译器"**。

输出目标语言包括 BluespecSystemVerilog、SystemVerilog、VHDL、Chisel 等。两个核心问题：

1. **这个编译器的输入数据是什么格式的？**
2. **这个编译器的内部运作流程是什么样子的？**

---

## 二、三部分架构

工程由 **backend、frontend、compiler**三部分组成，其中 **compiler 是最重要的核心**。

| 部分 | 职责 |
|------|------|
| **compiler** | 核心逻辑，把"图 + 自然语言"的 YAML 文件系统输入转换为目标语言的 RTL 代码 |
| **frontend** | 可视化界面，通过拖拽等方式生成 compiler 所需要的 YAML 文件系统。使用 litegraph.js 作为图形编辑框架，TypeScript 编写，Vite 构建为静态页面 |
| **backend** | Python (Flask) 服务端，粘合 compiler 和 frontend。对外提供静态页面服务，响应浏览器操作，管理 YAML 文件系统，调用 compiler 进行编译。同时提供项目文件读取、git 版本管理、通用编程 Agent 调用等 API |

技术栈：
- 前端：litegraph.js + TypeScript + Vite → 编译为静态 JS/CSS
- 后端：Python Flask，入口在 Python，不直接执行 npm
- LLM：OpenAI 优先，接口可扩展到其他 provider；可调用 Claude Code 作为 LLM Agent
- 构建：Makefile 自动完成前端构建

---

## 三、输入数据格式要求（YAML 文件系统）

### 3.1 核心思想

人类通过【**嵌套多层级的图结构 + 自然语言描述**】定义 RTL 项目的骨架和重要信息，大模型根据这些信息产出 RTL 代码和测试用例。

### 3.2 语言无关性（CRITICAL）

> "YAML 文件系统中应该是抽象的，不与任何具体目标 RTL 语言特性绑定的。"

YAML 结构字段必须是语言无关的。针对特定语言的指引写入对应层级的 `knowledge.<lang>` 的一些通用属性中（即应该留有添加属性或者自定义信息的机制，使之可以适应不同语言针对性描述的注入，而不需要为每种语言独立修改系统代码进行定制），不为某种语言单独增加结构字段。


### 3.3 文件组织模型（来自前端 IDE 需求）

YAML 是信息承载的基础方式，其文件组织需支持未来的可视化编辑环境（拖拽构建图）。以下需求来自前端 UI 的设计约束，直接影响 compiler 输入数据的组织形式。

#### 3.3.1 图与文件的一一对应

- 每个 graph 对应一个 YAML 数据文件（子 graph 也对应子数据文件）
- Graph 的层级结构对应文件系统目录结构
- 父图通过引用子图数据文件串接形成整个图

#### 3.3.2 工程与多树结构

一个工程是一套配置文件的合集。工程可定义为多个树：

| 树 | 用途 |
|----|------|
| **Top 树** | 对应传统 RTL 工程的 TOP 模块 |
| **Library 树** | 存储被引用的库模块，存在于特定 library 目录下 |
| **自定义树** | 用户可定义其他树 |

Top 和 Library 是约定俗成，非必须。一个模块可直接引用另一个子图的数据文件；原始子图变更时，所有引用等效变更。子图（yaml文件）之间允许递归引用。

#### 3.3.3 目录结构示意

```
project/
├── project.yaml              # 工程配置（目标语言、树定义、项目级知识）
├── types.yaml                # 类型定义注册表
├── top/                      # Top 树
│   ├── top_module.yaml       # 根模块
│   └── sub_module.yaml       # 子模块
├── library/                  # Library 树（被引用的库模块）
│   ├── fifo/
│   │   └── fifo.yaml
│   └── arbiter/
│       └── arbiter.yaml
└── generated/                # compiler 产出目录
    ├── typedefs.bsv
    ├── TopModule.bsv
    └── test/
```

---

## 四、YAML 数据格式详细设计

### 4.1 节点属性（来自 IDE 节点模型）

每个节点代表一个 RTL 模块，在 YAML 中需要承载以下信息：

| 字段 | 必填 | 说明 |
|------|------|------|
| `meta.name` | 是 | 模块名称 |
| `meta.description` | 是 | 功能描述字段。叶子节点：指导大模型生成 RTL 代码。子图节点：阐述子图间信号关系，同样指导生成子图 RTL 代码 |
| `meta.category` | 否 | 模块分类标签（combinational / sequential / interface 等） |
| `parameters` | 否 | 泛型/数值参数列表（name + kind + constraints） |
| `ports` | 否 | 端口列表（见 4.2） |
| `methods` | 否 | 方法签名声明（见 4.3） |
| `sub_interfaces` | 否 | 子接口列表（见 4.4） |
| `behavior` | 否 | 行为描述（state_elements + invariants + constraints） |
| `nodes` | 否 | 子模块实例化列表 |
| `connections` | 否 | 子模块间的连线列表 |
| `test_method` | 否 | 测试方法字段，指导大模型生成单元测试（激励生成逻辑、checker 逻辑等） |
| `properties` | 否 | 用户自定义键值对（透传到生成 prompt） |
| `knowledge.<lang>` | 否 | 语言特定的知识（imports、provisos、hints 等） |

编译器视角的关键约束：
- `meta.description` 是必填的核心字段——这是大模型理解模块意图的唯一入口
- `behavior` 中的内部信号描述由用户选择提供，具体信号由大模型自行生成
- `test_method` 描述激励和 checker 的逻辑，用于指导 testbench 生成

### 4.2 端口系统（来自 IDE 端口模型）

每个端口必须承载：

| 字段 | 必填 | 说明 |
|------|------|------|
| `name` | 是 | 端口名称 |
| `direction` | 是 | input / output |
| `type` | 是 | 引用 types.yaml 中定义的类型 ID |
| `description` | 否 | 端口的功能描述 |
| `properties` | 否 | 自定义属性 |

端口系统的关键设计约束（直接影响 compiler 的类型校验和连线逻辑）：

1. **端口类型引用类型 ID**，类型不同则禁止连线
2. **特殊端口类型**：复位信号、时钟信号需有标记
3. **时钟域**：端口需指定所属时钟域，不同时钟域的端口默认不可直接连接。可设置属性强制允许跨时钟域/跨复位域连接
4. **端口可自由添加、删除**，Subgraph 连接端口同理
5. **跨图连线**：连线穿越图边界时，路径上所有图都必须添加对应的端口，不能凭空跨越

### 4.3 方法签名（来自 IDE methods 模型）

显式声明接口方法签名及其与端口的映射：

```yaml
methods:
  - name: "grant"
    effect: "combinational"     # combinational / stateful / action
    description: "接收请求向量，返回 one-hot 授权结果"
    arguments:
      - name: "reqVec"
        type: "request_vector"
    returns: "grant_result"
    maps_to_port: "grantVec"
```

方法级别的 `effect` 字段告知 compiler 该方法是否有副作用，影响目标语言的实现方式（如 BSV 中 `method` vs `method Action` vs `method ActionValue#(T)`）。

### 4.4 子接口（来自 IDE subgraph 模型）

使用 litegraph.js 的 subgraphs 功能实现硬件 RTL 模块层级。在 YAML 中对应 `sub_interfaces`：

```yaml
sub_interfaces:
  - name: "fifof"
    type_id: "fifo_interface"
    library_ref: "FIFOF"        # 标准库接口引用（可选）
    description: "标准 FIFO 接口，提供 enqueue/dequeue 操作"
    methods:
      - name: "first"
        effect: "combinational"
        returns: "generic_data_type"
```

编译器视角：`sub_interfaces` 是模块对外暴露的结构化接口组，编译时需要为其生成对应的 interface 实例。

### 4.5 类型定义系统

类型统一定义在 `types.yaml` 中，每个类型是自然语言描述的标签：

```yaml
types:
  - id: "request_vector"
    description: >
      一个位宽为 reqNum 的向量，每个 bit 对应一个请求客户端。
      reqNum 是模块的泛型参数，由上层实例化时指定。
    category: "vector"

  - id: "grant_result"
    description: >
      与 request_vector 位宽相同的 one-hot 向量，只有一个 bit 为 1。
    category: "vector"
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 类型唯一标识符，语义化命名（如 `request_vector`，非 `Bit_N`） |
| `description` | 是 | 自然语言描述，是大模型翻译类型的唯一依据 |
| `category` | 否 | 大类标签：vector、register、struct、enum、fifo、pipeline 等 |

编译器视角：
- 两步生成：Phase 1 扫描所有被引用类型 → 翻译为目标语言类型文件（如 `typedefs.bsv`）→ Phase 2 模块代码引用翻译后的类型名
- 连接校验：同 type ID → 兼容；不同 type ID → 不兼容（除非连接带 `description` 描述变换）

### 4.6 连线系统

连线描述模块端口之间的数据流向。只发生在有明确类型 ID 的模块端口之间：

```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    to: [{ node: "left_arb_inst", port: "reqVec" }]
    description: >
      取 reqVec 的低半部分送给左子仲裁器。截断操作提取低位。
      from 类型: request_vector, to 类型: half_width_vector
```

连线级别可携带自己的 `knowledge.<lang>` 知识字段。

编译器视角的关键约束：
- 连线是图结构的基础——compiler 通过 connections 遍历上下游节点，收集相邻模块的知识
- 跨图连线必须穿透的所有层级都有对应端口（不凭空跨越）
- 带 `description` 的连线描述了数据变换（截断、合并、类型转换等），compiler 需将此信息传递给大模型

### 4.7 知识模板层级（6 级）

知识按层级组织，每层可向上层追加/覆盖提示词内容：

| 层级 | 位置 | 内容 | 作用域 |
|------|------|------|--------|
| L0 语言级 | `templates/<lang>/template.md` | 语法规范、编码约定、常见 pitfalls、导入决策表、类型翻译指导 | 所有同语言项目 |
| L1 项目级 | `project.yaml` + `system_knowledge.md` | 项目描述、目标语言、可用库、项目特定约束 | 单个 project 内所有模块 |
| L2 模块级 | 每个 `<module>.yaml` | 模块接口契约（ports + methods + sub_interfaces） | 当前模块 + 父模块可见 |
| L3 节点级 | `<module>.yaml` 的 `behavior` + `knowledge` | 实现算法、自然语言约束、实现细节 | 仅当前模块（接口隔离） |
| L4 连线级 | `connections[].knowledge` | 连线特定的数据变换知识 | 当前连线 |
| L5 端口级 | `ports[].knowledge` | 端口特定的知识 | 当前端口 |

关键规则：
- **接口隔离**：父模块仅获取子模块的 L2（接口契约），不获取 L3（行为知识/实现细节）
- **知识下沉**：多个子模块共享的知识写到父模块的 L3
- **知识上升**：项目内通用约定写到 L1
- **上级默认 + 下级覆盖**：上级提供默认模板，特殊场景下用户可覆盖

---

## 五、编译器内部运作流程

### 5.1 图遍历与知识收集

compiler 通过 connections 遍历图的上下游节点。对每个模块生成代码时，上看 N 层、下看 N 层，收集相邻层内的知识、数据类型、接口信息、模块功能，经过整理后交给大模型。

### 5.2 生成策略

compiler 需支持多种可插拔策略：

| 策略 | 描述 |
|------|------|
| **Two-Phase** | Phase 1：遍历所有类型定义 → 生成类型 RTL → Phase 2：按依赖拓扑序（叶子→根）生成模块代码 |
| **Bottom-Up** | 从叶子节点开始逐层向上生成，每层生成后编译验证 |
| **Top-Down** | 从根节点开始逐层向下生成 |
| **Parallel** | 所有叶子节点并行生成（无依赖时可并发） |

策略可组合。需通过实验对比效果确定最优策略。

### 5.3 构建范围与模式（来自 IDE 构建需求）

compiler 需支持不同构建范围和模式：

**构建范围**：
- 仅当前模块
- 该模块的所有子节点
- 该模块的所有父节点
- 整个工程全部重新构建

**构建模式**：
| 模式 | 说明 |
|------|------|
| **fresh** | 全新构建：只发送模块属性和端口提示词，不发送已生成代码 |
| **incremental** | 增量构建：发送模块属性 + 端口提示词 + 之前生成的 RTL 代码作为参考 |
| **test** | 测试生成：基于 test_method 字段 + 相邻模块信息，生成 testbench |


---

## 六、自我验证与迭代闭环

### 6.1 验证流程

使用 blue-rdma 目录下的 Bluespec 代码，按以下流程自我评判正确性并迭代：

1. 将 Bluespec 代码转写为 YAML 文件系统
2. compiler 从 YAML 编译生成新的 Bluespec 代码
3. 生成的 Bluespec 代码通过原 testbench 测试
4. 分析失败根因，修改 YAML 知识或模板，重新生成
5. 迭代到零手动修复即可通过

**迭代目标**：找到一种可以承接复杂RTL设计需求的yaml文件格式，以及可以将一组yaml文件正确转换为RTL的编译转换流程。

### 6.2 修改模式（CRITICAL）

> 正确模式：修改 YAML 中的知识表述 → 重新生成 BSV 代码 → 验证零手动修复通过
> 错误模式：直接修改生成的 BSV 代码 → 事后更新模板

### 6.3 迭代工作方式

每次迭代独立文件夹，不原地覆盖：

```
compiler/
├── state/              # 共享的持久化状态文件
│   ├── progress.json
│   ├── findings.jsonl
│   ├── directions_tried.json
│   └── iteration_log.jsonl
├── templates/          # 语言模板（跨迭代共享）
│   └── bluespec_sv/
│       └── template.md
├── iter_001/           # 第一次迭代工作区（独立）
├── iter_002/           # 第二次迭代工作区（独立）
└── iter_008/           # 当前迭代工作区（独立）
    ├── special_fifof/
    │   ├── project.yaml
    │   ├── library/
    │   └── generated/
    └── rr_arbiter/
        ├── project.yaml
        ├── library/
        └── generated/
```

---

## 七、Deli_AutoResearch 协议约束

当前任务遵循 Deli_AutoResearch 长周期自主任务协议：

| 约束 | 说明 |
|------|------|
| 零交互 | 运行期间不向用户提问，自行解决歧义并记录决策到 log |
| 准备好了就执行 | 不询问"是否应该提交"，直接执行 |
| 状态持久化到文件 | 所有进度写入 state/ 文件，不用对话记忆 |
| 新鲜会话 | 每轮迭代注入精选状态，不使用 resume |
| 方向多样性 | 新方向必须与所有已尝试方向不同 |
| 独立目录 | 每次迭代新建文件夹操作 |

---

## 八、关键设计决策记录

以下是从会话历史中提取的用户明确要求或确认的设计决策：

1. **compiler 是核心**，backend/frontend 围绕 compiler 服务
2. **类型 ID 是自然语言描述的标签**，不是真实数据类型。具体目标语言类型由大模型在生成阶段翻译
3. **内部信号由大模型自行生成**，不在 YAML 中预定义 signals 节。用户如果有特殊实现要求，通过自然语言在 behavior.description 中描述
4. **Provisos 以自然语言描述**，不绑定特定 RTL 语法。由大模型在生成时推导。合并脚本负责收集和呈现，不负责推导
5. **端口类型引用类型 ID**，连接校验基于类型 ID 匹配。同 ID → 兼容，不同 ID → 不兼容（除非有 transform 说明）
6. **两步生成流程**：Phase 1 翻译类型定义 → Phase 2 生成模块代码
7. **接口隔离**：父模块仅获取子模块的接口契约（L2），不获取行为实现细节（L3）
8. **Import 分析基于类型驱动**，不对 knowledge 文本做关键词匹配
9. **知识层级 6 级**：L0 语言模板 → L1 项目知识 → L2 模块接口 → L3 节点行为 → L4 连线知识 → L5 端口知识
10. **最终产物是图而非树**：节点间可以同级互相连接
11. **版本管理**：以 git 做历史记录
12. **IDE 布局**：多面板布局，左侧或顶部工具栏，方便用户操作
13. **缓存一致性**：切换子图不丢失数据，递归引用共享同一份缓存状态


## 九、 以上内容如有冲突，以下面描述为准：

我们需要实现一种由大语言模型作为核心能力的“自然语言->RTL的编译器”，对于这个编译器而言，其输出目标语言是BluespecSystemVerilog、SystemVerilog、VHDL、Chisel等等语言，因此输出是什么样子的，已经相对确定了。 重要的问题是：
1. 这个编译器的输入数据是什么格式的
2. 这个编译器的内部运作流程是什么样子的

首先讨论第一个问题：
* 我们希望人类可以通过【嵌套多层级的图结构 + 自然语言描述】来定义出一个RTL项目的骨架和重要信息，然后由大模型根据这些信息来产出RTL代码 和 对应的测试用例代码。
  * 因此，我们需要核心定义在yaml文件中如何存储这些必要的描述信息。
  * 在设计存储结构的过程中，要考虑到这种结构在未来如何支持一个可视化的编辑工具（IDE）。
    * 这就像你可以使用最简单的文本编辑器来编辑各种yaml文件，但是对用户不友好。yaml是信息承载最基础的方式，但我们未来要在上面提供一个可视化的编辑环境，来通过拖拽等方式，构建出这样的yaml文件系统。
        * 目前，我们已经有了一个初步的UI可视化界面，可以参考其设计。

然后是第二个问题，基于大模型的编译器如何工作：
* 我们的设计是一个图结构，因此在生成RTL代码的过程中，应该可以通过图的连接关系，在当前模块的上游和下游节点之间进行遍历游走访问，例如上看2层，下看2层，将相邻2层内的知识、数据类型、接口信息、模块功能等，经过整理，给到当前模块生成代码。当然，生成的策略也有不同的方式，例如是从最开始的根节点，逐层向下生成，还是所有节点同时并行生成？这是需要进行实际实验对比，才可以得出效果的。因此，第二步工作的重点是如何把这个编译的流程控制好，也就是我们需要一个主控程序来按照一定的规则，完成图的遍历、知识的合并，然后调用Agent完成代码的生成。这个主控程序需要支持不同的策略，例如先遍历所有的类型定义，生成类型对应的RTL，再对图进行遍历，对于每个节点，都看一下相邻节点的信息，然后指导本节点生成RTL代码。

所以，我们现在需要将现有工程的backend、frontend两部分架构，变更为backend、frontend、compiler三部分架构，其中compiler是三部分中最重要的一个。这三个部分的关系如下：
    - compiler： 核心逻辑，负责把图+自然语言的yaml文件系统输入转换为目标语言的RTL代码。
    - frontend： 后续补充的逻辑，提供可视化的界面来生成compiler所需要的yaml文件系统
    - backend： 将compiler和frontend粘合起来的服务系统，对外提供静态frontend的网页服务，并响应用户在浏览器中的操作，管理yaml文件系统、调用compiler进行编译等。

基于上述背景知识，开始你在compiler上的自动调研、开发任务：
1、设计符合上述思想的yaml文件定义
2、设计符合上述思想的compiler实现
3、使用blue-rdma目录下的bluespec代码，依然按照 先将bluespec代码转写为yaml文件系统，再由yaml文件系统反过来编译生成新的bluespec代码，最后看生成bluespec代码是否可以通过testbench测试的流程，来自我评判正确性、并自我迭代。直到找到最优的yaml文件格式，以及最优的compiler实现。
4、注意：你设计的系统，其yaml文件系统中应该是抽象的，不与任何具体目标RTL语言特性绑定的。如果必须针对某种目标语言进行指引，应该将其写在某个层级（如目标语言模板、项目、图、端口、连线等各个层级）私有的知识字段中，而不是为这个语言特地增加某种字段。
5、当生成的目标语言代码编译或者test发生错误时，应该修改yaml中的描述，然后重新弄生成目标代码，而不是直接修改已经生成的代码。
6、无论对生成代码的测试是成功还是失败，本轮迭代都已经完成，应该开启下一轮迭代。