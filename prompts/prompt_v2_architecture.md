# 系统架构

> 所属知识库：`prompt_v2.md` | 加载时机：需要理解系统整体架构时

---

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
