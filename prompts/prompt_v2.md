# 自然语言 + 多层级嵌套图→RTL 编译器系统 功能需求规格


## 一、系统总目标

实现一种**由大语言模型作为核心能力的"自然语言 + 多层级嵌套图→RTL的编译器"**，其中多层级嵌套图非常类似LabView软件的图形编程方式，也与Verilog的模块层级非常类似：顶层模块可以实例化若干子模块，每个子模块本身是一张图，有输入输出端口和各个子模块之间的连线，端口和连线具有类型约束，每个子模块对应一个独立的文件存储（类似Labview的.vi文件，我们在这里使用yaml格式）。

输出目标语言包括 BluespecSystemVerilog、SystemVerilog、VHDL、Chisel 等。


我们要通过自动研究系统的自动迭代实验，搞清楚两个核心问题：

1. **这个编译器的输入数据是什么格式的比较好？设计一套输入数据格式规范。**
2. **这个编译器的内部运作流程是什么样子的？设计一套可以正确将自然语言+图的输入数据正确翻译为目标语言的编译器。**

---

## 二、三部分架构

工程由 **backend、frontend、compiler**三部分组成，其中 **compiler 是最重要的核心**。

| 部分 | 职责 |
|------|------|
| **compiler** | 核心逻辑，把"图 + 自然语言"的 YAML 文件系统输入转换为目标语言的 RTL 代码 |
| **frontend** | 可视化界面，通过拖拽等方式生成 compiler 所需要的 YAML 文件系统。其展示结构参考LabView的多层级Flow Based Programming模式。使用 litegraph.js 作为图形编辑框架，TypeScript 编写，Vite 构建为静态页面 |
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
| `parameters` | 否 | 泛型/数值参数列表（name + kind + constraints） |
| `ports` | 否 | 端口列表（见 4.2） |
| `nodes` | 否 | 子模块实例化列表（见 4.5） |
| `connections` | 否 | 子模块间的连线列表 |
| `test_method` | 否 | 测试方法字段，指导大模型生成单元测试（激励生成逻辑、checker 逻辑等） |
| `properties` | 否 | 用户自定义键值对（透传到生成 prompt, description中可以使用模板语法动态引用此处定义的属性值） |
| `knowledge.<lang>` | 否 | 语言特定的知识（imports、provisos、hints 等） |

编译器视角的关键约束：
- `meta.description` 是必填的核心字段——这是大模型理解模块意图的唯一入口
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
6. **泛型类型端口**： 如果端口所对应的类型具有泛型参数，则泛型参数的具体值来自实例化该节点时父级图中的inst_local信息。


方法级别的 `effect` 字段告知 compiler 该方法是否有副作用，影响目标语言的实现方式（如 BSV 中 `method` vs `method Action` vs `method ActionValue#(T)`）。


### 4.3 类型定义系统

类型统一定义在 `types.yaml` 中，每个类型是自然语言描述的标签：

```yaml
types:
  - id: "request_vector"
    description: >
      一个位宽为 reqNum 的向量，每个 bit 对应一个请求客户端。
      reqNum 是模块的泛型参数，由上层实例化时指定。

  - id: "grant_result"
    description: >
      与 request_vector 位宽相同的 one-hot 向量，只有一个 bit 为 1。
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 类型唯一标识符 |
| `description` | 是 | 自然语言描述，是大模型翻译类型的唯一依据 |
| `generics` | 否 | 泛型参数列表 |
| `properties` | 否 | 自定义属性 |

编译器视角：
- 两步生成：Phase 1 扫描所有被引用类型 → 翻译为目标语言类型文件（如 `typedefs.bsv`）→ Phase 2 模块代码引用翻译后的类型名
- 连接校验：同 type ID → 兼容；不同 type ID → 不兼容（除非连接带 `description` 描述变换）

### 4.4 连线系统

连线描述模块端口之间的数据流向。只发生在有明确类型 ID 的模块端口之间：

```yaml
connections:
  - from: { node: "graph_input", port: "reqVec" }
    to: [{ node: "left_arb_inst", port: "reqVec" }]
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `from` | 是 | 连线的起始节点 |
| `to` | 是 | 连线的终止节点 |
| `generics` | 否 | 泛型参数列表 |
| `properties` | 否 | 自定义属性 |

