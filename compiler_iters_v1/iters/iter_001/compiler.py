#!/usr/bin/env python3
"""
Compiler: YAML + nested graph → BSV RTL code
Iteration 001 - Initial baseline compiler

Architecture:
1. Read YAML file system (project.yaml, types.yaml, module YAMLs)
2. Phase 1: Collect all type definitions, generate type RTL
3. Phase 2: Traverse module graph bottom-up, collect knowledge, generate module RTL
4. Call coding agent (ccb) for code generation
5. Run bsc compilation and testbench simulation

Strategy: Two-Phase + Bottom-Up
"""

import os
import sys
import json
import yaml
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# =============================================================================
# Configuration
# =============================================================================

BSC_BIN = "/data/mmh/vibe-grpah-HDL/blue-rdma/bsc-2022.01-ubuntu-20.04/bin"
BSC = f"{BSC_BIN}/bsc"
BLUE_RDMA_SRC = "/data/mmh/vibe-grpah-HDL/blue-rdma/src"
BLUE_RDMA_TEST = "/data/mmh/vibe-grpah-HDL/blue-rdma/test"
MAKEFILE_BASE = "/data/mmh/vibe-grpah-HDL/blue-rdma/Makefile.base"
CCB = "ccb"

# Build flags from Makefile.base
BLUESIMFLAGS = "-parallel-sim-link 16"
SCHEDFLAGS = "-show-schedule -sched-dot"
DEBUGFLAGS = "-check-assert -continue-after-errors -keep-fires -keep-inlined-boundaries -show-method-bvi -show-method-conf -show-module-use -show-range-conflict -show-stats -warn-action-shadowing -warn-method-urgency -promote-warnings ALL"
RUNTIMEFLAGS = "+RTS -K4095M -RTS"
MISCFLAGS = "-print-flags -show-timestamps -steps 6000000"

SIM_TIMEOUT = 180  # 3 minutes max per simulation

# =============================================================================
# YAML Loader
# =============================================================================

class YAMLLoader:
    """Load and parse the YAML file system."""

    def __init__(self, yaml_dir):
        self.yaml_dir = Path(yaml_dir)
        self.project = None
        self.types = {}
        self.modules = {}

    def load_all(self):
        """Load all YAML files from the directory."""
        # Load project.yaml if exists
        project_file = self.yaml_dir / "project.yaml"
        if project_file.exists():
            with open(project_file) as f:
                self.project = yaml.safe_load(f)

        # Load types.yaml if exists
        types_file = self.yaml_dir / "types.yaml"
        if types_file.exists():
            with open(types_file) as f:
                data = yaml.safe_load(f)
                if data and 'types' in data:
                    for t in data['types']:
                        self.types[t['id']] = t

        # Load all module YAML files
        for yf in sorted(self.yaml_dir.glob("*.yaml")):
            if yf.name in ('project.yaml', 'types.yaml'):
                continue
            with open(yf) as f:
                data = yaml.safe_load(f)
                if data:
                    name = data.get('meta', {}).get('name', yf.stem)
                    self.modules[name] = {
                        'data': data,
                        'path': str(yf)
                    }
        return self

# =============================================================================
# Knowledge Collector
# =============================================================================

