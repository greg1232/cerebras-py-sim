# Host-Device Interface (HDI) Specification

This document defines the host-device interface for the CS3 simulator. The CS3 programming model is CUDA-inspired, utilizing an asynchronous command-queue system to manage work submission and memory orchestration between the host and the Wafer-Scale Engine (WSE).

## 1. Command Queue

The host communicates with the CS3 via one or more ordered command queues. A command queue is an abstraction analogous to a CUDA stream; commands submitted to a single queue are guaranteed to execute in the order they were enqueued.

### 1.1 Queue Properties
- **Ordering:** Strict FIFO execution within a single queue.
- **Concurrency:** Multiple queues may be created to allow independent work streams to execute concurrently on the device.
- **Asynchrony:** Command submission is non-blocking. The host continues execution immediately after enqueuing a command.

### 1.2 Command Set
The following commands are supported by the CS3 Command Queue:

| Command | Description |
| :--- | :--- |
| `MALLOC` | Allocates a block of memory on the Weight Server. |
| `FREE` | Deallocates a previously allocated block of memory. |
| `MEMCPY_H2D` | DMA transfer from host memory to the Weight Server. |
| `MEMCPY_D2H` | DMA transfer from the Weight Server to host memory. |
| `KERNEL_LAUNCH` | Triggers execution of a kernel across a specified grid of PEs. |
| `SYNC_BARRIER` | Internal device barrier; ensures previous commands in the queue complete. |

---

## 2. Device Memory (Weight Server)

The CS3 utilizes a massive external Weight Server as its primary device memory pool, supporting up to 1.5TB of addressable space.

### 2.1 Memory Model
- **DevicePtr:** A 64-bit opaque handle representing a physical address in the Weight Server's memory space.
- **Access:** `DevicePtr` cannot be dereferenced by the host CPU. All data movement must occur via explicit memory transfer commands.

### 2.2 Allocation API
- `cs3_malloc(size_t bytes) -> DevicePtr`
  Allocates a contiguous block of memory from the pool. Returns a valid `DevicePtr` or `NULL` if allocation fails.
- `cs3_free(DevicePtr ptr)`
  Returns the memory block associated with the pointer to the pool.

---

## 3. Memory Transfer

Memory transfers utilize the CS3's high-bandwidth IO fabric, consisting of 12x 100Gbps links.

### 3.1 Transfer API
- `cs3_memcpy_h2d(DevicePtr dst, void *src, size_t bytes, CS3Queue *q)`
  Asynchronously initiates a DMA transfer from host memory (`src`) to the Weight Server (`dst`).
- `cs3_memcpy_d2h(void *dst, DevicePtr src, size_t bytes, CS3Queue *q)`
  Asynchronously initiates a DMA transfer from the Weight Server (`src`) to host memory (`dst`).

### 3.2 Performance Characteristics
- **Aggregate Bandwidth:** Up to $12 \times 100\text{ Gbps} \approx 150\text{ GB/s}$.
- **Execution:** Transfers are enqueued on the provided `CS3Queue` and execute only after all preceding commands in that queue have completed.

---

## 4. Kernel Launch

Kernels are launched across a 2D grid of Processing Elements (PEs).

### 4.1 Launch API
`cs3_launch(CS3Kernel *kernel, KernelArgs args, Grid2D grid, Tile2D tile, CS3Queue *q)`

### 4.2 Parameter Definitions
- **`CS3Kernel`**: A handle to the compiled kernel binary stored on the device.
- **`Grid2D`**: Defines the active compute area.
  - `width`: Number of PEs in X dimension (Max 800).
  - `height`: Number of PEs in Y dimension (Max 900).
- **`Tile2D`**: Defines the synchronization domain (tile width $\times$ tile height).
- **`KernelArgs`**: A packed structure containing scalar constants and `DevicePtr` values passed to every PE in the grid.

---

## 5. Synchronization

To synchronize the host and device, the host can block until the device catches up to the submission point.

### 5.1 Sync API
- `cs3_queue_sync(CS3Queue *q)`
  Blocks the calling host thread until all commands previously enqueued on the specified queue `q` have finished execution.

---

## 6. C API Declarations

```c
#include <stdint.h>
#include <stddef.h>

// Types
typedef uint64_t DevicePtr;
typedef struct CS3Queue CS3Queue;
typedef struct CS3Kernel CS3Kernel;

typedef struct {
    uint32_t width;
    uint32_t height;
} Grid2D;

typedef struct {
    uint32_t tile_w;
    uint32_t tile_h;
} Tile2D;

typedef struct {
    uint64_t args_data[16]; // Packed scalars and DevicePtrs
} KernelArgs;

// Memory Management
DevicePtr cs3_malloc(size_t bytes);
void      cs3_free(DevicePtr ptr);

// Memory Transfer
void cs3_memcpy_h2d(DevicePtr dst, void *src, size_t bytes, CS3Queue *q);
void cs3_memcpy_d2h(void *dst, DevicePtr src, size_t bytes, CS3Queue *q);

// Execution
void cs3_launch(CS3Kernel *kernel, KernelArgs args, Grid2D grid, Tile2D tile, CS3Queue *q);

// Synchronization
void cs3_queue_sync(CS3Queue *q);
```

## 7. End-to-End Example

The following example demonstrates a typical workflow: allocating memory, uploading data, launching a compute kernel, and retrieving results.

```c
void run_simulation() {
    CS3Queue *q = cs3_create_queue();
    
    // 1. Allocate device memory for input and output buffers
    DevicePtr d_in  = cs3_malloc(1024 * 1024);
    DevicePtr d_out = cs3_malloc(1024 * 1024);
    
    // 2. Transfer data from host to device (Asynchronous)
    float host_input[262144]; 
    cs3_memcpy_h2d(d_in, host_input, sizeof(host_input), q);
    
    // 3. Define kernel launch parameters
    Grid2D grid = { .width = 400, .height = 400 };
    Tile2D tile = { .tile_w = 32, .tile_h = 32 };
    KernelArgs args = { .args_data[0] = (uint64_t)d_in, .args_data[1] = (uint64_t)d_out };
    
    // 4. Launch the kernel (Asynchronous)
    cs3_launch(&my_kernel, args, grid, tile, q);
    
    // 5. Transfer results back to host (Asynchronous)
    float host_output[262144];
    cs3_memcpy_d2h(host_output, d_out, sizeof(host_output), q);
    
    // 6. Block until all operations are complete
    cs3_queue_sync(q);
    
    // Cleanup
    cs3_free(d_in);
    cs3_free(d_out);
}
```

## 8. Comparison to CUDA

| CS3 Concept | CUDA Equivalent | Notes |
| :--- | :--- | :--- |
| `CS3Queue` | `cudaStream_t` | Both provide ordered, asynchronous command submission. |
| `DevicePtr` | `device pointer` | Both are opaque to the host and require DMA for access. |
| `cs3_malloc` | `cudaMalloc` | CS3 allocates from a dedicated external Weight Server. |
| `cs3_memcpy_h2d` | `cudaMemcpyAsync` | Specifically targets the 12x 100Gbps IO fabric. |
| `cs3_launch` | `cudaLaunchKernel` | Maps to a 2D grid of PEs instead of blocks/threads. |
| `cs3_queue_sync` | `cudaStreamSynchronize` | Blocks host until the stream/queue is empty. |
