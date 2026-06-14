# CS3 Simulator Test Plan

This document outlines the comprehensive test suite for the CS3 simulator, covering unit tests for individual modules, integration tests for cross-layer functionality, end-to-end application correctness, and performance model validation.

## 1. Unit Tests

### hw/core.py (Core PE & SIMD)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| Register Initialization | New PE instance | All SIMD-8 registers = 0 | `hw/core.py` |
| SRAM Initialization | New PE instance | All SRAM addresses = 0 | `hw/core.py` |
| VMASK Configuration | Binary mask pattern | Correct lane mask bits set in PE state | `hw/core.py` |
| VADD Correctness | Two vectors [1,2..], [3,4..] | [4,6..] on all 8 lanes | `hw/core.py` |
| VADD Masking | VADD with mask [1,0,1..] | Only lanes 0, 2, ... modified; others preserved | `hw/core.py` |
| VFMADD Correctness | A, B, C vectors | Result = (A * B) + C for all active lanes | `hw/core.py` |
| VRELU Correctness | Vector with [-1.0, 2.0, -0.5, 3.0] | [0.0, 2.0, 0.0, 3.0] | `hw/core.py` |
| SRAM Round-trip | Write float32 at offset X, then read | Original float32 value | `hw/core.py` |
| SRAM Bounds Check | Read from address > SRAM_SIZE | `MemoryError` raised | `hw/core.py` |

### hw/mesh.py (Interconnect)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| MeshBuffer Order | Enqueue(A), Enqueue(B) | Dequeue() returns A, then B | `hw/mesh.py` |
| MeshBuffer Overflow | Enqueue 17 packets into size 16 buffer | `OverflowError` raised | `hw/mesh.py` |
| MeshNetwork Routing | `send_packet` to NORTH | Packet arrives in neighbor's SOUTH buffer | `hw/mesh.py` |
| Block Isolation | Packet sent across block boundary | Error/Exception raised | `hw/mesh.py` |
| Hop Count | Source (0,0), Dest (2,3) | Hop count = 5 (Manhattan distance) | `hw/mesh.py` |
| XY Route Generation | Start (0,0), End (2,2) | Correct sequence of intermediate hops | `hw/mesh.py` |

### hw/memory.py (Global Memory)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| Malloc Validity | Request N bytes | Valid `DevicePtr` returned | `hw/memory.py` |
| Bump Pointer Advance | Two consecutive mallocs | Second `DevicePtr` > First `DevicePtr` | `hw/memory.py` |
| Free Logic | `free(ptr)`, then `load(ptr)` | `MemoryError` or similar access error | `hw/memory.py` |
| Memcpy H2D Round-trip | Host array $\to$ `memcpy_h2d` $\to$ `load` | Values match original host array | `hw/memory.py` |
| Memcpy D2H Correctness | Device data $\to$ `memcpy_d2h` | Correct bytes returned to host | `hw/memory.py` |
| Transfer Tracking | Multiple `memcpy` operations | `total_bytes_transferred` = sum of all | `hw/memory.py` |

### engine/sampler.py (Stochastic Sampling)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| Full Sampling | `sampling_rate = 1.0` | All blocks marked as sampled | `engine/sampler.py` |
| Minimum Sampling | `sampling_rate = 0.0` | At least 1 block sampled | `engine/sampler.py` |
| PE-to-Block Mapping | PE (x,y) $\to$ `is_pe_sampled` | Correct boolean based on block coordinates | `engine/sampler.py` |
| Sample Count | Total grid, rate $R$ | Approx. $R \times$ Total Blocks sampled | `engine/sampler.py` |

