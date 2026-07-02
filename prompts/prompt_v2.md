# 自然语言 + 多层级嵌套图 → RTL 编译器系统

> **项目目标**：实现一种由大语言模型作为核心能力的编译器，将"嵌套多层级的图结构 + 自然语言描述"的 YAML 文件系统转换为 RTL 代码（BSV/SV/VHDL/Chisel）。通过自动迭代实验，找到最优的 YAML 输入格式和 compiler 内部运作流程。

---

## 知识加载规则

本文件是知识入口。以下子文件按需加载，第一次加载需要全部阅读。

### 加载指令

1. **首先阅读本文件**，了解知识结构和各子文件的用途
2. **根据当前任务阶段**，只加载相关的子文件
3. **执行阶段**：阅读本文件末尾的执行命令

### 子文件索引

| 文件 | 内容 | 何时加载 |
|------|------|---------|
| `prompt_v2_architecture.md` | 系统总目标、三部分架构（compiler/frontend/backend）、技术栈 | 需要理解系统整体架构时 |
| `prompt_v2_yaml_spec.md` | YAML 文件系统完整规范：节点属性、端口系统、类型定义、连线系统、子模块系统、6级知识模板层级 | 设计 YAML 格式、编写 YAML、理解字段含义时 |
| `prompt_v2_compiler_flow.md` | compiler 内部运作流程：图遍历、知识收集、生成策略（Two-Phase/Bottom-Up/Top-Down/Parallel）、构建范围与模式 | 实现/修改 compiler 逻辑时 |
| `prompt_v2_iteration_loop.md` | 自我验证与迭代闭环：bsv→yaml→bsv 流程、修改模式（CRITICAL）、Deli_AutoResearch 协议约束 | 执行迭代实验时 |
| `prompt_v2_design_decisions.md` | 8条关键设计决策 + 矛盾优先级说明 | 遇到设计冲突或不确定时 |
| `prompt_v2_optimization.md` | 优化方向：从指令式→声明式、L0-L4 抽象层级定义、字节数最小化目标 | 调优 YAML 格式或 compiler 策略时 |
| `prompt_v2_test_suite.md` | 20个测试样本（T01-T20），按简单→复杂排序，含模块依赖关系图和推进策略 | 选择测试目标、规划测试顺序时 |
| `prompt_v2_metrics.md` | 完整评估指标体系：维度A(知识表示质量 4指标) + 维度B(编译器转换能力 6指标) + 效率指标(3个) | 收集/分析实验数据、评判迭代效果时 |

### 典型加载场景

| 场景 | 加载文件 |
|------|---------|
| 开始新迭代 | `prompt_v2_iteration_loop.md` + `prompt_v2_test_suite.md` |
| 设计/修改 YAML 格式 | `prompt_v2_yaml_spec.md` + `prompt_v2_optimization.md` |
| 实现 compiler | `prompt_v2_compiler_flow.md` + `prompt_v2_yaml_spec.md` |
| 分析实验结果 | `prompt_v2_metrics.md` + `prompt_v2_test_suite.md` |
| 遇到设计冲突 | `prompt_v2_design_decisions.md` |
| 全局理解 | `prompt_v2_architecture.md` |

---

## 关键约束（速查）

- **核心任务**：1. 探索知识的组织记录存储形式。2.编写出好用的“编译器”（用于合并知识，形成完整的prompt，最后调用agent执行目标代码生成）。不可以跳过编译器或者coding agent而直接生成目标代码，目标代码必须是编译器调用coding agent生成的。
- **修改模式**：只改 YAML → 重新生成 BSV，禁止直接修改生成的 BSV
- **语言无关**：YAML 通用字段不得包含语言特定构造，语言知识写入 `knowledge.<lang>`
- **接口隔离**：父模块仅获取子模块 L2（接口契约），不获取 L3（行为实现细节）
- **零交互**：运行期间不向用户提问，自行决策并记录到 log
- **快速失败，高效迭代**：设置仿真器超时时间，不要因为仿真器卡死而浪费时间。多个仿真验证任务可以并行执行。
- **勤于记录**：每一步实验，每一次迭代，都要按照结果评估体系记录必要的数据，用于后续迭代和离线分析。
- **独立目录**：每次迭代新建文件夹。无论对生成代码的测试是成功还是失败，本轮迭代都已经完成，应该开启下一轮迭代。 执行完毕后清理bsc编译产物，只保留产生的bsv源代码（无论是否正确），进行git提交。
- **批量迭代**：每次迭代尝试独立、并行测试prompt_v2_test_suite.md文件中所有的20个test case，为每个test case判断是否通过，并收集指标。然后收集这一轮测试的所有问题，作为下一轮的改进方向。
- **自然语言优先**：在迭代过程中由原始bsv生成yaml文件时，参照prompt_v2_optimization.md的描述，尽可能使用L0级别，在description中用自然语言描述原有bsv的逻辑。如有任何升级必要，则必须开启新一轮迭代。尽量提升prompt_v2_metrics.md中的AL指标。严禁在任何迭代步骤中采用将原始bsv文件按语法或分词等方式进行拆解后写入yaml文件的行为或者尝试。
- **核心指标**：ZFPR（零修复通过率）——只改 YAML 不改 BSV 即通过所有 testbench
---

## 执行命令

```
/loop 30m /Deli_AutoResearch 以prompts/prompt_v2.md中的内容为基础，进行Compiler的研究工作。即使你已经看过这个md文件中的内容了，现在也重新阅读一遍。不能直接修改bsv，无论成功失败都要开始下一轮迭代，每次迭代创建新的目录，采用批量并行迭代策略，每次仿真超时时间不大于3分钟。产出结果放在当前目录的compiler_iters_v1目录下。 没有明确的指令，则一直尝试新的方向，不要停止。不要查看git的历史提交记录，不要受到历史尝试的影响。bsc编译器使用这个：/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04
```
