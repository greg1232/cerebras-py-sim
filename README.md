# Cerebras CS3 Simulator

A high-fidelity architectural simulator for the Cerebras CS3 Wafer-Scale Engine (WSE). This project models the hardware architecture, interconnects, and execution environment to enable performance analysis and software development for massively parallel 2D mesh architectures.

## 🚀 Project Overview

The Cerebras-Sim is designed to model the CS3 WSE, featuring a massive array of 720,000 processing elements (PEs). It provides a full-stack simulation environment, from a high-level Python DSL down to a custom 32-bit ISA binary.

### Key Goals
- **Performance Analysis**: Estimate total runtime and identify bottlenecks using a hybrid performance/functional model.
- **Software Development**: Verify kernel correctness via a CUDA-like programming model before deploying to hardware.
- **Architectural Exploration**: Model the impact of mesh bisection bandwidth, latency, and SRAM constraints.

---

## 🏗️ Architecture

### Hardware Model
- **Processing Element (PE)**: Each core implements an 8-wide SIMD unit, vector registers, and a private **48KB local SRAM**.
- **Interconnect**: A 2D Mesh (800x900) where communication occurs via `SEND`/`RECV` primitives and global address space abstractions.
- **Memory Hierarchy**:
    - **Local SRAM**: Private high-speed memory per PE (analogous to CUDA Shared Memory).
    - **Weight Server**: External DRAM accessed via a global address space for large-scale model weights and data.
- **Host-Device Interface**: A driver model implementing a command queue (`CS3Queue`) and memory movement (`cs3_memcpy`).

### Execution Model
The simulator employs a **Bulk Synchronous Parallel (BSP)** model, dividing execution into discrete "supersteps":
1. **Compute**: PEs perform local SIMD operations.
2. **Communicate**: PEs exchange data across the mesh or with the Weight Server.
3. **Synchronize**: A global barrier (`SYNC`) aligns the execution state.

To balance accuracy and speed, the simulator uses a **hybrid execution track**:
- **Performance Track (Global)**: All PEs are tracked for cycle counts and timing.
- **Functional Track (Sampled)**: A stochastic sampling strategy is used where only a subset of blocks is fully simulated functionally to verify correctness.

---

## 💻 Software Stack

The project implements a complete toolchain:
**`Python DSL` $\rightarrow$ `Tungsten-IR` $\rightarrow$ `ISA Binary` $\rightarrow$ `Simulator`**

### Programming Example
Kernels are written in a CUDA-like Python DSL. For example, a simple SAXPY ($\mathbf{z} = \alpha \mathbf{x} + \mathbf{y}$) kernel:

```python
@cs3_kernel(block_w=16, block_h=16)
def saxpy_kernel(ctx):
    # Load inputs from global memory (Weight Server)
    x = ctx.load_global(None, 0)
    y = ctx.load_global(None, 4)
    
    # Compute: z = 2.0 * x + y
    z = 2.0 * x + y
    
    # Store result back to global memory
    ctx.store_global(None, 8, z)
```

1. **Frontend**: A CUDA-like DSL embedded in Python using `@cs3_kernel` decorators.
2. **Intermediate Representation (Tungsten-IR)**: A dataflow-centric IR mapping compute nodes and synchronization points.
3. **Compiler Backend**:
    - **Mapping & Scheduling**: Assigns IR nodes to the physical 2D mesh and manages the SRAM budget.
    - **Assembler**: Emits the final 32-bit binary stream.
4. **Simulator Engine**: A Python-based engine that decodes the ISA and drives the hardware model.


---

## ⏱️ Performance Modeling

Instead of exhaustive packet-level simulation, the system uses a **latency-and-bandwidth-aware abstract model**:

- **Latency**: Calculated based on physical Manhattan distance:
  $$\text{Latency}_{\text{op}} = \text{Base Latency} + (\text{Manhattan Distance} \times \text{Hop Latency})$$
- **Bandwidth & Congestion**: The simulator enforces a **Bisection Bandwidth Constraint**. If total bytes transferred per superstep exceed network capacity, a congestion multiplier is applied to "stretch" the superstep duration.

---

## 🛠️ Current Status

| Component | Status | Details |
| :--- | :--- | :--- |
| **ISA Decoder** | ✅ Complete | Full implementation of Compute, Mesh, Control, System, DSD, and Global memory opcodes. |
| **Hardware Model**| ✅ Functional | Core logic, SRAM, 2D Mesh, and Host-Device IO are implemented. |
| **Compiler** | ✅ Functional | AST parsing, IR generation, register allocation, and assembly are operational. |
| **Simulation Engine**| ✅ Functional | Hybrid Performance/Functional tracks and BSP scheduling are implemented. |
| **Advanced Mapping**| 🚧 In Progress | Optimizing spatial mapping for complex kernels. |
| **Weight Server** | 🚧 In Progress | Integration with external weight servers for real-world model weights. |

## 🧪 Testing & Validation

The project uses a **Dual-Execution** strategy to verify the compiler:
1. **Python Path**: Executes the kernel as a Python function via `KernelContext` (Golden Reference).
2. **Binary Path**: Compiles the kernel $\rightarrow$ executes the resulting binary on the `BSPScheduler`.
3. **Comparison**: Bit-exact comparison of final memory states.

To run integration tests:
```bash
python3 -m unittest discover tests/integration
```
