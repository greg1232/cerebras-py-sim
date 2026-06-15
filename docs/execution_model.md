# CS3 Execution Model Overview

This document describes the high-level execution model of the CS3 simulator. The CS3 architecture is designed as a massively parallel wafer-scale engine. To make the programming model intuitive for developers familiar with GPU computing, the execution model is designed to be analogous to CUDA, but mapped specifically to the physical constraints and capabilities of the CS3 wafer.

## Conceptual Mapping: CS3 vs. CUDA

The following table summarizes how the CS3 execution model maps to familiar CUDA concepts.

| CS3 Concept | CUDA Analogy | Description |
| :--- | :--- | :--- |
| **Wafer** | **Grid** | The entire physical array of PEs. |
| **Processing Element (PE)** | **Thread** | The smallest unit of execution. |
| **Tile** | **Block** | A grouping of PEs that act as an isolated scheduling and communication unit. |
| **Local SRAM** | **Shared Memory** | Private high-speed memory local to each PE. |
| **Weight Server** | **Global Memory** | External DRAM accessed asynchronously by all PEs via the IO fabric. |

---

## The Execution Hierarchy

### 1. Grid = Wafer
The CS3 wafer consists of an **800x900 grid of Processing Elements (PEs)**. When a kernel is launched, the host specifies a 2D grid dimension (up to 800x900).

- **Single Program, Multiple Data (SPMD):** Every PE executes the same kernel program.
- **Unique Identification:** Each PE determines which piece of data to operate on based on its unique coordinates `(pe_x, pe_y)`.
- **Independence:** Unlike CUDA warps, there is no "warp divergence" in CS3. PEs execute independently, removing the need for complex branch synchronization within the hardware.

### 2. Block = Tile
A kernel launch also specifies a **Tile size** (e.g., 16x16 PEs). 

```text
Wafer (Grid)
+---------------------------------------+
|  Tile (0,0)  |  Tile (0,1)  | ...     |
|  [ 16x16 ]   |  [ 16x16 ]   |         |
+---------------------------------------+
|  Tile (1,0)  |  Tile (1,1)  | ...     |
|  [ 16x16 ]   |  [ 16x16 ]   |         |
+---------------------------------------+
```

- **Hierarchical Scheduling:** Blocks are the primary unit of scheduling. The scheduler manages blocks independently, and their execution order is not guaranteed. To maintain simulation performance, the scheduler selects a subset of blocks for full functional simulation; all other blocks are abstractly simulated for timing.
- **Isolation Boundary:** A block serves as a strict isolation boundary. PEs in Block A cannot communicate with PEs in Block B via the mesh.
- **Communication via Global Memory:** PEs communicate with each other and with the Weight Server through `LDR_GLOBAL` and `STR_GLOBAL` instructions. Logically, this is a memory operation—a PE issues a load or store to a global address, and the hardware handles delivery. Internally, the hardware uses the NESW mesh links for routing, but this is transparent to the programmer.
- **Synchronization:** Tiles are the unit of synchronization. The `SYNC` instruction acts as a barrier, ensuring all PEs within a specific tile have reached the same point in execution before proceeding.

## Block Communication via Global Memory
Communication in the CS3 programming model is logically a memory operation. Programmers do not issue explicit mesh `SEND` or `RECV` instructions; instead, they use `LDR_GLOBAL` and `STR_GLOBAL` to read and write a global address space. The hardware implements these operations by routing through the NESW mesh, but this routing is internal to the hardware.

This abstraction has several important consequences:
- **Unified programming model:** Both local neighbor communication and remote Weight Server access use the same `load_global`/`store_global` interface.
- **No explicit routing:** Programmers do not manage mesh directions. The hardware resolves the address to a physical location and routes accordingly.
- **Block boundaries are transparent:** A load from a neighboring PE's SRAM that happens to be in a different block is handled by the hardware; the programmer does not need to check block boundaries or use different primitives.

---

## Memory Architecture

### Registers and Local Memory
Each PE is equipped with a dedicated memory hierarchy to minimize latency:

- **Vector Registers:** 32 SIMD-8 vector registers. These are extremely fast with zero latency.
- **Local SRAM:** 48KB of local SRAM. This is analogous to CUDA's shared memory but is **private** to the individual PE rather than shared across a block.

### External Storage (The Weight Server)
There is no global device memory located on the wafer itself. Large tensors and model weights reside on an external **Weight Server** (DRAM). This memory is accessed via the IO fabric, which consists of 12x 100Gbps IO links.

- **Global Access:** All PEs across the wafer can issue loads and stores to the Weight Server.
- **Asynchronous Nature:** These operations are asynchronous and high-latency compared to local SRAM or mesh communication.

---

## Execution Flow

### Bulk Synchronous Execution
The CS3 simulator follows a **Bulk Synchronous Parallel (BSP)** model, mapping directly to the Tungsten stencil model. Execution proceeds in discrete "supersteps":

1. **Compute:** All PEs perform local computations using registers and local SRAM.
2. **Communicate:** PEs exchange data via global load/store operations. The hardware transparently routes these through the mesh.
3. **Synchronize:** PEs hit a `SYNC` barrier to align execution state.

### Kernel Lifecycle
The typical lifecycle of a kernel execution is as follows:

1. **Allocation:** The Host allocates memory on the Weight Server.
2. **Data Transfer:** The Host issues a `memcpy` to transfer initial data to the device via the IO links.
3. **Launch:** The Host enqueues the kernel launch, specifying grid (800x900) and tile (e.g., 16x16) dimensions.
4. **Execution:** The scheduler manages blocks independently. A subset of blocks is sampled for full functional simulation (where every PE in the block is fully simulated), while others are abstractly simulated. All PEs begin executing the kernel program in parallel, but block-level scheduling determines when specific tiles are active.
5. **Iteration:** PEs perform compute $\rightarrow$ communicate $\rightarrow$ `SYNC` cycles.
6. **Retrieval:** Upon completion, the Host issues a `memcpy` to pull results back from the device.
