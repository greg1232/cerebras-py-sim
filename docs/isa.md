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

### 3.2 Global Memory Operations
- **LDR_GLOBAL [Address, Register]:** Loads data from the global address space (Weight Server or remote PE SRAM) into a register. This operation internally triggers mesh movement to route the request to the target address.
- **STR_GLOBAL [Address, Register]:** Stores data from a register into the global address space. This operation internally utilizes the mesh to transport data to the destination.
- **Internal Mesh Primitives:** The hardware utilizes internal primitives (`SEND_*`, `RECV_*`, `WAIT_*`) to implement these global operations. These are not exposed as user-accessible instructions.

### 3.3 Memory Operations
- **Load/Store:** Accesses the 48KB local SRAM.
- **DSD (Data Structure Descriptor) Access:** Indirect addressing for tensor slices and strides.

### 3.4 Control Flow
- **Branching:** Conditional execution based on SIMD mask registers.
- **Sync:** Block-Local Barrier. Synchronizes all Processing Elements (PEs) within a single block. There is no global SYNC instruction in the ISA; global synchronization is managed by the host via the `CS3Queue`.

## 4. Hardware Constraints
The mesh interconnect hardware is abstracted behind the global memory model. While the physical mesh exists, the programmer interacts with it via `LDR_GLOBAL` and `STR_GLOBAL`. Any underlying `SEND_*` or `RECV_*` operations are handled by the hardware to facilitate these global memory accesses.

## 5. SIMD Execution Model
Instructions are executed in a Single Instruction, Multiple Data (SIMD) fashion. A mask register determines which of the 8 lanes are active for a given operation.

## 6. Dataflow Triggering
The ISA supports a "trigger" mechanism where instructions can be gated by the arrival of data via the global memory fabric, which internally utilizes the bidirectional mesh.
