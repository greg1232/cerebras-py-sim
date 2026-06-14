# Software Architecture: Cerebras-Sim

This document provides the technical blueprint for the Python implementation of the Cerebras-Sim. The simulator is designed as a hybrid system that balances functional verification (correctness) with performance estimation (runtime) for a wafer-scale engine.

## Architecture Overview

The simulator is structured into four distinct layers: the **Hardware Model** (Physical), the **Execution Engine** (Virtual), the **Host Interface** (Driver), and the **Frontend** (User).

### Component Interaction Diagram

```text
+-------------------+       +-------------------+
|   User Application| ---->  |  SimulationRunner |
+-------------------+       +-------------------+
                                    |
                                    v
+-------------------+       +-------------------+
| KernelCompiler    | ----> |   CommandQueue    |
| (DSL -> ISA)      |       | (Host Commands)   |
+-------------------+       +-------------------+
                                    |
                                    v
+-------------------+       +-------------------+
|  WeightServer     | <---- |      Driver       |
| (DRAM Simulation) |       | (cs3_* API Logic) |
+-------------------+       +-------------------+
                                    |
                                    v
+-------------------+       +-------------------+
|  PerformanceCount | <---- |    Scheduler      |
|  (Global Cycles)  |       | (BSP Loop / Sync) |
+-------------------+       +-------------------+
                                    |
                                    v
+-------------------+       +-------------------+
|    MeshNetwork    | <---  |     Sampler      |
| (FIFO Fabric)     |       | (Active vs Abstract)|
+-------------------+       +-------------------+
                                    |
                                    v
+-------------------+       +-------------------+
|   MeshBuffer      | <---  |   Core (PE)       |
| (SRAM/Registers)  |       | (Step/Execute)    |
+-------------------+       +-------------------+
```

---

## 1. The Hardware Model (The 'Physical' Layer)

This layer simulates the on-chip components of the CS3 architecture.

### Core (PE)
Represents a single Processing Element.
- **State**: 
  - **Registers**: A SIMD-8 vector register file (implemented as a NumPy array for performance).
  - **SRAM**: 48KB of local memory (NumPy array).
  - **PC**: Program Counter tracking the current instruction.
  - **Mask**: A bitmask for conditional execution in SIMD operations.
- **Logic**:
  - `step()`: The primary execution method. It fetches the current instruction from the ISA sequence, decodes the operands, and executes the operation (arithmetic, memory access, or mesh communication).

### MeshNetwork
The communication fabric connecting the 800x900 grid.
- **Logic**: Manages a 2D array of `MeshBuffer` objects. It handles the routing of data packets between adjacent PEs.
- **API**:
  - `send_packet(x, y, direction, packet)`: Enqueues a packet into the neighbor's buffer in the specified direction (N, S, E, W).
  - `pop_packet(x, y, direction)`: Retrieves a packet from the local buffer associated with a specific direction.

### WeightServer
Simulates the external DRAM and the high-bandwidth memory interface.
- **State**: A large contiguous byte-buffer (NumPy array) representing the device's global memory.
- **Logic**: Handles DMA requests originating from the mesh. It manages `load_global` and `store_global` operations, simulating the high latency associated with off-chip access.

---

## 2. The Execution Engine (The 'Virtual' Layer)

This layer manages the simulation's logic, balancing speed and accuracy.

### Sampler
Implements the logic from `sampling_strategy.md`.
- **Responsibility**: To avoid the overhead of simulating 720k cores, the Sampler determines which PEs are **'Active'** (fully simulated for functional correctness) and which are **'Abstract'** (only tracked for timing and performance).
- **Logic**: Uses a configurable sampling rate ($\rho$) and tile-based selection to maintain local communication patterns.

### Scheduler (The BSP Loop)
The central orchestrator of the simulator.
- **Logic**: Implements the Bulk Synchronous Parallel (BSP) model.
- **Workflow**:
  1. **Dispatch**: Trigger `step()` on all Active PEs.
  2. **Communicate**: Process `MeshNetwork` traffic and update `MeshBuffer` states.
  3. **Synchronize**: Handle `SYNC` barriers, ensuring all PEs in a tile have reached the synchronization point before proceeding to the next superstep.

### PerformanceCounter
The global clock and latency tracker.
- **Logic**: Aggregates latency from individual instructions (e.g., VFMADD vs. VEXP) and mesh hops. It calculates the total elapsed cycles to provide an estimated runtime for the executed kernel.

---

## 3. The Host Interface (The 'Driver' Layer)

This layer bridges the gap between the user's host-side code and the device simulation.

### CommandQueue
A FIFO buffer that holds host commands (e.g., kernel launches, memory copies) to be processed sequentially by the driver.

### Driver
Implements the `cs3_*` API.
- **Logic**:
  - `cs3_launch`: Translates a kernel call into a task for the Scheduler, including the mapping of arguments to the PEs.
  - `cs3_memcpy`: Translates host-to-device transfers into operations on the `WeightServer`.

---

## 4. The Frontend (The 'User' Layer)

The interface for the end-user to define and run simulations.

### KernelCompiler (Stub)
A translation layer for the CS3 DSL.
- **Responsibility**: Parses the C-like DSL (defined in `kernel_programming_model.md`) and lowers it into a sequence of ISA instructions that the `Core` can execute.

### SimulationRunner
The main entry point for the simulator.
- **Responsibility**: 
  - Loads the compiled kernel.
  - Initializes the `MeshNetwork` and `WeightServer`.
  - Configures the `Sampler` (sampling rate and grid size).
  - Drives the `Scheduler` until the kernel completes execution.

---

## Performance Optimizations

To maintain acceptable simulation speeds in Python, the following strategies are employed:

1. **NumPy for Memory**: SRAM and Register files are implemented as **NumPy arrays** rather than Python lists. This allows for efficient vectorization of SIMD-8 operations and significantly reduces the memory overhead of storing millions of values across the grid.
2. **State Compression**: For 'Abstract' cores (non-sampled), the simulator only tracks the Program Counter and critical status flags, skipping all data-plane computations.
3. **Vectorized Latency**: Where possible, the `PerformanceCounter` applies latency costs to blocks of PEs rather than individual cores to reduce loop overhead.
