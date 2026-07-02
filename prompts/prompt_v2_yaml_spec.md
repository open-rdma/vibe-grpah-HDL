# YAML 文件系统规范

> 所属知识库：`prompt_v2.md` | 加载时机：设计 YAML 格式、编写 YAML、理解字段含义时

---

## 三、输入数据格式要求

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
