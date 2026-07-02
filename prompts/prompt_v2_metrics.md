# 评估指标体系

> 所属知识库：`prompt_v2.md` | 加载时机：收集/分析实验数据、评判迭代效果时

---

## 附录B：指标总览

评估分为两大维度：
- **维度A：知识表示质量** — 评判 YAML 格式本身的好坏（4个指标）
- **维度B：编译器转换能力** — 评判 compiler + Agent 将 YAML 正确转换为 BSV 的能力（6个指标）
- **辅助效率指标** — 3个辅助指标

每个指标包含：定义、测量方法、数据收集方式、存储格式。

---

## 维度A：知识表示质量指标

### A1. 语义完整性 (Semantic Completeness, SC)

**定义**：原始 BSV 代码中的语义构造（interface方法、module实例、rule、状态寄存器、连线关系等）有多少能在 YAML 文件中被正确表达。

**测量**：`SC = 已表达的语义构造数 / 原始BSV语义构造总数`

**存储** (`metrics/sc_<module_name>.json`):
```json
{
  "module": "SpecialFIFOF", "iteration": "iter_001",
  "original_constructs": {"interfaces": 3, "methods": 15, "rules": 12, "submodules": 0, "state_registers": 8},
  "expressed_in_yaml": {"interfaces": 3, "methods": 15, "rules": 12, "submodules": 0, "state_registers": 6},
  "sc_score": 0.92
}
```

### A2. 信息密度 (Information Density, ID)

**定义**：YAML 文件总字节数 / 原始 BSV 文件总字节数的比值。值越小越好。

**测量**：`ID = sum(os.path.getsize(yaml_files)) / os.path.getsize(bsv_file)`

**存储** (`metrics/id_<module_name>.json`):
```json
{"module": "SpecialFIFOF", "iteration": "iter_001", "bsv_bytes": 18720, "yaml_bytes": 12480, "id_ratio": 0.667, "yaml_file_count": 3}
```

### A3. 抽象层级 (Abstraction Level, AL)

**定义**：YAML 中声明式（L0+L1级别）描述字段占所有描述性字段的比例。越高越好。

**测量**：对每个 description 字段用 LLM 辅助分类（L0纯声明 ~ L4含代码），`AL = (L0+L1数量) / 总计`

**存储** (`metrics/al_<module_name>.json`):
```json
{"module": "SpecialFIFOF", "iteration": "iter_001", "total_description_fields": 24,
 "level_distribution": {"L0_pure_declarative": 8, "L1_minimal_hints": 6, "L2_moderate_detail": 5, "L3_pseudocode": 3, "L4_code_snippets": 2},
 "al_score": 0.583}
```

### A4. 语言独立性评分 (Language Independence Score, LIS)

**定义**：YAML 通用字段中出现的语言特定构造数量。0 = 完全语言无关（目标）。

**测量**：正则扫描排除 `knowledge.<lang>` 后的字段，检测 BSV/SV/VHDL 特定关键词出现次数。

**存储** (`metrics/lis_<module_name>.json`):
```json
{"module": "SpecialFIFOF", "iteration": "iter_001", "language_specific_occurrences": {"bsv_specific": 0, "sv_specific": 0, "vhdl_specific": 0}, "lis_score": 0}
```

---

## 维度B：编译器转换能力指标

### B1. 首次编译通过率 (First-Pass Compilation, FPC)

**定义**：不修改生成的 BSV，直接通过 bsc 编译的比例。

**测量**：`FPC = 首次编译成功的模块数 / 总模块数`

**存储** (`metrics/fpc_<iter>.json`):
```json
{"iteration": "iter_001", "total_modules": 20, "first_pass_compile_success": 12, "fpc_rate": 0.60,
 "per_module": {"SpecialFIFOF": {"success": true, "errors": []}, "Arbitration": {"success": false, "errors": ["Type mismatch..."]}}}
```

### B2. 测试通过率 (Test Pass Rate, TPR)

**定义**：生成 BSV + 原始 testbench 仿真的通过比例。每个 testcase 单独统计。

**测量**：`TPR = 通过的testcase数 / 总testcase数`

**存储** (`metrics/tpr_<iter>.json`):
```json
{"iteration": "iter_001", "total_testcases": 87, "passed_testcases": 45, "tpr_score": 0.517,
 "per_module": {"SpecialFIFOF": {"total": 4, "passed": 4, "tpr": 1.0,
   "details": {"mkTestCacheFIFO2": "PASS", "mkTestScanFIFOF": "PASS", "mkTestSearchFIFOF": "PASS", "mkTestVectorSearch": "PASS"}}}}
```

### B3. 零修复通过率 (Zero-Fix Pass Rate, ZFPR) ⭐核心指标

**定义**：只改 YAML 不改 BSV，所有 testbench 全部通过的模块比例。

