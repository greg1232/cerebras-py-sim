# Bulk Synchronous Parallel (BSP) Execution Model

The CS3 simulator implements a Bulk Synchronous Parallel (BSP) execution model, inspired by Valiant's BSP model and the Tungsten dataflow domain translation paper. This model provides a structured approach to parallel execution across the wafer-scale mesh of Processing Elements (PEs).

## What is a Superstep?

The fundamental unit of execution in the CS3 is the **superstep**. A superstep is a single iteration consisting of three distinct phases:

1.  **Local Computation:** Each PE executes a set of instructions using its local resources (SRAM and SIMD units).
2.  **Mesh Communication:** PEs exchange data with their immediate neighbors via the 2D mesh.
3.  **Global Barrier (SYNC):** A synchronization point that ensures all PEs have completed their computation and communication phases before any PE proceeds to the next superstep.

All PEs execute the computation and communication phases concurrently and independently. The `SYNC` phase prevents race conditions and ensures global consistency of the machine state.

## Why BSP on a Wafer?

The BSP model is particularly suited for the CS3 wafer-scale architecture for several reasons:

*   **Predictable Latency:** The 2D mesh provides bounded latency. With a cost of 1 cycle per hop, the worst-case latency is predictable based on the mesh dimensions (up to $\max(800, 900)$ hops).
*   **Deadlock Freedom:** By enforcing a strict superstep structure where all PEs follow the same send/receive patterns, the system avoids circular dependencies that lead to deadlocks.
*   **Workload Mapping:** The model maps directly to stencil computations and finite-difference methods, which are the primary workloads for the Tungsten model and similar scientific simulations.

## Superstep Structure and Timing

### Timeline Diagram
```text
Superstep n:
|--- Compute Phase ---|--- Communicate Phase ---|-- SYNC --|
| (Local SIMD/SRAM)   | (Mesh SEND/RECV)         | (Barrier) |
^                    ^                         ^           ^
t_start              t_comm_start              t_sync       t_next
```

### Phase Details
- **Compute Phase:** Each PE executes local SIMD instructions. Duration is proportional to the kernel complexity and the amount of data processed from local SRAM.
- **Communicate Phase:** PEs issue `SEND_*` and `RECV_*` commands. The mesh supports 16 bits per cycle per direction. Packets may remain in-flight across the mesh during this phase.
- **Barrier:** The `SYNC` instruction. PEs that complete their work early must stall at the barrier until the slowest PE reaches the `SYNC` point.

## Mapping to the ISA

The BSP phases are realized through specific instructions in the CS3 ISA:

| Phase | ISA Instructions |
| :--- | :--- |
| **Compute** | `VADD`, `VMUL`, `VFMADD`, activations, SRAM loads/stores |
| **Communicate** | `SEND_N/S/E/W`, `RECV_N/S/E/W`, `WAIT_*` |
| **Barrier** | `SYNC` |

## Multi-Superstep Programs

Complex programs are structured as a series of supersteps. From the host's perspective, this is typically a single kernel launch, with the loop logic executing entirely on-device.

### Pseudocode Pattern
```python
# Device-side execution loop
for t in range(T):
    # Phase 1: Local Computation
    compute_local_stencil(data_sram)
    
    # Phase 2: Mesh Communication (Halo Exchange)
    send_to_neighbors(boundary_data)
    recv_from_neighbors(boundary_data)
    
    # Phase 3: Global Barrier
    sync() 
```

## Deadlock Avoidance Rules

To ensure the stability of the mesh and prevent hangs, the following rules must be observed:

1.  **Symmetry:** If a PE issues a `SEND_N` (North), the North neighbor must issue a `RECV_S` (South) within the same superstep.
2.  **Corresponding Pairs:** Never issue a `RECV` without a corresponding `SEND` from the neighbor in the same superstep.
3.  **Universal Sync:** The `SYNC` instruction must be reached by all PEs in the execution group before any PE is allowed to begin the next superstep.

## Performance Model

The total time for a single superstep is governed by the slowest component:

$$\text{Time per superstep} = \max(T_{\text{compute}}, T_{\text{communicate}}) + T_{\text{barrier}}$$

Where:
- $T_{\text{compute}}$ is the time taken by the slowest PE to finish local work.
- $T_{\text{communicate}}$ is the time for the largest message to traverse the required hops.
- $T_{\text{barrier}}$ is the overhead of the global synchronization signal.

### Communication Latency
The communication time is calculated as:
$$T_{\text{communicate}} = \left( \frac{\text{message\_size\_bits}}{16} \right) \text{ cycles per hop}$$

### Worked Example: 1D Halo Exchange
**Scenario:** A row of $N$ PEs passing a 32-bit float (single precision) to their eastern neighbor.

- **Message Size:** 32 bits.
- **Bandwidth:** 16 bits/cycle.
- **Hops:** 1 (immediate neighbor).

**Calculation:**
$$\text{Cycles} = \left( \frac{32}{16} \right) \times 1 = 2 \text{ cycles}$$

In this example, the communication phase takes 2 cycles, assuming the compute phase is shorter or runs in parallel with the transmission.
