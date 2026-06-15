# Design: High-Level Mesh Communication Model

## Overview
Instead of a cycle-accurate simulation of every `MeshPacket` moving through every buffer at every tick, we will implement a **latency-and-bandwidth-aware abstract model** for global memory operations (`LDR_GLOBAL`, `STR_GLOBAL`). 

This approach captures the primary performance bottlenecks of a Wafer-Scale Engine—network diameter and bisection bandwidth—without the massive overhead of simulating millions of individual packet movements.

## Communication Model

### 1. Latency Modeling (Hops)
Every global load or store is treated as a request-response pair. The total latency for a single operation is calculated as:

$$\text{Latency}_{\text{op}} = \text{Base Latency} + (\text{Manhattan Distance} \times \text{Hop Latency})$$

- **Base Latency**: The fixed cost of initiating a request and processing it at the source/destination.
- **Manhattan Distance**: The number of hops between the requesting PE $(x_1, y_1)$ and the target (Weight Server IO or remote PE $(x_2, y_2)$).
- **Hop Latency**: The time cost of a single mesh hop (typically 1 cycle).

For **Weight Server (WS)** access, we model the IO links as being distributed across the wafer edges. The distance is calculated from the PE to the nearest IO link.

### 2. Bandwidth Modeling (Congestion)
To model the impact of thousands of PEs competing for the same mesh links, we implement a **Bisection Bandwidth Constraint**.

- **The Bottleneck**: The mesh is divided into quadrants. The "bisection" is the cut that separates the wafer into two halves. The total bandwidth across this cut is the limiting factor for global traffic.
- **Capping Throughput**: We track the total bytes transferred per superstep. If the total volume of `LDR_GLOBAL`/`STR_GLOBAL` requests exceeds the bisection bandwidth of the mesh, we apply a **Congestion Penalty**.
- **Penalty Calculation**:
  $$\text{Actual Latency} = \text{Calculated Latency} \times \max\left(1.0, \frac{\text{Requested Bandwidth}}{\text{Bisection Bandwidth}}\right)$$

This effectively "stretches" the superstep duration when the network is saturated, accurately modeling the queueing delays seen in real WSE workloads.

## Implementation Strategy

### 1. `MeshNetwork` Enhancements
- Update `hop_count` to provide the distance from a PE to the nearest Weight Server IO port.
- Add a `track_bandwidth(bytes_transferred)` method to accumulate total traffic per superstep.

### 2. `BSPScheduler` Integration
- In `run_superstep()`, before finalizing the clock:
    1. Calculate the total bytes requested by all PEs in the compute phase.
    2. Determine the congestion multiplier based on the bisection bandwidth limit.
    3. Scale the `current_step_cycles` of the `PerformanceCounter` by this multiplier.

### 3. `PerformanceCounter` Updates
- Add a `congestion_factor` to the `finalize_superstep` logic to ensure that network saturation correctly increases the total estimated runtime.

## Metrics and Verification
- **Baseline**: A single PE performing a global load should see latency $\approx$ distance to IO.
- **Saturation**: A kernel that performs massive global loads across all PEs should show a non-linear increase in runtime as the congestion penalty kicks in.
- **Verification**: Compare the "Abstract Mesh" runtime against the "Golden Reference" Python-mode execution to ensure functional correctness is preserved while performance is modeled.
