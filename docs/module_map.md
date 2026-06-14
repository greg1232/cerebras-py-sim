# Module Map: Cerebras-Sim

This document serves as the architectural blueprint for the Python implementation of the Cerebras-Sim simulator. It maps the theoretical design (Functional vs. Performance tracks, BSP model, and Host-Device Interface) to a concrete file and class structure.

## Project Structure

```text
cerebras_sim/
├── __init__.py
├── main.py                 # Simulation entry point
├── hw/                     # Hardware Emulation
│   ├── __init__.py
│   ├── core.py             # PE state and instruction execution
│   ├── mesh.py             # Mesh network and buffer logic
│   └── memory.py           # Weight Server and DevicePtr management
├── engine/                 # Simulation Logic
│   ├── __init__.py
│   ├── scheduler.py        # BSP loop and superstep orchestration
│   ├── sampler.py          # Stochastic Functional Sampling manager
│   └── perf_model.py       # Performance counting and latency tables
├── driver/                 # Host Interface
│   ├── __init__.py
│   ├── queue.py            # Command queue (CS3Queue) and command types
│   └── api.py              # Implementation of cs3_* C-style API
├── compiler/               # DSL to ISA
│   ├── __init__.py
│   ├── parser.py           # DSL parsing logic
│   └── codegen.py          # Generation of ISA instruction streams
└── utils/                  # Shared Utilities
    ├── __init__.py
    ├── constants.py        # Hardware constants, opcodes, and dimensions
    └── logging.py          # Telemetry, trace logging, and event reporting
```

---

## Module Details

### `cerebras_sim/` (Root)
- **`main.py`**: The top-level coordinator.
  - `SimulationRunner`: Loads the kernel, initializes the `MeshNetwork`, and drives the `Scheduler` through the sequence of host commands and kernel supersteps.

### `cerebras_sim/hw/` (Hardware Emulation)
- **`core.py`**: Models the Processing Element (PE).
  - `Core`: 
    - `execute(instruction)`: Updates register state/SRAM based on the instruction.
    - `step()`: Advances the PE state.
    - `get_state()`: Returns current PC and critical flags.
- **`mesh.py`**: Models the 2D wafer-scale interconnect.
  - `MeshNetwork`: Manages the grid of PEs and routes packets.
    - `route_packet(packet)`: Moves data between PEs (1 cycle/hop).
  - `MeshBuffer`: Handles the 16-bit/cycle buffers for `SEND`/`RECV` operations.
- **`memory.py`**: Models the external Weight Server.
  - `WeightServer`: Manages the 1.5TB address space.
    - `allocate(size)`: Returns a `DevicePtr`.
    - `read(ptr, size)` / `write(ptr, data)`: Simulates DMA access.
  - `DevicePtr`: An opaque handle for memory addresses.

### `cerebras_sim/engine/` (Simulation Logic)
- **`scheduler.py`**: Orchestrates the BSP (Bulk Synchronous Parallel) model.
  - `BSPScheduler`:
    - `run_superstep()`: Coordinates the Compute $\rightarrow$ Communicate $\rightarrow$ Sync sequence.
    - `synchronize()`: Implements the global barrier.
- **`sampler.py`**: Implements the hybrid execution model.
  - `SamplingManager`: 
    - `select_sample_set()`: Randomly selects $K$ cores for functional execution.
    - `should_compute_functional(core_id)`: Determines if a PE performs full SIMD computation or just latency counting.
- **`perf_model.py`**: The "Counting" track for runtime estimation.
  - `PerformanceCounter`:
    - `add_cycles(instruction_type)`: Adds latency from the lookup table.
    - `get_total_runtime()`: Returns the accumulated simulation time.
  - `LatencyTable`: Static mapping of ISA instructions to cycle costs.

### `cerebras_sim/driver/` (Host Interface)
- **`queue.py`**: Models the asynchronous command stream.
  - `CS3Queue`:
    - `enqueue(command)`: Adds a command (MALLOC, MEMCPY, LAUNCH) to the FIFO.
    - `process_next()`: Executes the next command in the queue.
  - `Command`: Base class for `MemcpyCmd`, `LaunchCmd`, etc.
- **`api.py`**: Python wrappers for the HDI.
  - `cs3_malloc()`, `cs3_memcpy_h2d()`, `cs3_launch()`, `cs3_queue_sync()`: Direct mappings to the C API specification.

### `cerebras_sim/compiler/` (DSL to ISA)
- **`parser.py`**: Converts high-level DSL into an intermediate representation.
  - `DSLParser`: Parses kernel source into a graph of operations.
- **`codegen.py`**: Translates IR into the CS3 ISA.
  - `ISAGenerator`: Produces the final binary stream of instructions for the PEs.

### `cerebras_sim/utils/`
- **`constants.py`**:
  - `MESH_WIDTH`, `MESH_HEIGHT`: (800, 900).
  - `OPCODES`: Dictionary mapping instruction names (e.g., `VFMADD`) to hex codes.
  - `CLOCK_SPEED`: Simulation frequency settings.
- **`logging.py`**:
  - `SimLogger`: Provides structured logging for superstep transitions and PE state changes.
  - `TraceWriter`: Exports simulation events to a file for external analysis.
