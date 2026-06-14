# Simulator Architecture: Cerebras-Sim

This document defines the underlying architecture and operational logic of the Cerebras-Sim simulator. The simulator is designed as a hybrid system that provides both **Functional Simulation** (ensuring the correctness of computations) and **Performance Simulation** (estimating the total execution time of programs on the hardware).

## 1. Core Simulation Philosophy

Simulating a wafer-scale engine with 720,000 cores in a high-level language like Python is computationally prohibitive for meaningful workloads. To overcome this, Cerebras-Sim employs a dual-track execution model:

1.  **Performance Track (Global/Counting):** Every Processing Element (PE) is tracked to estimate runtime and resource utilization.
2.  **Functional Track (Sampled/Computational):** Only a small subset of PEs performs actual data computation to verify correctness.

---

## 2. Performance Modeling (The "Counting" Mode)

The performance simulator acts as a cycle-accurate (or near cycle-accurate) estimator. It does not execute the full logic of every instruction but instead "counts" the cost of the operations performed.

### 2.1 Latency Modeling
Every operation contributes to a global cycle counter based on defined hardware latencies:
- **Instruction Latencies:** Different instructions have different weights (e.g., `VFMADD` = 1 cycle, `VEXP` = 5 cycles).
- **Mesh Latency:** Communication between PEs is modeled as 1 cycle per hop.
- **Memory Access:** SRAM read/write operations carry specific costs.
- **Host-Device IO:** Data transfers via `cs3_memcpy` are modeled based on a 100Gbps bandwidth limit.

### 2.2 Runtime Estimation
The total estimated runtime for a program is calculated as:
$$\text{Total Runtime} = \sum (\text{cycles per superstep}) \times \text{cycle period}$$

---

## 3. Functional Simulation via Sampling

To maintain functional correctness without the overhead of 720k cores, the simulator implements **Stochastic Functional Sampling**.

### 3.1 Sampling Strategy
The simulator logically tracks the state of all PEs but only performs "full" functional execution (updating registers, calculating arithmetic results, and modifying SRAM) for a randomly selected subset of $K$ cores or "thread groups" (tiles).

### 3.2 Verification and State Tracking
- **Correctness Verification:** The sampled cores are used to verify that the kernel produces the expected output. Because kernels are generally symmetric across the grid, the correctness of the sampled subset serves as a proxy for the correctness of the entire mesh.
- **Compressed State:** For non-sampled cores, the simulator maintains a "compressed" state (e.g., only tracking the Program Counter (PC) and critical flags). This ensures that performance counting remains accurate even when the actual computation is skipped.

---

## 4. Comparison: Performance vs. Functional Tracking

| Feature | Performance Track (All Cores) | Functional Track (Sampled Cores) |
| :--- | :--- | :--- |
| **Instruction Execution** | Latency counting only | Full SIMD computation |
| **Register State** | PC and critical flags only | Full register file updates |
| **SRAM Interaction** | Access cost counting | Actual data read/write |
| **Mesh Communication** | Hop count $\rightarrow$ cycle cost | Data packet movement |
| **Purpose** | Runtime/Bottleneck Estimation | Correctness/Output Verification |

---

## 5. Full-Stack Simulation Scope

The simulator covers the entire execution pipeline, from the host driver to the on-chip kernel.

### 5.1 Driver Simulation
The simulator models the `CS3Queue` and host-side operations. API calls such as `cs3_malloc` and `cs3_memcpy` are not instantaneous; they add to the total estimated runtime based on the size of the request and hardware bandwidth limits.

### 5.2 Kernel Simulation
Kernel execution is modeled as a series of BSP (Barrier Synchronization Parallel) supersteps.

### 5.3 The "Hybrid Loop"
The simulator operates in a continuous loop:
1.  **Host Trigger:** A host command is issued $\rightarrow$ time is added to the global counter $\rightarrow$ the kernel is triggered.
2.  **Superstep Execution:** For each BSP superstep:
    - **Performance Count:** Iterate through all PEs to accumulate cycles.
    - **Functional Compute:** Perform actual SIMD computation for the sampled subset of PEs.
    - **Traffic Modeling:** Model mesh traffic for all PEs to identify communication bottlenecks.
