# Project-Specific Knowledge (blue-rdma)

This file contains ONLY project-specific conventions. For BSV language syntax and patterns, see the shared language template.

## Available Project Libraries

- **PAClib**: Provides `PipeOut#(T)`, `mkFork`, pipeline stage primitives
- **PrimUtils**: Provides `CReg` (concurrent register), `mkCReg`, `toPipeOut` conversion

## Project Conventions
- Module names use PascalCase (e.g., `mkPipelinedArbiter`)
- Method names use camelCase (e.g., `grant`, `encode`)
- All numeric types use `numeric type` (not `Integer` for static parameters)
- One module per file, one interface per module
