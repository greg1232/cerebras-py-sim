# CS3 Instruction Set Architecture (ISA) Specification

## 1. Overview
The CS3 ISA is designed for high-throughput tensor operations and dataflow execution. Each core (Processing Element) operates on a SIMD-8 architecture, executing instructions on local SRAM and communicating via the bidirectional mesh.

## 2. Register File & State
- **SIMD Registers:** 8-wide vector registers for 16-bit/32-bit operations.
- **SRAM:** 48KB local memory mapped as a fast-access scratchpad.
- **Program Counter (PC):** Tracks current instruction execution.
- **Control State:** State machine for dataflow triggers (Wait for Data $\rightarrow$ Execute $\rightarrow$ Forward).

## 3. Instruction Categories

### 3.1 Compute Operations
- **SIMD Arithmetic:** Vector addition, subtraction, and multiplication across 8 lanes.
- **Fused Multiply-Add (FMA):** The primary compute primitive for AI workloads.
- **Activation Functions:** Hardware-accelerated ReLU, GeLU, and Sigmoid approximations.
- **Quantization/Casting:** Instructions for moving between FP16, BF16, and INT8.

### 3.2 Data Movement (Mesh)
- **Send [Direction, Register]:** Pushes data to the adjacent core in the specified direction (N, S, E, W).
- **Recv [Direction, Register]:** Blocks or triggers based on data arrival from a specific direction.
- **Broadcast:** Special primitives for row/column distribution.

### 3.3 Memory Operations
- **Load/Store:** Accesses the 48KB local SRAM.
- **DSD (Data Structure Descriptor) Access:** Indirect addressing for tensor slices and strides.

### 3.4 Control Flow
- **Branching:** Conditional execution based on SIMD mask registers.
- **Sync:** Block-Local Barrier. Synchronizes PEs only within the same block, not across the entire wafer.

## 4. Hardware Constraints
The mesh interconnect hardware enforces hierarchical block isolation. All `SEND_*` and `RECV_*` instructions are gated by the current Block ID. If a `SEND` operation attempts to cross a block boundary, it is treated as a NOP or triggers a hardware exception, depending on the system configuration.

## 5. SIMD Execution Model
Instructions are executed in a Single Instruction, Multiple Data (SIMD) fashion. A mask register determines which of the 8 lanes are active for a given operation.

## 6. Dataflow Triggering
The ISA supports a "trigger" mechanism where instructions are not merely sequential but can be gated by the arrival of packets on the 16-bit bidirectional mesh.
