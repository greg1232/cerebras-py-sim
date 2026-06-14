# SAXPY Example (Single-precision A*X Plus Y)

SAXPY is a fundamental vector operation used extensively in linear algebra and scientific computing. This document describes the implementation and performance analysis of SAXPY on the Cerebras system.

## Launch Configuration

- **Grid Size**: 800x900 PEs
- **Tile Size**: 16x16
- **Total Elements**: 720,000 (800 * 900)

## Kernel Logic

The kernel implements the operation $Z = a \cdot X + Y$.

1. **Scalar Load**: Load the constant scalar `a` into a register.
2. **Vector Load**: Load elements $X[i]$ and $Y[i]$ from the Weight Server into local SRAM using Data Stream Descriptors (DSDs).
3. **Compute**: Perform a SIMD-8 operation: $Z = a \cdot X + Y$.
4. **Vector Store**: Store the resulting $Z[i]$ back to the Weight Server.

## CS3 DSL Implementation

```cs3
// SAXPY Kernel
kernel saxpy(float a, vector X, vector Y, vector Z) {
    // Load scalar a
    reg float scalar_a = load_scalar(a);

    // Define DSDs for X and Y
    dsd x_stream = dsd_weight_server(X);
    dsd y_stream = dsd_weight_server(Y);
    dsd z_stream = dsd_weight_server(Z);

    // SIMD-8 loop
    for (int i = 0; i < TILE_SIZE; i += 8) {
        float x_vec = x_stream.read_simd8();
        float y_vec = y_stream.read_simd8();
        
        float z_vec = scalar_a * x_vec + y_vec;
        
        z_stream.write_simd8(z_vec);
    }
}
```

## Execution Trace (Single PE)

For a single Processing Element (PE) handling a 16x16 tile:

1. **Cycle 0**: `scalar_a` is loaded into a general-purpose register.
2. **Cycle 1-10**: DSDs are initialized and the first SIMD-8 block of `X` and `Y` is requested from the Weight Server.
3. **Cycle 11**: `X[0-7]` and `Y[0-7]` arrive in SRAM.
4. **Cycle 12**: SIMD unit computes `a * X[0-7] + Y[0-7]`.
5. **Cycle 13**: Result `Z[0-7]` is buffered for write-back to the Weight Server.
6. **Cycle 14-20**: Pipeline overlaps the next load with the current store.
7. **Repeat**: This sequence repeats for the remaining 8 elements of the tile.

## Analysis

### Compute Intensity
The compute intensity is **very low**. For every two loads and one store (3 memory operations), only two floating-point operations (1 multiply, 1 add) are performed.

### Bottleneck
The primary bottleneck is **memory bandwidth**. The performance is limited by the IO links between the PE and the Weight Server, as the SIMD units spend most of their time waiting for data.

### Mesh Usage
Mesh usage is **minimal**. Since there is no communication between PEs during the compute phase, the mesh is only used for global synchronization (barrier) to signal completion of the kernel.

## Performance Estimate

Assuming the system is memory-bound:
- **Data per element**: 3 words (X, Y, Z) * 4 bytes = 12 bytes.
- **Total Data**: $720,000 \text{ elements} \times 12 \text{ bytes} \approx 8.64 \text{ MB}$.
- **Throughput**: With the Weight Server interface operating at peak bandwidth, the total execution time is dominated by the round-trip latency and bandwidth of the IO links.
- **Estimated Cycles**: For 720k elements distributed across 720k PEs (1 element per PE), the execution time is essentially the latency of a single tile execution ($\approx 20\text{--}50$ cycles) plus global synchronization overhead.