连线级别可携带自己的 `knowledge.<lang>` 知识字段。

编译器视角的关键约束：
- 连线是图结构的基础——compiler 通过 connections 遍历上下游节点，收集相邻模块的知识
- 跨图连线必须穿透的所有层级都有对应端口（不凭空跨越）

### 4.5 子模块系统

描述如何实例化另一个yaml中描述的子模块到当前模块中。

```yaml
nodes:
  - id: "foo_1"
    ref: "aaa/bbb/foo.yaml"
    inst_local:
      properties:
        - key: k1
        - value: v1
      overwrites:
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | 是 | 模块实例的唯一标识 |
| `ref` | 是 | 模块对应的定义yaml文件 |
| `inst_local` | 否 | 模块本身特有的属性， 以及覆盖掉ref指向的yaml文件中某些配置的字段，从而使得同一个yaml文件的不同实例可以呈现出不同的特点。例如具有泛型类型端口的实例，其具体类型可以在这里指定 |


### 4.6 知识模板层级（6 级）

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
| **fresh** | 全新构建：只发送模块的各种知识信息合并得到的提示词，不发送已生成代码 |
| **incremental** | 增量构建：发送各种知识信息合并得到的提示词 + 之前生成的 RTL 代码作为参考 |
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

每次迭代独立文件夹，不原地覆盖，具体参考Deli_AutoResearch技能

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
3. **内部信号由大模型自行生成**，用户如果有特殊实现要求，通过自然语言在 behavior.description 中描述
4. **Provisos 以自然语言描述**，不绑定特定 RTL 语法。由大模型在生成时推导。合并脚本负责收集和呈现，不负责推导
5. **端口类型引用类型 ID**，连接校验基于类型 ID 匹配。同 ID → 兼容，不同 ID → 不兼容（除非有 transform 说明）。对于具有泛型的参数，需要将泛型带入具体类型后进行对比。
6. **两步生成流程**：Phase 1 翻译类型定义 → Phase 2 生成模块代码
7. **接口隔离**：父模块仅获取子模块的接口契约（L2），不获取行为实现细节（L3）
8. **版本管理**：以 git 做历史记录


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
7、执行完毕后清理bsc编译产物，只保留产生的bsv源代码（无论是否正确），进行git提交。
8、当前系统安装的claude code名为ccb， 在脚本中如果需要启动claude code，命令行命令为ccb，其余使用和Claude code 完全一致。

## 十、 优化方向
* 首先优化yaml的表达能力，以及compiler整合各层级知识，能够调用coding agent生成正确等价bsv代码的能力。
* 在保证代码生成正确性的基础上，逐步迭代简化yaml文件的复杂度，减少字段种类；使得yaml文件逐渐变得更加抽象，减少其中对具体实现的描述，例如：
  * 向着仅使用自然语言描述需求的**声明式**表述进化，而不是指令式的。
  * 在描述需求的过程中不能提供内部实现的变量名称、变量类型等，这些内部变量应该由大模型自动生成出来
  * 原则上，模块边界、端口的描述，可以明确指定变量名称、方法名称、数据类型。但是对于模块内部的功能，原则上仅描述功能诉求，如果多次迭代仍无法得到正确生成结果，则可以按照如下层级结构逐步添加细节信息（你尽可能使用L0，实在不行才可以向更高层级移动）：
    * L0： 仅描述需求，不描述任何细节，一些必要的信息可以从父级的知识中获取,例如：该模块实现一个Credit预分配功能，当req端口有信号时，在resp端口返回一个credit token。当该token使用完成后，通过put接口归还之前的token。
    * L1: 描述需求，提供少量实现细节，大部分知识仍然从父级知识中获取，例如： 该模块实现一个Credit预分配功能，当req端口有信号时，在resp端口返回一个credit token。当该token使用完成后，通过put接口归还之前的token，其中的credit可以通过两个FIFO来实现。
    * L2： 描述需求，提供大量实现细节，但父级知识也有重要作用，例如：该模块实现一个Credit预分配功能，当req端口有信号时，在resp端口返回一个credit token。当该token使用完成后，通过put接口归还之前的token，其中的credit可以通过两个FIFO来实现，第一个FIFO叫做busy_fifo，第二个fifo叫做idel_fifo,在两个时钟周期内完成。
    * L3： 描述需求，同时提供部分伪代码示例。
    * L4： 描述需求，直接提供可以使用的特定语言代码片段。
  * 在不引入源代码片段的情况下，两个可以指导编译器生成正确RTL代码的yaml文件，字节数较小的yaml文件更好。


---------------------------------------------------------------------

/loop 30m /Deli_AutoResearch 以prompts/prompt_v2.md中的内容为基础，进行Compiler的研究工作。即使你已经看过这个md文件中的内容了，现在也重新阅读一遍。不能直接修改bsv，无论成功失败都要开始下一轮迭代，每次迭代创建新的目录，每次仿真超时时间不大于1分钟。产出结果放在当前目录的compiler_iters_v1目录下。 没有明确的指令，则一直尝试新的方向，不要停止。bsc编译器使用这个：/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04

---

## 附录A：bsv→yaml→bsv 转换实验测试集

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

### 测试样本清单

---

#### Phase 1 — 纯类型定义（无行为逻辑，验证YAML对类型系统的表达能力）

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

#### Phase 2 — 简单工具模块（独立可测，逻辑简单）

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

#### Phase 3 — 仲裁与工作完成生成（中等单模块）

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

#### Phase 4 — 流水线与包处理模块（中等复杂度，Pipeline模式）

**T07: ExtractAndPrependPipeOut.bsv**
- 源文件: `blue-rdma/src/ExtractAndPrependPipeOut.bsv` (748行)
- 测试文件: `blue-rdma/test/TestExtractAndPrependPipeOut.bsv` (329行, 5个testcase)
- 复杂度: ★★★☆☆
- 模块类型: 数据流处理管线（Header提取/插入/转换）
- 涉及 `DataStream` <-> `HeaderRDMA` 双向转换、字节对齐
- Testcases: `mkTestHeaderAndDataStreamConversion`, `mkTestPrependHeaderBeforeEmptyDataStream`, `mkTestExtractHeaderWithPayloadLessThanOneFrag`, `mkTestExtractHeaderLongerThanDataStream`, `mkTestExtractAndPrependHeader`
- 关键挑战: 生物理层的字节操作逻辑在YAML中的声明式描述

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

#### Phase 5 — 发送队列与请求生成（多子模块协作）

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

#### Phase 6 — QP管理与重试处理（核心协议逻辑）

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

#### Phase 7 — 负载处理（大模块，复杂数据通路）

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

#### Phase 8 — 元数据基础设施（多层嵌套图结构）

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

#### Phase 9 — 顶层集成（全系统验证）

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

---

## 附录B：评估指标体系

### B.1 指标总览

评估分为两大维度：
- **维度A：知识表示质量** — 评判 YAML 格式本身的好坏
- **维度B：编译器转换能力** — 评判 compiler + Agent 将 YAML 正确转换为 BSV 的能力

每个指标包含：定义、测量方法、数据收集方式、存储格式。

---

### B.2 维度A：知识表示质量指标

#### A1. 语义完整性 (Semantic Completeness, SC)

**定义**：原始 BSV 代码中的语义构造（interface方法、module实例、rule、状态寄存器、连线关系等）有多少能在 YAML 文件中被正确表达。

**测量方法**：
1. 解析原始 BSV 源码，提取语义构造列表：`{interfaces: N, methods: M, rules: R, submodules: S, connections: C, states: ST}`
2. 解析对应的 YAML 文件，统计已表达的语义构造数量
3. `SC = 已表达的语义构造数 / 原始BSV语义构造总数`

**数据收集**：每个模块的 bsv→yaml 转写阶段自动统计

**存储格式** (`metrics/sc_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF",
  "timestamp": "2026-07-02T10:00:00Z",
  "iteration": "iter_001",
  "original_constructs": {
    "interfaces": 3,
    "methods": 15,
    "rules": 12,
    "submodules": 0,
    "state_registers": 8
  },
  "expressed_in_yaml": {
    "interfaces": 3,
    "methods": 15,
    "rules": 12,
    "submodules": 0,
    "state_registers": 6
  },
  "sc_score": 0.92
}
```

#### A2. 信息密度 (Information Density, ID)

**定义**：YAML 文件总字节数 / 原始 BSV 文件总字节数的比值。值越小说明用更少的信息量描述了相同的功能（更好）。

**测量方法**：
1. `yaml_size = sum(os.path.getsize(f) for f in yaml_files)`
2. `bsv_size = os.path.getsize(original_bsv_file)`
3. `ID = yaml_size / bsv_size`

**数据收集**：每次 bsv→yaml 转写完成后自动计算

**存储格式** (`metrics/id_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF",
  "iteration": "iter_001",
  "bsv_bytes": 18720,
  "yaml_bytes": 12480,
  "id_ratio": 0.667,
  "yaml_file_count": 3
}
```

#### A3. 抽象层级 (Abstraction Level, AL)

**定义**：YAML 中使用自然语言描述（声明式）的字段数量占所有描述性字段的比例。比例越高说明越"声明式"而非"指令式"。

**测量方法**：
1. 扫描所有 YAML 文件中的 `description`、`behavior.description`、`knowledge` 等描述性字段
2. 使用启发式规则分类：含代码片段/变量名/具体时序 → "指令式"；纯功能描述 → "声明式"
3. 也可由 LLM 辅助分类：对每个描述字段调用轻量模型判断其抽象层级（L0纯声明 ~ L4含代码）
4. `AL = L0+L1级别描述数 / 总描述字段数`

**数据收集**：YAML 写入后自动分析

**存储格式** (`metrics/al_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF",
  "iteration": "iter_001",
  "total_description_fields": 24,
  "level_distribution": {
    "L0_pure_declarative": 8,
    "L1_minimal_hints": 6,
    "L2_moderate_detail": 5,
    "L3_pseudocode": 3,
    "L4_code_snippets": 2
  },
  "al_score": 0.583
}
```

#### A4. 语言独立性评分 (Language Independence Score, LIS)

**定义**：YAML 文件中出现在通用字段（非 `knowledge.<lang>` 字段）中的语言特定构造数量。越低越好，0 表示完全语言无关。

**测量方法**：
1. 扫描所有 YAML 文件，排除 `knowledge.bsv`、`knowledge.sv` 等语言知识字段
2. 在剩余字段中检测语言特定模式：
   - BSV 特定关键词：`FIFOF`, `Reg#(`, `interface`, `method`, `rule`, `module`, `provisos`
   - SystemVerilog 特定关键词：`always_ff`, `always_comb`, `logic`, `wire`, `reg`
   - VHDL 特定关键词：`entity`, `architecture`, `process`, `signal`
