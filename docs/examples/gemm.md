# GEMM (General Matrix Multiplication)

GEMM is the core operation for most AI workloads, serving as the foundation for linear layers in neural networks. This example demonstrates a high-performance GEMM implementation on the Cerebras-sim architecture.

## Launch Configuration

- **Grid:** 800 x 900 PEs
- **Tile Size:** 16 x 16

## Kernel Logic

The implementation follows a tiled, systolic approach to maximize data reuse and compute throughput.

### 1. Tiling
The output matrix $C$ is partitioned into tiles. Each Processing Element (PE) is responsible for computing a specific $16 \times 16$ tile of the output matrix.

### 2. SRAM Buffering
To minimize global memory traffic, tiles of matrices $A$ and $B$ are loaded from the Weight Server into the 48KB local SRAM of each PE. This allows the PE to perform multiple operations on the same data without re-fetching from the server.

### 3. Inner Loop
The compute core utilizes SIMD-8 FMA (Fused Multiply-Add) operations. The inner loop executes:
`C += A * B`
This is performed over the local tiles until the partial sum for the output tile is complete.

### 4. Data Movement
The kernel employs a systolic dataflow using the mesh network. Tiles of matrix $A$ are shifted horizontally across the wafer, and tiles of matrix $B$ are shifted vertically. This movement ensures that data is reused across multiple PEs, drastically reducing the required bandwidth from the Weight Server.

## CS3 DSL Implementation

```cs3
kernel gemm_kernel {
    grid = [800, 900];
    tile = [16, 16];

    sram {
        buffer a_tile[16][16];
        buffer b_tile[16][16];
        buffer c_tile[16][16];
    }

    compute {
        // Load initial tiles from Weight Server
        load(a_tile, weight_server.A[grid.x]);
        load(b_tile, weight_server.B[grid.y]);

        for (int k = 0; k < K_BLOCKS; ++k) {
            // SIMD-8 FMA Inner Loop
            simd_fma(c_tile, a_tile, b_tile);

            // Systolic Shift
            shift_right(a_tile); // Move A horizontally
            shift_down(b_tile);  // Move B vertically
        }
    }
}
```

## Analysis

### Systolic Dataflow
The dataflow is designed as a "wavefront." Matrix $A$ enters from the left edge of the mesh and propagates rightward, while Matrix $B$ enters from the top edge and propagates downward. As $A$ and $B$ meet at each PE, the local FMA units compute the partial products for the corresponding $C$ tile.

### Performance Estimate
- **Compute Intensity:** High. The use of SIMD-8 FMAs and local SRAM buffering ensures the compute units are rarely stalled.
- **Bottleneck:** The primary bottlenecks are the local SRAM capacity (limiting the maximum tile size) and the Mesh bandwidth during the systolic tile shifts.
- **Compute-to-Comm Ratio:** The ratio is highly favorable due to the systolic reuse. Since each element of $A$ and $B$ is used $N$ times (where $N$ is the dimension of the grid/tile), the communication cost is amortized over a large number of floating-point operations.

**Summary:**
- **Mesh Use:** Heavy (systolic data movement).
- **Efficiency:** High, leveraging maximum hardware parallelism and data reuse.
