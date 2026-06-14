# Compiler Stack Architecture

This document defines the multi-stage compiler pipeline designed to translate a high-level Python-based DSL into the ISA binary executed by the CS3 simulator.

## 1. The Frontend: Python DSL

The entry point for developers is a CUDA-like Domain Specific Language (DSL) embedded in Python. This allows users to write kernels using familiar Python syntax while restricting the execution model to a hardware-compatible subset.

### DSL Exposure
- **Decorators**: Kernels are defined using the `@cs3_kernel` decorator, which signals the compiler to treat the function as a device-side program rather than standard Python code.
- **Specialized Types**: To support SIMD operations, the DSL introduces types such as `vec8`, representing a vector of 8 elements processed in parallel.
- **Tensor References**: Arguments passed to kernels (e.g., `x`, `y`) are treated as tensor references pointing to device memory rather than Python objects.

**Example:**
```python
@cs3_kernel
def kernel_saxpy(a, x, y):
    # x and y are vec8 types
    res = a * x + y
    return res
```

### Static Analysis
The frontend performs a mandatory static analysis pass to ensure the program is executable on the CS3 hardware:
- **Memory Constraints**: Forbids dynamic heap allocation.
- **Control Flow**: Restricts unbounded loops and recursion.
- **Type Checking**: Validates that operations are performed on compatible `vec8` or scalar types.

## 2. Intermediate Representation (IR): Tungsten-IR

The compiler lowers the Python AST into **Tungsten-IR**, a dataflow-centric representation of the kernel. Tungsten-IR focuses on how data moves across the wafer and when compute is triggered.

### IR Components
- **Dataflow Dependencies**: Explicitly maps which compute node requires data from which neighbor or local register.
- **Compute Nodes**: Represents SIMD operations (e.g., `VADD`, `VMUL`) and their associated precision.
- **Memory Nodes**: Handles interactions with the local 48KB SRAM and requests to the Weight Server for model parameters.
- **Synchronization Points**: Inserts Barriers to ensure all parallel units have reached a consistent state before proceeding.

## 3. The Backend: Code Generation

The backend transforms the Tungsten-IR into a hardware-specific binary stream.

### Mapping Stage
The Mapper assigns IR nodes to the physical spatial layout of the wafer. It optimizes for locality, placing dependent operations on adjacent cores to minimize communication latency.

### Scheduling Stage
The Scheduler determines the exact sequence of operations. Its primary goals are:
- **Stall Minimization**: Ordering instructions to hide memory latency.
- **SRAM Management**: Managing the strict 48KB SRAM budget per core, inserting spills or re-loads as necessary.

### Emission Stage
The final stage converts the scheduled operations into the binary format defined in `docs/isa/encoding.md`. It produces a stream of opcodes and operands ready for the CS3 simulator.

## 4. The "Host" Compiler

While the backend generates the binary, the Host Compiler manages the interaction between the Python environment and the hardware simulator.

- **`CS3Queue` Management**: Orchestrates the sequence of commands sent to the device.
- **`cs3_launch` Orchestration**:
    1. Uploads the generated ISA binary to the designated device memory region.
    2. Configures kernel arguments (tensor pointers).
    3. Triggers the start signal to begin execution.

## 5. Compiler Pipeline Diagram

```text
+------------+      +-------------------+      +-------------+
| Python DSL | ---> | AST / Static Anal. | ---> | Tungsten-IR |
+------------+      +-------------------+      +-------------+
                                                       |
                                                       v
+------------+      +-------------------+      +-------------+
| ISA Binary | <--- | Emission Stage     | <--- | Mapping &    |
+------------+      +-------------------+      | Scheduling  |
                                               +-------------+
```

## Design Trade-offs: Compiler vs. Transpiler

During the design of this stack, two primary approaches were considered:

### The "Transpiler" Approach
A simpler approach that maps high-level Python constructs directly to ISA blocks (e.g., a Python `+` becomes a `VADD` opcode).
- **Pros**: Faster implementation, easier to debug.
- **Cons**: Poor performance; cannot optimize for the spatial layout of the wafer or manage the SRAM budget efficiently.

### The Full Compiler Approach (Tungsten-IR)
The chosen approach involving a dedicated IR and a multi-stage backend.
- **Pros**: Enables sophisticated spatial mapping, instruction scheduling, and memory optimization, which are critical for the CS3 architecture.
- **Cons**: Higher complexity in the toolchain.

**Conclusion**: Given the unique constraints of the CS3 wafer (spatial dependencies and limited SRAM), the full compiler approach is necessary to achieve acceptable hardware utilization.