3. `LIS = 语言特定构造出现次数`（越低越好，目标为 0）

**数据收集**：YAML 写入后自动正则扫描

**存储格式** (`metrics/lis_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF",
  "iteration": "iter_001",
  "language_specific_occurrences": {
    "bsv_specific": 0,
    "sv_specific": 0,
    "vhdl_specific": 0
  },
  "lis_score": 0,
  "details": []
}
```

---

### B.3 维度B：编译器转换能力指标

#### B1. 首次编译通过率 (First-Pass Compilation, FPC)

**定义**：Agent 生成的 BSV 代码在**不做任何手动修改**的情况下，首次通过 bsc 编译的比例。

**测量方法**：
1. Agent 从 YAML 生成 BSV 代码
2. 立即运行 `bsc -verilog -g <topmodule> <generated.bsv>` （不做任何修改）
3. 记录编译是否成功（exit code 0 且无 error）
4. `FPC = 首次编译成功的模块数 / 总模块数`

**数据收集**：每次 Agent 生成后自动运行编译

**存储格式** (`metrics/fpc_<iteration_id>.json`):
```json
{
  "iteration": "iter_001",
  "timestamp": "2026-07-02T10:30:00Z",
  "total_modules": 20,
  "first_pass_compile_success": 12,
  "fpc_rate": 0.60,
  "per_module": {
    "SpecialFIFOF": {"success": true, "errors": []},
    "Arbitration": {"success": false, "errors": ["Type mismatch at line 45..."]}
  }
}
```

#### B2. 测试通过率 (Test Pass Rate, TPR)

**定义**：生成的 BSV 代码通过对应 testbench 仿真的比例。

**测量方法**：
1. 编译生成的 BSV 代码 + 原始 testbench（testbench 不做转换）
2. 运行 `bsc -verilog -g <test_module> -e <test_module> <generated.bsv> <testbench.bsv>`
3. 执行仿真，检查 `$finish(0)` vs `$finish(1)` / `$error`
4. 每个 testcase 单独统计
5. `TPR = 通过的testcase数 / 总testcase数`

**数据收集**：编译成功后自动运行仿真

**存储格式** (`metrics/tpr_<iteration_id>.json`):
```json
{
  "iteration": "iter_001",
  "total_testcases": 87,
  "passed_testcases": 45,
  "tpr_score": 0.517,
  "per_module": {
    "SpecialFIFOF": {
      "total": 4,
      "passed": 4,
      "tpr": 1.0,
      "details": {
        "mkTestCacheFIFO2": "PASS",
        "mkTestScanFIFOF": "PASS",
        "mkTestSearchFIFOF": "PASS",
        "mkTestVectorSearch": "PASS"
      }
    }
  }
}
```

#### B3. 零修复通过率 (Zero-Fix Pass Rate, ZFPR)

**定义**：**这是最核心的指标**。在不手动修改任何一行生成的 BSV 代码的前提下，所有 testbench 全部通过的模块比例。对应 prompt_v2.md 中的核心迭代目标："零手动修复即可通过"。

**测量方法**：
1. 禁止对生成的 BSV 做任何手动修改（CRITICAL）
2. 只允许修改 YAML → 重新生成 BSV（正确迭代模式）
3. `ZFPR = 零修复全部testcase通过的模块数 / 总模块数`

**数据收集**：每个模块的所有 testcase 都 PASS 时标记为 zero-fix pass

**存储格式** (`metrics/zfpr_<iteration_id>.json`):
```json
{
  "iteration": "iter_001",
  "total_modules": 20,
  "zero_fix_pass_modules": 5,
  "zfpr_score": 0.25,
  "per_module": {
    "SpecialFIFOF": {"zero_fix_pass": true, "all_testcases_pass": true},
    "Arbitration": {"zero_fix_pass": false, "failing_testcases": ["mkTestServerArbiter"]}
  },
  "note": "零手动修复——仅通过修改YAML和重新生成达到的通过状态"
}
```

#### B4. 迭代收敛次数 (Iteration Count to Pass, ICP)

**定义**：一个模块从初始 YAML 到达到 ZFPR（零修复通过所有testcase）所需的 bsv→yaml→bsv 迭代轮数。

**测量方法**：
1. 对每个模块追踪迭代次数
2. 每次迭代 = 修改 YAML → 重新生成 BSV → 编译 → 仿真
3. 记录首次达到 ZFPR 时的迭代次数
4. 若超过最大迭代限制仍未通过，标记为 `unconverged`

**数据收集**：per-module 计数器

**存储格式** (`metrics/icp_<iteration_id>.json`):
```json
{
  "iteration": "iter_005",
  "per_module": {
    "SpecialFIFOF": {"icp": 2, "converged": true},
    "Arbitration": {"icp": 5, "converged": true},
    "ReqHandleRQ": {"icp": null, "converged": false, "max_iterations": 20}
  },
  "average_converged": 3.8,
  "unconverged_modules": ["ReqHandleRQ", "PayloadGen"]
}
```

#### B5. 依赖链覆盖率 (Dependency Chain Coverage, DCC)

**定义**：在依赖图中，从叶子节点开始，连续通过（ZFPR）的最大深度。反映 compiler 处理依赖传递的能力。

**测量方法**：
1. 建立模块依赖 DAG
2. 找到所有从叶子开始的连续 ZFPR 链路
3. `DCC = 最长连续ZFPR链路深度 / 总依赖深度`
4. 记录断点位置（第一个未通过的模块及其下游影响范围）

**数据收集**：基于 ZFPR 结果和依赖图计算

**存储格式** (`metrics/dcc_<iteration_id>.json`):
```json
{
  "iteration": "iter_005",
  "total_dependency_depth": 9,
  "longest_continuous_zfpr_chain": 4,
  "dcc_score": 0.444,
  "zfpr_chain": ["Settings", "Headers", "Utils", "SpecialFIFOF"],
  "break_point": "Arbitration",
  "blocked_modules": ["WorkCompGen", "InputPktHandle", "... 下游12个模块"]
}
```

#### B6. 轮转保真度 (Round-Trip Fidelity, RTF)

**定义**：生成的 BSV 代码与原始 BSV 代码在**结构层面**的相似度。不要求逐字节相同（因为 YAML 是声明式描述，具体实现可能有差异），但关键结构应匹配。

**测量方法**：
1. 对比原始 BSV 与生成 BSV 的以下结构要素：
   - Interface 方法数量和名称匹配度
   - 端口数量和方向匹配度
   - 子模块实例化数量匹配度
   - Rule 数量匹配度
2. `RTF = (方法匹配率 + 端口匹配率 + 子模块匹配率 + Rule匹配率) / 4`

**数据收集**：BSV 解析器自动对比

**存储格式** (`metrics/rtf_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF",
  "iteration": "iter_001",
  "interface_methods": {
    "original": ["fifof.enq", "fifof.deq", "fifof.first", "fifof.notEmpty", "..."],
    "generated": ["fifof.enq", "fifof.deq", "fifof.first", "fifof.notEmpty", "..."],
    "match_rate": 1.0
  },
  "ports": {"match_rate": 1.0},
  "submodules": {"match_rate": 1.0},
  "rules": {"match_rate": 0.85},
  "rtf_score": 0.962
}
```

---

### B.4 辅助效率指标

#### C1. 生成耗时 (Generation Time, GT)

**定义**：compiler + Agent 从 YAML 生成 BSV 代码的 wall-clock 时间。

**测量**：Python `time.time()` 差值，单位为秒。

**存储格式** (`metrics/gt_<iteration_id>.json`):
```json
{
  "iteration": "iter_001",
  "per_module": {
    "SpecialFIFOF": {"generation_seconds": 45.2, "model": "deepseek-v4"},
    "ReqHandleRQ": {"generation_seconds": 180.5, "model": "deepseek-v4"}
  },
  "total_generation_seconds": 1820.3
}
```

#### C2. Token 效率 (Token Efficiency, TE)

**定义**：LLM 消耗的 token 数与生成的 BSV 代码行数之比。

**测量**：
1. 从 LLM API 响应中获取 `usage.prompt_tokens` + `usage.completion_tokens`
2. 统计生成的 BSV 文件总行数
3. `TE = total_tokens / total_generated_lines`

**存储格式** (`metrics/te_<iteration_id>.json`):
```json
{
  "iteration": "iter_001",
  "total_input_tokens": 45000,
  "total_output_tokens": 12000,
  "total_generated_lines": 2500,
  "te_tokens_per_line": 22.8
}
```

#### C3. 编译成功率趋势 (Compile Success Trend, CST)

**定义**：随着 YAML 知识不断丰富（迭代推进），FPC 和 TPR 的变化趋势。

**测量**：将每次迭代的 FPC 和 TPR 绘制为趋势线。

**存储格式** (`metrics/cst.json`):
```json
{
  "trends": [
    {"iteration": "iter_001", "fpc": 0.60, "tpr": 0.52},
    {"iteration": "iter_002", "fpc": 0.65, "tpr": 0.58},
    {"iteration": "iter_003", "fpc": 0.75, "tpr": 0.70}
  ],
  "fpc_trend": "improving",
  "tpr_trend": "improving"
}
```

---

### B.5 指标收集与存储总览

#### 目录结构

```
compiler_iters_v1/
├── metrics/
│   ├── summary_<iteration_id>.json     # 每次迭代的汇总指标
│   ├── sc/                             # 语义完整性
│   │   └── sc_<module>_<iter>.json
│   ├── id/                             # 信息密度
│   │   └── id_<module>_<iter>.json
│   ├── al/                             # 抽象层级
│   │   └── al_<module>_<iter>.json
│   ├── lis/                            # 语言独立性
│   │   └── lis_<module>_<iter>.json
│   ├── fpc/                            # 首次编译通过率
│   │   └── fpc_<iter>.json
│   ├── tpr/                            # 测试通过率
│   │   └── tpr_<iter>.json
│   ├── zfpr/                           # 零修复通过率
│   │   └── zfpr_<iter>.json
│   ├── icp/                            # 迭代收敛次数
│   │   └── icp_<iter>.json
│   ├── dcc/                            # 依赖链覆盖率
│   │   └── dcc_<iter>.json
│   ├── rtf/                            # 轮转保真度
│   │   └── rtf_<module>_<iter>.json
│   ├── gt/                             # 生成耗时
│   │   └── gt_<iter>.json
│   ├── te/                             # Token效率
│   │   └── te_<iter>.json
│   └── cst.json                        # 编译成功率趋势
└── iters/
    ├── iter_001/
    ├── iter_002/
    └── ...
```

#### 汇总指标格式 (`metrics/summary_<iteration_id>.json`)

每次迭代结束后自动生成汇总 JSON，包含所有维度指标的摘要：

```json
{
  "iteration_id": "iter_001",
  "timestamp": "2026-07-02T12:00:00Z",
  "test_set": "T01-T20 (full suite)",
  "modules_tested": 20,
  
  "dimension_a_knowledge_quality": {
    "avg_sc": 0.85,
    "avg_id": 0.72,
    "avg_al": 0.55,
    "avg_lis": 1.2
  },
  
  "dimension_b_compiler_capability": {
    "fpc": 0.60,
    "tpr": 0.52,
    "zfpr": 0.25,
    "avg_icp_converged": 3.8,
    "dcc": 0.44,
    "avg_rtf": 0.88
  },
  
  "efficiency": {
    "total_generation_seconds": 1820.3,
    "avg_tokens_per_line": 22.8
  },
  
  "key_findings": [
    "SpecialFIFOF 在2轮内收敛，说明简单状态机的YAML表达已较成熟",
    "ReqHandleRQ 和 PayloadGen 20轮未收敛，需要增强L3级别知识描述",
    "依赖链在 Arbitration 处断裂，compiler 处理多端口仲裁器的泛型传递有问题"
  ],
  
  "next_actions": [
    "优化 Arbitration 的泛型参数在 YAML 中的表达",
    "为 ReqHandleRQ 增加 L2 级别的子模块交互描述"
  ]
}
```

#### 自动化收集流程

1. **bsv→yaml 转写完成后**：自动运行 A1(SC)、A2(ID)、A3(AL)、A4(LIS) 指标采集脚本
2. **Agent 生成 BSV 完成后**：自动运行 B1(FPC) 编译检查
3. **编译通过后**：自动运行 B2(TPR) 仿真测试
4. **所有测试完成后**：自动计算 B3(ZFPR)、B4(ICP)、B5(DCC)、B6(RTF)
5. **迭代结束时**：生成 summary JSON 并追加 CST 趋势数据
6. **所有指标文件随迭代目录一起 git 提交**

#### 指标使用原则

- **核心判断标准**：ZFPR（零修复通过率）是判断 compiler 成熟度的第一指标
- **优化方向指引**：AL + ID 联合判断 YAML 格式是否过于冗长或过于抽象
- **瓶颈定位**：DCC 帮助定位知识传递的断裂点；ICP 帮助识别难以表达的模块类型
- **回归检测**：CST 趋势线在每次迭代后自动更新，确保新改动不引入回归
- **目标**：最终达到 20/20 模块的 ZFPR=1.0，且 AL≥0.7（以声明式描述为主）