class KnowledgeCollector:
    """Collect and merge knowledge from multiple levels for a module."""

    def __init__(self, loader):
        self.loader = loader

    def collect_for_module(self, module_name, target_lang="bsv"):
        """Collect all relevant knowledge for generating a module."""
        module = self.loader.modules.get(module_name)
        if not module:
            return None

        data = module['data']
        knowledge_parts = []

        # L0: Language-level knowledge
        knowledge_parts.append(self._get_language_knowledge(target_lang))

        # L1: Project-level knowledge
        if self.loader.project:
            proj_knowledge = self.loader.project.get('knowledge', {})
            if target_lang in proj_knowledge:
                knowledge_parts.append(f"## Project-level knowledge\n{proj_knowledge[target_lang]}")

        # L2/L3: Module-level knowledge (interface + behavior)
        knowledge_parts.append(self._format_module_knowledge(data, target_lang))

        # Collect knowledge from connected modules (up/down N layers)
        connected_knowledge = self._collect_connected_knowledge(module_name, data, target_lang)
        if connected_knowledge:
            knowledge_parts.append(connected_knowledge)

        return "\n\n".join(knowledge_parts)

    def _get_language_knowledge(self, lang):
        """Get L0 language-level knowledge."""
        if lang == "bsv":
            return """## Language Knowledge (BSV/Bluespec SystemVerilog)

BSV is a hardware description language based on SystemVerilog with Guarded Atomic Actions.

Key constructs:
- `typedef` for type aliases: `typedef Bit#(32) MyType;`
- `typedef enum { ... } MyEnum deriving(Bits, Bounded, Eq, FShow);`
- `typedef struct { Type field; } MyStruct deriving(Bits, Bounded, FShow);`
- Numeric type functions: `TAdd#(a,b)`, `TSub#(a,b)`, `TMul#(a,b)`, `TDiv#(a,b)`, `TLog#(a)`, `TExp#(a)`
- `SizeOf#(Type)` returns bit width of a type
- `valueOf(Type)` returns numeric value of a numeric type
- Interface: `interface MyIfc; method Type methodName(Args); endinterface`
- Module: `module mkMyMod(MyIfc); ... endmodule` with `(* synthesize *)` if needed
- Rules: `rule doSomething; ... endrule` with optional attributes like `(* fire_when_enabled *)`
- Registers: `Reg#(Type) regName <- mkReg(initVal);` or `<- mkRegU;`
- FIFOs: `FIFOF#(Type) fifoName <- mkFIFOF;`
- Ehr/CReg: `Reg#(Type) regName[2] <- mkCReg(2, initVal);`
- Action methods modify state, non-Action methods read state
- `import ModuleName :: *;` for imports
- `function Type funcName(Args); ... endfunction`
- `provisos` clause constrains type parameters: `provisos(Bits#(a, sz), Add#(x, y, z))`
- Pack/unpack: `pack(value)` converts to bits, `unpack(bitVal)` converts from bits
- `Bit#(n)` is an n-bit vector, `Bool` is boolean
- Struct fields accessed with dot notation: `structVal.fieldName`
- `Maybe#(T)` is tagged union: `tagged Valid val` or `tagged Invalid`
- `case` statement with `matches` for pattern matching on tagged unions
- When generating BSV, include `import` statements for all referenced modules/types
- Always include proper `provisos` on parameterized modules/functions
"""
        return ""

    def _format_module_knowledge(self, data, target_lang):
        """Format L2/L3 module-level knowledge."""
        parts = []
        meta = data.get('meta', {})
        parts.append(f"## Module: {meta.get('name', 'unknown')}")
        if meta.get('description'):
            parts.append(f"\n{meta['description']}")

        # L2: Interface contract
        parts.append("\n### Interface Contract (L2)")
        if data.get('ports'):
            parts.append("Ports:")
            for p in data['ports']:
                parts.append(f"  - {p['name']}: {p['direction']} {p['type']}" +
                           (f" // {p['description']}" if p.get('description') else ""))

        if data.get('methods'):
            parts.append("Methods:")
            for m in data['methods']:
                effect = m.get('effect', '')
                parts.append(f"  - {m['name']}: {m.get('return_type', 'Action')} ({m.get('args', '')})" +
                           (f" [{effect}]" if effect else "") +
                           (f" // {m['description']}" if m.get('description') else ""))

        if data.get('sub_interfaces'):
            parts.append("Sub-interfaces:")
            for si in data['sub_interfaces']:
                parts.append(f"  - {si['name']}: {si['type']}")

        # L3: Behavior knowledge
        if data.get('behavior'):
            parts.append("\n### Behavior Knowledge (L3)")
            parts.append(data['behavior'].get('description', ''))

        if data.get('state_elements'):
            parts.append("\n### State Elements")
            for s in data['state_elements']:
                parts.append(f"  - {s['name']}: {s.get('type', '')} = {s.get('init', '')}" +
                           (f" // {s['description']}" if s.get('description') else ""))

        if data.get('rules'):
            parts.append("\n### Rules")
            for r in data['rules']:
                parts.append(f"  - {r['name']}: {r.get('description', '')}")
                if r.get('condition'):
                    parts.append(f"    Condition: {r['condition']}")
                if r.get('body'):
                    parts.append(f"    Body: {r['body']}")

        # L4/L5: Connection and port knowledge
        if target_lang in data.get('knowledge', {}):
            parts.append(f"\n### Language-specific knowledge")
            parts.append(data['knowledge'][target_lang])

        # Parameters
        if data.get('parameters'):
            parts.append("\n### Parameters")
            for param in data['parameters']:
                parts.append(f"  - {param['name']}: {param.get('kind', '')}" +
                           (f" // {param['description']}" if param.get('description') else ""))

        # Test method
        if data.get('test_method'):
            parts.append("\n### Test Method")
            parts.append(data['test_method'].get('description', ''))

        return "\n".join(parts)

    def _collect_connected_knowledge(self, module_name, data, target_lang):
        """Collect knowledge from connected modules."""
        connections = data.get('connections', [])
        nodes = data.get('nodes', [])
        if not connections and not nodes:
            return ""

        parts = ["## Connected Module Knowledge"]

        # Collect sub-module interfaces
        for node in nodes:
            ref = node.get('ref', '')
            node_id = node.get('id', '')
            parts.append(f"\n### Sub-module: {node_id} (ref: {ref})")

            # Try to load sub-module interface
            if ref:
                sub_name = Path(ref).stem
                if sub_name in self.loader.modules:
                    sub = self.loader.modules[sub_name]['data']
                    if sub.get('ports'):
                        parts.append("Ports:")
                        for p in sub['ports']:
                            parts.append(f"  - {p['name']}: {p['direction']} {p['type']}")
                    if sub.get('methods'):
                        parts.append("Methods:")
                        for m in sub['methods']:
                            parts.append(f"  - {m['name']}: {m.get('return_type', 'Action')}")

        return "\n".join(parts)

