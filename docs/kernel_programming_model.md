# CS3 Simulator: Kernel Programming Model

The CS3 simulator utilizes a C-like Domain Specific Language (DSL) for writing kernels. This language is designed for massive parallelism across a grid of Processing Elements (PEs), sharing similarities with CUDA C but tailored for a mesh-based architecture.

## Kernel Declaration

Kernels are the primary unit of execution. They are declared using the `__kernel` keyword:

```c
__kernel void kernel_name(KernelArgs args) {
    // Kernel implementation
}
```

- **Single Program Multiple Data (SPMD):** Every PE in the grid executes the same kernel function.
- **No Host Code:** Kernel files contain only the kernel implementation; host-side orchestration (launching kernels, memory allocation) is handled separately.

## PE Identity

To perform data-dependent operations, each PE can determine its position in the grid and within its local tile:

- `pe_x()` and `pe_y()`: Return the global coordinates of the PE in the grid (Range: $0..799$, $0..899$). These are primarily used for global ID and calculating memory offsets.
- `tile_x()` and `tile_y()`: Return the PE's relative coordinates within its specific block. These are the primary coordinates used for mesh communication and synchronization.

These functions are analogous to `blockIdx` and `threadIdx` in CUDA, allowing PEs to partition the global workload.

## Local Memory

Each PE possesses a private 48KB SRAM for fast data access.

- **Local Buffers:** Declared using `__local`.
  ```c
  __local float buf[N];
  ```
  This is analogous to CUDA's `__shared__` memory, though it is private to the PE rather than shared across a block.
- **Registers:** Stack variables and registers reside in the 32x SIMD-8 vector register file.
- **Static Allocation:** No heap allocation is permitted within kernels. All memory must be statically laid out in SRAM at compile time.

## Global Memory Communication

Communication between PEs and the host is performed via global load and store operations. This abstracts the underlying mesh network into a global address space.

### Loading and Storing Data
- `load_global(DevicePtr ptr, int offset)`: Loads a value from the global address space (which may be in the Weight Server or another PE's SRAM) into a local register.
- `store_global(DevicePtr ptr, int offset, float val)`: Stores a value from a local register to the global address space.

All inter-PE communication—whether between neighbors in the same block or across block boundaries—is now handled via these primitives. The hardware internally routes these operations via the mesh.

### Synchronization
- `sync()`: A barrier across all PEs in the current block. No PE can proceed past the `sync()` call until every PE in the block has reached it.

## Weight Server and Global Memory Access

The global address space is the primary mechanism for data exchange. This includes the external Weight Server (DRAM) and the SRAM of other PEs.

- `load_global(DevicePtr ptr, int offset)`: Loads a value from the weight server or remote PE into a local register. 
- `store_global(DevicePtr ptr, int offset, float val)`: Stores a value to the weight server or remote PE.

**Performance Note:** Accessing the global memory space is high-latency ($\sim 100+$ cycles) as it may involve multiple mesh hops or external IO. Prefetching data into `__local` memory is strongly recommended to hide this latency.

## Vector Operations

The CS3 architecture is SIMD-8. The DSL exposes this via the `vec8` type.

- **Vector Loading:** `vec8 a = vec8_load(__local float *p);` loads 8 contiguous floats from SRAM into a register.
- **Arithmetic:** Standard operators (`+`, `-`, `*`, `/`) are overloaded to perform element-wise operations on `vec8` types.
- **Activations:** Built-in element-wise activation functions are provided:
  - `relu(vec8)`
  - `gelu(vec8)`
  - `sigmoid(vec8)`

---

## Example: 2D Stencil (5-Point Laplacian)

This example demonstrates a Laplacian filter where each PE processes a local tile. Halo exchange is performed using `load_global` and `store_global` to share boundary values with neighbors, regardless of whether they are in the same block.

```c
__kernel void laplacian_stencil(DevicePtr input, DevicePtr output) {
    // Local storage for the tile and halo regions
    // Assume tile size 8x8 for SIMD-8 alignment
    __local float tile[10][10]; 
    
    int px = pe_x();
    int py = pe_y();

    // 1. Load data from Global Memory to Local SRAM
    for (int i = 1; i < 9; i++) {
        for (int j = 1; j < 9; j++) {
            tile[i][j] = load_global(input, (py * 800 + px) * 64 + (i-1)*8 + (j-1));
        }
    }

    // 2. Halo Exchange
    // All boundary exchanges now use global load/store, abstracting the mesh.
    
    // North boundary
    float north_val = tile[1][4]; 
    store_global(output, (py-1)*800*64 + px*64, north_val); 
    tile[0][4] = load_global(input, (py-1)*800*64 + px*64);

    // South boundary
    float south_val = tile[8][4];
    store_global(output, (py+1)*800*64 + px*64, south_val);
    tile[9][4] = load_global(input, (py+1)*800*64 + px*64);

    // East boundary
    float east_val = tile[4][8];
    store_global(output, py*800*64 + (px+1)*64, east_val);
    tile[4][9] = load_global(input, py*800*64 + (px+1)*64);

    // West boundary
    float west_val = tile[4][1];
    store_global(output, py*800*64 + (px-1)*64, west_val);
    tile[4][0] = load_global(input, py*800*64 + (px-1)*64);

    // Ensure all halo exchanges are complete
    sync();

    // 3. Compute Stencil using Vectorized Operations
    for (int i = 1; i < 9; i++) {
        vec8 center = vec8_load(&tile[i][1]);
        vec8 north  = vec8_load(&tile[i-1][1]);
        vec8 south  = vec8_load(&tile[i+1][1]);
        vec8 west   = vec8_load(&tile[i][0]); 
        vec8 east   = vec8_load(&tile[i][2]);

        vec8 result = (center * 4.0f) - (north + south + east + west);
        result = relu(result);

        // 4. Write back to Global Memory
        for(int v=0; v<8; v++) {
            store_global(output, (py * 800 + px) * 64 + (i-1)*8 + v, result[v]);
        }
    }
}
```

---

## Concept Comparison: CS3 DSL vs. CUDA C

| CS3 DSL Concept | CUDA C Equivalent | Notes |
| :--- | :--- | :--- |
| `__kernel` | `__global__` | Entry point for device execution. |
| `pe_x()`, `pe_y()` | `blockIdx.x`, `blockIdx.y` | Global grid identity. |
| `tile_x()`, `tile_y()` | `threadIdx.x`, `threadIdx.y` | Local group identity. |
| `__local` | `__shared__` | Fast SRAM. CS3 is private per PE; CUDA is shared per block. |
| `load_global()` / `store_global()` | `__syncthreads()` / Shared Mem | CS3 uses a global memory-mapped model; CUDA uses shared memory. |
| `sync()` | `__syncthreads()` | Barrier synchronization. |
| `load_global()` | `cudaMemcpy` / Global Load | High-latency access to off-chip or remote memory. |
| `vec8` | `float4` / `float8` | SIMD vector types for data-parallel arithmetic. |
| `relu()`, `gelu()` | Custom Device Functions | Built-in hardware-accelerated activations. |