### engine/perf_model.py (Latency & Timing)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| VFMADD Latency | `add_instruction_latency('VFMADD')` | +1 cycle added to current step | `engine/perf_model.py` |
| VEXP Latency | `add_instruction_latency('VEXP')` | +5 cycles added to current step | `engine/perf_model.py` |
| Max Latency Logic | VFMADD (1) and VEXP (5) in one step | `current_step_cycles` = 5 | `engine/perf_model.py` |
| Superstep Finalization | Call `finalize_superstep` | `total_cycles` increased, `current_step` = 0 | `engine/perf_model.py` |
| Runtime Estimation | 750MHz vs 1200MHz | Estimated runtime scales inversely with freq | `engine/perf_model.py` |

### driver/queue.py (Command FIFO)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| FIFO Preservation | Enqueue(CMD1), Enqueue(CMD2) | Drain() processes CMD1 then CMD2 | `driver/queue.py` |
| Queue Clearing | Enqueue(X), then `drain()` | Queue size = 0 | `driver/queue.py` |
| Command Storage | `Command(type=MALLOC, args=...)` | Correct type and args stored in dataclass | `driver/queue.py` |

### driver/api.py (Host Interface)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| api_malloc | `cs3_malloc(size)` | `DevicePtr` returned, MALLOC command in queue | `driver/api.py` |
| api_memcpy_h2d | `cs3_memcpy_h2d(dst, src, size)` | MEMCPY_H2D command in queue with correct size | `driver/api.py` |
| api_launch | `cs3_launch(kernel, grid, block)` | KERNEL_LAUNCH command in queue | `driver/api.py` |
| api_sync | `cs3_sync()` | SYNC_BARRIER command in queue | `driver/api.py` |

### compiler/kernel.py (Kernel Decoration)
| Test Name | Input | Expected Output | Layer Validated |
| :--- | :--- | :--- | :--- |
| Basic Decorator | `@cs3_kernel` on function $f$ | $f$ is wrapped in a `Kernel` dataclass | `compiler/kernel.py` |
| Parameterized Decorator | `@cs3_kernel(block_w=32, block_h=32)` | Kernel object contains specified dimensions | `compiler/kernel.py` |
| KernelArgs Access | `args['param_name']` | Correct value for the given parameter | `compiler/kernel.py` |

## 2. Integration Tests

| Test Name | Scenario | Expected Outcome | Layers Validated |
| :--- | :--- | :--- | :--- |
| Host-Device Data Flow | `malloc` $\to$ `memcpy_h2d` $\to$ `load` | Loaded value == Original host value | `driver/api`, `hw/memory`, `hw/core` |
| Block Isolation E2E | Two blocks; attempt cross-block send | Inter-block send raises error | `hw/mesh`, `engine/scheduler` |
| BSP Step Counting | Run 10 supersteps with known latencies | `total_cycles` == $\sum_{i=1}^{10} \max(\text{latency}_i)$ | `engine/scheduler`, `engine/perf_model` |

## 3. End-to-End Application Tests (Correctness)

All E2E tests are run with `sampling_rate=1.0` to ensure full functional correctness.

| App | Configuration | Success Criteria |
| :--- | :--- | :--- |
| **SAXPY** | Small grid (e.g., 2x2 blocks of 2x2 PEs) | For all $i$: $z[i] = a \cdot x[i] + y[i]$ |
| **GEMM** | Minimal grid, 4x4 output matrix | Result matches `numpy.dot(A, B)` |
| **Heat Eq** | 4x4 grid, 10 time steps | Result matches Python 5-point Laplacian reference |

## 4. Performance Modeling Tests

| Test Name | Input | Expected Outcome |
| :--- | :--- | :--- |
| Bandwidth Estimate | `memcpy_h2d` of 1MB | `total_bytes_transferred` == 1MB; Estimated time == $1\text{MB} / \text{IO\_BANDWIDTH\_BPS}$ |
| Sampling Efficiency | SAXPY: Rate=0.01 vs Rate=1.0 | Simulation wall-clock time at 1% $\le$ 2% of time at 100% (at least 50x speedup) |

## 5. Regression Tests

- **CI Trigger**: All tests in sections 1, 2, and 3 must execute on every commit.
- **Failure Policy**: Any regression in unit or E2E correctness blocks merging.