# =============================================================================
# Code Generator (via coding agent)
# =============================================================================

class CodeGenerator:
    """Generate BSV code by calling the coding agent (ccb)."""

    def __init__(self, output_dir, iter_dir):
        self.output_dir = Path(output_dir)
        self.iter_dir = Path(iter_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_module(self, module_name, knowledge_text, module_data):
        """Generate BSV code for a module using the coding agent."""
        prompt = self._build_prompt(module_name, knowledge_text, module_data)

        # Write prompt to file for debugging
        prompt_file = self.iter_dir / "logs" / f"prompt_{module_name}.md"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        with open(prompt_file, 'w') as f:
            f.write(prompt)

        # Call ccb to generate code
        output_file = self.output_dir / f"{module_name}.bsv"

        cmd = [
            CCB, "-p", prompt,
            "--permission-mode", "auto",
            "--output-format", "text",
            "--print"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout for code generation
                cwd=str(self.iter_dir)
            )

            # Extract BSV code from the output
            bsv_code = self._extract_bsv(result.stdout)

            if bsv_code:
                with open(output_file, 'w') as f:
                    f.write(bsv_code)
                return True, bsv_code, result.stderr
            else:
                # Save raw output for debugging
                with open(str(output_file) + ".raw", 'w') as f:
                    f.write(result.stdout)
                return False, "", f"No BSV code found in output. Raw: {result.stdout[:500]}"

        except subprocess.TimeoutExpired:
            return False, "", "Code generation timed out"
        except Exception as e:
            return False, "", str(e)

    def _build_prompt(self, module_name, knowledge_text, module_data):
        """Build the prompt for the coding agent."""
        module_type = module_data.get('module_type', 'module')

        base_prompt = f"""You are a Bluespec SystemVerilog (BSV) code generator. Generate a BSV source file based on the specification below.

The module name is: {module_name}

{knowledge_text}

## Generation Instructions

1. Generate ONLY the BSV source code for the module described above.
2. Output the code in a ```bsv code block.
3. Include all necessary `import` statements.
4. Do NOT include any explanation, only the code block.
5. If this is a type-only file (no module/interface), output typedefs and functions only.
6. For modules: implement the complete interface and all methods.
7. Include proper `provisos` on all parameterized constructs.
8. For testbench modules: implement the complete testbench with stimulus generation and checking logic.
9. The module must match the interface specification exactly - same method names, same port names, same types.

## Module type: {module_type}

Generate the BSV code now."""
        return base_prompt

    def _extract_bsv(self, text):
        """Extract BSV code from agent output."""
        import re
        # Try ```bsv ... ``` block first
        match = re.search(r'```bsv\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try ```bluespec ... ```
        match = re.search(r'```bluespec\s*\n(.*?)```', text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Try ``` ... ``` with BSV keywords
        match = re.search(r'```\s*\n(.*?)```', text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if any(kw in content for kw in ['typedef', 'module', 'interface', 'endmodule', 'import ', 'Bit#']):
                return content

        return ""

# =============================================================================
# BSV Compiler & Tester
# =============================================================================

class BSVCompiler:
    """Compile and test BSV code using bsc."""

    def __init__(self, iter_dir):
        self.iter_dir = Path(iter_dir)
        self.bsc = BSC

    def compile_module(self, bsv_file, build_dir):
        """Compile a single BSV module to check for syntax errors."""
        build_dir = Path(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            self.bsc,
            "-elab", "-sim",
            "-p", f"+:{BLUE_RDMA_SRC}",
            "-p", f"+:{bsv_file.parent}",
            "-bdir", str(build_dir),
            "-info-dir", str(build_dir),
            "-simdir", str(build_dir),
            "-u",
            "-check-assert",
            "-steps", "6000000",
            "+RTS", "-K4095M", "-RTS",
            str(bsv_file)
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Compilation timed out"
        except Exception as e:
            return False, str(e)

    def run_testbench(self, bsv_file, test_module, testbench_file, build_dir):
        """Compile and run a testbench."""
        build_dir = Path(build_dir)
        build_dir.mkdir(parents=True, exist_ok=True)

        out_dir_flags = [
            "-bdir", str(build_dir),
            "-info-dir", str(build_dir),
            "-simdir", str(build_dir),
        ]

        src_paths = [
            "-p", f"+:{BLUE_RDMA_SRC}",
            "-p", f"+:{BLUE_RDMA_TEST}",
            "-p", f"+:{bsv_file.parent}",
        ]

        common_flags = [
            "-u", "-check-assert",
            "-steps", "6000000",
            "+RTS", "-K4095M", "-RTS",
        ]

        # Step 1: Compile testbench
        compile_cmd = [self.bsc, "-elab", "-sim"] + src_paths + out_dir_flags + common_flags + ["-g", test_module, str(testbench_file)]

        try:
            result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                return False, f"Compilation failed:\n{result.stderr[-2000:]}"
        except subprocess.TimeoutExpired:
            return False, "Testbench compilation timed out"

        # Step 2: Link
        link_cmd = [self.bsc, "-sim"] + out_dir_flags + ["-e", test_module, "-o", str(build_dir / f"{test_module}.sh")]

        try:
            result = subprocess.run(link_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                return False, f"Linking failed:\n{result.stderr[-1000:]}"
        except subprocess.TimeoutExpired:
            return False, "Linking timed out"

        # Step 3: Simulate
        sim_script = build_dir / f"{test_module}.sh"
        if not sim_script.exists():
            return False, "Simulation script not found"

        try:
            result = subprocess.run(
                [str(sim_script)],
                capture_output=True,
                text=True,
                timeout=SIM_TIMEOUT,
                cwd=str(build_dir)
            )

            # Check for pass/fail
            output = result.stdout + result.stderr
            passed = result.returncode == 0 and "PASS" in output
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Simulation timed out"

# =============================================================================
# Metrics Collector
# =============================================================================

class MetricsCollector:
    """Collect and store evaluation metrics."""

    def __init__(self, iter_dir):
        self.iter_dir = Path(iter_dir)
        self.metrics_dir = self.iter_dir / "metrics"
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.data = {
            'fpc': {},  # First-pass compilation per module
            'tpr': {},  # Test pass rate per module
            'sc': {},   # Semantic completeness
            'id': {},   # Information density
            'gt': {},   # Generation time
        }

    def record_fpc(self, module_name, success, errors=""):
        self.data['fpc'][module_name] = {'success': success, 'errors': str(errors)[:500]}

    def record_tpr(self, module_name, test_results):
        self.data['tpr'][module_name] = test_results

    def record_metrics(self, module_name, bsv_bytes, yaml_bytes, gen_time):
        self.data['sc'][module_name] = {'bsv_bytes': bsv_bytes}
        self.data['id'][module_name] = {'bsv_bytes': bsv_bytes, 'yaml_bytes': yaml_bytes,
                                         'id_ratio': yaml_bytes / max(bsv_bytes, 1)}
        self.data['gt'][module_name] = {'gen_time_seconds': gen_time}

    def save_summary(self, iteration_id):
        """Save summary metrics."""
        summary = {
            'iteration_id': iteration_id,
            'timestamp': datetime.now().isoformat(),
            'fpc': self._calc_fpc(),
            'tpr': self._calc_tpr(),
            'module_details': {}
        }

        for mod in set(list(self.data['fpc'].keys()) + list(self.data['tpr'].keys())):
            summary['module_details'][mod] = {
                'fpc': self.data['fpc'].get(mod, {}),
                'tpr': self.data['tpr'].get(mod, {}),
                'id': self.data['id'].get(mod, {}),
                'gt': self.data['gt'].get(mod, {}),
            }

        with open(self.metrics_dir / f"summary_{iteration_id}.json", 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        return summary

    def _calc_fpc(self):
        fpc_data = self.data['fpc']
        if not fpc_data:
            return 0.0
        success_count = sum(1 for v in fpc_data.values() if v.get('success'))
        return success_count / len(fpc_data)

    def _calc_tpr(self):
        tpr_data = self.data['tpr']
        total = 0
        passed = 0
        for mod_results in tpr_data.values():
            for tc_name, tc_result in mod_results.items():
                total += 1
                if tc_result == 'PASS':
                    passed += 1
        return passed / max(total, 1)

# =============================================================================
# Test Case Definitions
# =============================================================================

TEST_CASES = {
    "T01_Settings": {
        "bsv_file": f"{BLUE_RDMA_SRC}/Settings.bsv",
        "module_type": "typedef_only",
        "has_testbench": False,
        "test_file": None,
        "test_modules": [],
        "dependencies": [],
    },
    "T02_Headers": {
        "bsv_file": f"{BLUE_RDMA_SRC}/Headers.bsv",
        "module_type": "typedef_and_functions",
        "has_testbench": False,
        "test_file": None,
        "test_modules": [],
        "dependencies": [],
    },
    "T03_Utils": {
        "bsv_file": f"{BLUE_RDMA_SRC}/Utils.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestUtils.bsv",
        "test_modules": ["mkTestPsnFunc"],
        "dependencies": ["Headers", "PrimUtils"],
    },
    "T04_SpecialFIFOF": {
        "bsv_file": f"{BLUE_RDMA_SRC}/SpecialFIFOF.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestSpecialFIFOF.bsv",
        "test_modules": ["mkTestCacheFIFO2", "mkTestScanFIFOF", "mkTestSearchFIFOF", "mkTestVectorSearch"],
        "dependencies": ["PrimUtils"],
    },
    "T05_Arbitration": {
        "bsv_file": f"{BLUE_RDMA_SRC}/Arbitration.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestArbitration.bsv",
        "test_modules": ["mkTestPipeOutArbiter", "mkTestServerArbiter", "mkTestClientArbiter"],
        "dependencies": ["PrimUtils", "Utils"],
    },
    "T06_WorkCompGen": {
        "bsv_file": f"{BLUE_RDMA_SRC}/WorkCompGen.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestWorkCompGen.bsv",
        "test_modules": ["mkTestWorkCompGenNormalCaseRQ", "mkTestWorkCompGenErrFlushCaseRQ",
                         "mkTestWorkCompGenNormalCaseSQ", "mkTestWorkCompGenErrFlushCaseSQ"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils"],
    },
    "T07_ExtractAndPrependPipeOut": {
        "bsv_file": f"{BLUE_RDMA_SRC}/ExtractAndPrependPipeOut.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestExtractAndPrependPipeOut.bsv",
        "test_modules": ["mkTestHeaderAndDataStreamConversion", "mkTestPrependHeaderBeforeEmptyDataStream",
                         "mkTestExtractHeaderWithPayloadLessThanOneFrag", "mkTestExtractHeaderLongerThanDataStream",
                         "mkTestExtractAndPrependHeader"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils"],
    },
    "T08_DupReadAtomicCache": {
        "bsv_file": f"{BLUE_RDMA_SRC}/DupReadAtomicCache.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestDupReadAtomicCache.bsv",
        "test_modules": ["mkTestDupReadAtomicCache", "mkTestCacheFIFO"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T09_InputPktHandle": {
        "bsv_file": f"{BLUE_RDMA_SRC}/InputPktHandle.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestInputPktHandle.bsv",
        "test_modules": ["mkTestCalculateRandomPktLen", "mkTestCalculatePktLenEqPMTU",
                         "mkTestCalculateZeroPktLen", "mkTestReceiveCNP"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T10_SendQ": {
        "bsv_file": f"{BLUE_RDMA_SRC}/SendQ.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestSendQ.bsv",
        "test_modules": ["mkTestSendQueueRawPktCase", "mkTestSendQueueNormalCase",
                         "mkTestSendQueueNoPayloadCase", "mkTestSendQueueZeroPayloadLenCase"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T11_ReqGenSQ": {
        "bsv_file": f"{BLUE_RDMA_SRC}/ReqGenSQ.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestReqGenSQ.bsv",
        "test_modules": ["mkTestReqGenNormalCase", "mkTestReqGenZeroLenCase", "mkTestReqGenDmaReadErrCase"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils", "SpecialFIFOF"],
    },
    "T12_QueuePair": {
        "bsv_file": f"{BLUE_RDMA_SRC}/QueuePair.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestQueuePair.bsv",
        "test_modules": ["mkTestQueuePairCreate", "mkTestQueuePairDestroy", "mkTestQueuePairStateTransition",
                         "mkTestQueuePairError", "mkTestQueuePairNormalOp", "mkTestQueuePairMultiQP",
                         "mkTestQueuePairRQPath"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils", "SpecialFIFOF", "SendQ", "ReqGenSQ"],
    },
    "T13_RetryHandleSQ": {
        "bsv_file": f"{BLUE_RDMA_SRC}/RetryHandleSQ.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestRetryHandleSQ.bsv",
        "test_modules": ["mkTestRetry", "mkTestRetryRNR", "mkTestRetrySeqErr", "mkTestRetryTimeout",
                         "mkTestRetryNested", "mkTestRetryAll", "mkTestRetryMultiple"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T14_RespHandleSQ": {
        "bsv_file": f"{BLUE_RDMA_SRC}/RespHandleSQ.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestRespHandleSQ.bsv",
        "test_modules": ["mkTestRespNormal", "mkTestRespDup", "mkTestRespGhost", "mkTestRespError",
                         "mkTestRespNAK", "mkTestRespMulti", "mkTestRespOutOfOrder",
                         "mkTestRespWithRetry", "mkTestRespAll", "mkTestRespCorner"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils", "SpecialFIFOF"],
    },
    "T15_PayloadConAndGen": {
        "bsv_file": f"{BLUE_RDMA_SRC}/PayloadConAndGen.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestPayloadConAndGen.bsv",
        "test_modules": ["mkTestPayloadNormal", "mkTestPayloadSegmented", "mkTestPayloadDmaNormal",
                         "mkTestPayloadDmaCancel", "mkTestPayloadAddrChunk", "mkTestPayloadMulti",
                         "mkTestPayloadBoundary"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T16_PayloadGen": {
        "bsv_file": f"{BLUE_RDMA_SRC}/PayloadGen.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestPayloadGen.bsv",
        "test_modules": [],  # 13 testcases - need to parse from file
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T17_ReqHandleRQ": {
        "bsv_file": f"{BLUE_RDMA_SRC}/ReqHandleRQ.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestReqHandleRQ.bsv",
        "test_modules": [],  # 9 testcases
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T18_MetaData": {
        "bsv_file": f"{BLUE_RDMA_SRC}/MetaData.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestMetaData.bsv",
        "test_modules": [],  # 7 testcases
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils", "Controller", "QueuePair", "Arbitration"],
    },
    "T19_Controller": {
        "bsv_file": f"{BLUE_RDMA_SRC}/Controller.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestController.bsv",
        "test_modules": ["mkTestCntrlInVec"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils"],
    },
    "T20_TransportLayer": {
        "bsv_file": f"{BLUE_RDMA_SRC}/TransportLayer.bsv",
        "module_type": "module",
        "has_testbench": True,
        "test_file": f"{BLUE_RDMA_TEST}/TestTransportLayer.bsv",
        "test_modules": ["mkTestTransportLayerNormalCase", "mkTestTransportLayerErrorCase"],
        "dependencies": ["DataTypes", "Headers", "PrimUtils", "Utils", "SpecialFIFOF", "Controller",
                        "QueuePair", "MetaData", "SendQ", "ReqGenSQ", "RetryHandleSQ", "RespHandleSQ",
                        "PayloadConAndGen", "PayloadGen", "ReqHandleRQ", "Arbitration", "WorkCompGen",
                        "ExtractAndPrependPipeOut", "DupReadAtomicCache", "InputPktHandle"],
    },
}

# =============================================================================
# Main Compiler Pipeline
# =============================================================================

class CompilerPipeline:
    """Main compiler pipeline orchestrator."""

    def __init__(self, iter_dir, yaml_dir, parallel=4):
        self.iter_dir = Path(iter_dir)
        self.yaml_dir = Path(yaml_dir)
        self.parallel = parallel
        self.generated_dir = self.iter_dir / "generated"
        self.build_dir = self.iter_dir / "build"
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.build_dir.mkdir(parents=True, exist_ok=True)

        self.loader = None
        self.collector = None
        self.generator = None
        self.compiler = BSVCompiler(iter_dir)
        self.metrics = MetricsCollector(iter_dir)

    def run(self, test_cases=None):
        """Run the full compiler pipeline."""
        if test_cases is None:
            test_cases = list(TEST_CASES.keys())

        log_file = self.iter_dir / "logs" / "pipeline.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        results = {}

        # Phase 1: Generate types
        self._log("=" * 60)
        self._log(f"Iteration 001 - Compiler Pipeline Start")
        self._log(f"Time: {datetime.now().isoformat()}")
        self._log("=" * 60)

        # Process test cases
        for tc_name in test_cases:
            if tc_name not in TEST_CASES:
                self._log(f"Unknown test case: {tc_name}")
                continue

            tc = TEST_CASES[tc_name]
            self._log(f"\n--- Processing {tc_name} ---")

            t_start = time.time()

            # Check if YAML exists for this test case
            yaml_path = self._find_yaml(tc_name)
            if not yaml_path:
                self._log(f"  SKIP: No YAML found for {tc_name}")
                results[tc_name] = {'status': 'SKIP', 'reason': 'No YAML'}
                continue

            # Load YAML
            try:
                with open(yaml_path) as f:
                    module_data = yaml.safe_load(f)
            except Exception as e:
                self._log(f"  ERROR loading YAML: {e}")
                results[tc_name] = {'status': 'ERROR', 'reason': str(e)}
                continue

            # Generate BSV
            module_name = module_data.get('meta', {}).get('name', tc_name)
            collector = KnowledgeCollector(self.loader) if self.loader else None

            # For now, directly use the YAML to build a prompt
            knowledge = self._build_knowledge_from_yaml(module_data, tc)

            generator = CodeGenerator(self.generated_dir, self.iter_dir)
            success, code, msg = generator.generate_module(module_name, knowledge, module_data)
            gen_time = time.time() - t_start

            self._log(f"  Generation: {'OK' if success else 'FAIL'} ({gen_time:.1f}s)")

            if not success:
                self.metrics.record_fpc(tc_name, False, msg)
                self.metrics.record_metrics(tc_name, 0, os.path.getsize(yaml_path), gen_time)
                results[tc_name] = {'status': 'GEN_FAIL', 'reason': msg[:200]}
                continue

            bsv_path = self.generated_dir / f"{module_name}.bsv"

            # Compile check (FPC)
            build_mod_dir = self.build_dir / tc_name
            compile_ok, compile_msg = self.compiler.compile_module(bsv_path, build_mod_dir)
            self._log(f"  Compile: {'OK' if compile_ok else 'FAIL'}")
            self.metrics.record_fpc(tc_name, compile_ok, compile_msg if not compile_ok else "")

            bsv_size = os.path.getsize(bsv_path) if bsv_path.exists() else 0
            yaml_size = os.path.getsize(yaml_path)
            self.metrics.record_metrics(tc_name, bsv_size, yaml_size, gen_time)

            # Test (TPR) if applicable
            test_results = {}
            if tc['has_testbench'] and tc['test_file'] and tc['test_modules'] and compile_ok:
                for test_mod in tc['test_modules']:
                    test_build_dir = self.build_dir / tc_name / test_mod
                    test_ok, test_msg = self.compiler.run_testbench(
                        bsv_path, test_mod, tc['test_file'], test_build_dir
                    )
                    test_results[test_mod] = 'PASS' if test_ok else 'FAIL'
                    self._log(f"    Test {test_mod}: {'PASS' if test_ok else 'FAIL'}")
                self.metrics.record_tpr(tc_name, test_results)

            results[tc_name] = {
                'status': 'DONE',
                'compile_ok': compile_ok,
                'test_results': test_results,
                'gen_time': gen_time,
            }

        # Save summary
        summary = self.metrics.save_summary("iter_001")

        # Write results
        with open(self.iter_dir / "logs" / "results.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self._log(f"\n{'='*60}")
        self._log(f"Pipeline complete. FPC={summary['fpc']:.2f}, TPR={summary['tpr']:.2f}")
        self._log(f"Results saved to {self.iter_dir / 'logs' / 'results.json'}")

        return results, summary

    def _find_yaml(self, tc_name):
        """Find the YAML file for a test case."""
        # Try direct name match
        yaml_path = self.yaml_dir / f"{tc_name}.yaml"
        if yaml_path.exists():
            return yaml_path

        # Try module name without prefix
        module_name = tc_name.replace("T01_", "").replace("T02_", "").replace("T03_", "").replace("T04_", "").replace("T05_", "").replace("T06_", "").replace("T07_", "").replace("T08_", "").replace("T09_", "").replace("T10_", "").replace("T11_", "").replace("T12_", "").replace("T13_", "").replace("T14_", "").replace("T15_", "").replace("T16_", "").replace("T17_", "").replace("T18_", "").replace("T19_", "").replace("T20_", "")
        yaml_path = self.yaml_dir / f"{module_name}.yaml"
        if yaml_path.exists():
            return yaml_path

        return None

    def _build_knowledge_from_yaml(self, module_data, tc_info):
        """Build knowledge text from YAML data for prompt generation."""
        # This is the core knowledge merging function
        parts = []

        # Language knowledge (L0)
        parts.append("""## Bluespec SystemVerilog (BSV) Language Reference

BSV uses Guarded Atomic Actions (GAA) semantics. Key syntax:
- `typedef Bit#(N) TypeName;` - Type alias
- `typedef enum {A, B} MyEnum deriving(Bits, Bounded, Eq, FShow);`
- `typedef struct { Type f; } MyStruct deriving(Bits, Bounded, FShow);`
- `interface IfcName; method Type m(args); endinterface`
- `module mkMod(IfcName); ... endmodule`
- `Reg#(T) r <- mkReg(v);` / `<- mkRegU;`
- `FIFOF#(T) f <- mkFIFOF;`
- `function Type f(args); ... endfunction`
- `rule rName; ... endrule`
- `provisos(Bits#(a, sz), Add#(x,y,z))`
- `SizeOf#(T)` - bit width; `valueOf(T)` - numeric value
- `TAdd#()`, `TSub#()`, `TMul#()`, `TDiv#()`, `TLog#()`, `TExp#()` - numeric type functions
- `pack(v)` / `unpack(b)` - convert to/from bits
- `Maybe#(T)` with `tagged Valid v` / `tagged Invalid`
- `import Module::*;` for imports
""")

        # YAML description
        meta = module_data.get('meta', {})
        module_type = tc_info.get('module_type', 'module')

        parts.append(f"## Module: {meta.get('name', 'unknown')}")
        parts.append(f"Type: {module_type}")
        if meta.get('description'):
            parts.append(f"\n{meta['description']}")

        # Design knowledge section
        dk = module_data.get('design_knowledge', {})
        if dk:
            if dk.get('description'):
                parts.append(f"\n### Design Description\n{dk['description']}")
            if dk.get('structural_info'):
                parts.append(f"\n### Structure\n{dk['structural_info']}")
            if dk.get('behavioral_info'):
                parts.append(f"\n### Behavior\n{dk['behavioral_info']}")

        # Type definitions
        if module_data.get('typedefs'):
            parts.append("\n### Type Definitions to Generate")
            for td in module_data['typedefs']:
                parts.append(f"- `{td['name']}`: {td.get('description', '')}")
                if td.get('bsv_equivalent'):
                    parts.append(f"  BSV equivalent: `{td['bsv_equivalent']}`")

        # Enum definitions
        if module_data.get('enums'):
            parts.append("\n### Enum Types")
            for enum in module_data['enums']:
                parts.append(f"- `{enum['name']}`: {enum.get('description', '')}")
                if enum.get('variants'):
                    parts.append(f"  Variants: {', '.join(enum['variants'])}")
                if enum.get('bsv_equivalent'):
                    parts.append(f"  BSV equivalent: `{enum['bsv_equivalent']}`")

        # Struct definitions
        if module_data.get('structs'):
            parts.append("\n### Struct Types")
            for struct in module_data['structs']:
                parts.append(f"- `{struct['name']}`: {struct.get('description', '')}")
                if struct.get('fields'):
                    for fld in struct['fields']:
                        parts.append(f"  - {fld['name']}: {fld.get('type', '')} // {fld.get('description', '')}")

        # Functions
        if module_data.get('functions'):
            parts.append("\n### Functions")
            for func in module_data['functions']:
                parts.append(f"- `{func['name']}`: {func.get('description', '')}")
                if func.get('bsv_equivalent'):
                    parts.append(f"  BSV equivalent:\n```bsv\n{func['bsv_equivalent']}\n```")

        # Module definition
        if module_data.get('module_def'):
            md = module_data['module_def']
            parts.append("\n### Module Interface")
            parts.append(f"Module name: {md.get('name', meta.get('name', 'unknown'))}")
            if md.get('interface_name'):
                parts.append(f"Interface: {md['interface_name']}")
            if md.get('methods'):
                parts.append("Methods:")
                for m in md['methods']:
                    parts.append(f"  - {m['name']}: {m.get('return_type', 'Action')} ({m.get('args', '')})")
                    if m.get('description'):
                        parts.append(f"    {m['description']}")
            if md.get('ports'):
                parts.append("Ports:")
                for p in md['ports']:
                    parts.append(f"  - {p['name']}: {p['direction']} {p['type']}")

        # Implementation
        if module_data.get('implementation'):
            impl = module_data['implementation']
            parts.append("\n### Implementation Details")
            if impl.get('registers'):
                parts.append("Registers:")
                for r in impl['registers']:
                    parts.append(f"  - {r['name']}: {r.get('type', '')} = {r.get('init', '')}")
            if impl.get('rules'):
                parts.append("Rules:")
                for r in impl['rules']:
                    parts.append(f"  - {r['name']}: {r.get('description', '')}")
            if impl.get('submodules'):
                parts.append("Sub-modules:")
                for s in impl['submodules']:
                    parts.append(f"  - {s['name']}: {s.get('type', '')}")

        # Generation instructions
        parts.append(f"""
## Generation Instructions
1. Generate ONLY the BSV source code inside a ```bsv code block.
2. Include all necessary `import` statements at the top.
3. Use the exact type names and module names specified above.
4. For typedefs/enums/structs: generate them exactly as specified in their BSV equivalent field.
5. Make sure to handle all provisos correctly.
6. Do NOT include any explanation text - ONLY the ```bsv code block.
""")

        return "\n\n".join(parts)

    def _log(self, msg):
        log_file = self.iter_dir / "logs" / "pipeline.log"
        print(msg)
        with open(log_file, 'a') as f:
            f.write(msg + "\n")

# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compiler Pipeline")
    parser.add_argument("--iter-dir", default=".", help="Iteration directory")
    parser.add_argument("--yaml-dir", default="yaml", help="YAML files directory")
    parser.add_argument("--test-cases", nargs="*", help="Test cases to run")
    parser.add_argument("--parallel", type=int, default=4, help="Parallel workers")
    args = parser.parse_args()

    pipeline = CompilerPipeline(args.iter_dir, args.yaml_dir, args.parallel)
    results, summary = pipeline.run(args.test_cases)

    # Exit with summary
    print(f"\nFinal: FPC={summary['fpc']:.2f}, TPR={summary['tpr']:.2f}")