**测量**：`ZFPR = 零修复全部testcase通过的模块数 / 总模块数`

**存储** (`metrics/zfpr_<iter>.json`):
```json
{"iteration": "iter_001", "total_modules": 20, "zero_fix_pass_modules": 5, "zfpr_score": 0.25,
 "per_module": {"SpecialFIFOF": {"zero_fix_pass": true}, "Arbitration": {"zero_fix_pass": false, "failing_testcases": ["mkTestServerArbiter"]}},
 "note": "零手动修复——仅通过修改YAML和重新生成达到的通过状态"}
```

### B4. 迭代收敛次数 (Iteration Count to Pass, ICP)

**定义**：模块从初始 YAML 到达到 ZFPR 所需的迭代轮数。超限标为 `unconverged`。

**存储** (`metrics/icp_<iter>.json`):
```json
{"iteration": "iter_005", "per_module": {"SpecialFIFOF": {"icp": 2, "converged": true}, "ReqHandleRQ": {"icp": null, "converged": false, "max_iterations": 20}},
 "average_converged": 3.8, "unconverged_modules": ["ReqHandleRQ", "PayloadGen"]}
```

### B5. 依赖链覆盖率 (Dependency Chain Coverage, DCC)

**定义**：依赖图中从叶子开始的连续 ZFPR 最大深度 / 总依赖深度。

**存储** (`metrics/dcc_<iter>.json`):
```json
{"iteration": "iter_005", "total_dependency_depth": 9, "longest_continuous_zfpr_chain": 4, "dcc_score": 0.444,
 "zfpr_chain": ["Settings", "Headers", "Utils", "SpecialFIFOF"], "break_point": "Arbitration"}
```

### B6. 轮转保真度 (Round-Trip Fidelity, RTF)

**定义**：生成 BSV 与原始 BSV 的结构相似度（接口方法、端口、子模块、Rule 的数量匹配率均值）。

**存储** (`metrics/rtf_<module>_<iter>.json`):
```json
{"module": "SpecialFIFOF", "iteration": "iter_001",
 "interface_methods": {"match_rate": 1.0}, "ports": {"match_rate": 1.0}, "submodules": {"match_rate": 1.0}, "rules": {"match_rate": 0.85},
 "rtf_score": 0.962}
```

---

## 辅助效率指标

### C1. 生成耗时 (GT)
Wall-clock 时间（秒），per-module 统计。存于 `metrics/gt_<iter>.json`。

### C2. Token 效率 (TE)
`total_tokens / total_generated_lines`，越低越好。存于 `metrics/te_<iter>.json`。

### C3. 编译成功率趋势 (CST)
FPC 和 TPR 随迭代的变化趋势线。存于 `metrics/cst.json`。

---

## 指标收集与存储

### 目录结构

```
compiler_iters_v1/
├── metrics/
│   ├── summary_<iteration_id>.json
│   ├── sc/    ├── id/    ├── al/    ├── lis/
│   ├── fpc/   ├── tpr/   ├── zfpr/  ├── icp/
│   ├── dcc/   ├── rtf/   ├── gt/    ├── te/
│   └── cst.json
└── iters/
    ├── iter_001/
    ├── iter_002/
    └── ...
```

### 汇总指标格式 (`metrics/summary_<iter>.json`)

```json
{
  "iteration_id": "iter_001", "timestamp": "2026-07-02T12:00:00Z",
  "dimension_a": {"avg_sc": 0.85, "avg_id": 0.72, "avg_al": 0.55, "avg_lis": 1.2},
  "dimension_b": {"fpc": 0.60, "tpr": 0.52, "zfpr": 0.25, "avg_icp_converged": 3.8, "dcc": 0.44, "avg_rtf": 0.88},
  "efficiency": {"total_generation_seconds": 1820.3, "avg_tokens_per_line": 22.8},
  "key_findings": [...], "next_actions": [...]
}
```

### 自动化收集流程

1. bsv→yaml 转写完成 → 运行 A1(SC)、A2(ID)、A3(AL)、A4(LIS)
2. Agent 生成 BSV 完成 → 运行 B1(FPC) 编译检查
3. 编译通过 → 运行 B2(TPR) 仿真
4. 全部测试完成 → 计算 B3(ZFPR)、B4(ICP)、B5(DCC)、B6(RTF)
5. 迭代结束 → 生成 summary JSON + 追加 CST 趋势
6. 所有指标文件随迭代目录一起 git 提交

### 指标使用原则

- **核心判断标准**：ZFPR 是判断 compiler 成熟度的第一指标
- **优化方向指引**：AL + ID 联合判断 YAML 格式是否过于冗长或过于抽象
- **瓶颈定位**：DCC 定位知识传递断裂点；ICP 识别难以表达的模块类型
- **回归检测**：CST 趋势线确保新改动不引入回归
- **目标**：20/20 模块 ZFPR=1.0，且 AL≥0.7
