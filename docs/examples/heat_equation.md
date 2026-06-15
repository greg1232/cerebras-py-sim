# 2D Heat Equation Example

The 2D Heat Equation is a classic stencil computation, making it an ideal candidate for demonstrating the Tungsten dataflow model. This example showcases how to implement a grid-based simulation where each Processing Element (PE) manages a local tile of the global grid and communicates with its neighbors to update boundary values.

## Configuration

To simulate a large-scale heat diffusion process, we launch the kernel with the following parameters:

- **Global Grid Size**: $800 \times 900$
- **Tile Size (per PE)**: $16 \times 16$
- **PE Grid**: $50 \times 56$ (approximately)

Each PE is responsible for computing the heat evolution of its assigned $16 \times 16$ tile.

## Kernel Logic

The implementation follows a synchronous dataflow pattern across the PE array:

1. **Local State**: Each PE maintains the current temperature values $u(x,y)$ for its tile in local SRAM.
2. **Halo Exchange**: To compute the Laplacian for boundary pixels, PEs exchange their edge rows and columns with neighbors. This is now performed using `load_global` and `store_global` operations, which abstract the underlying mesh movement.
3. **Stencil Compute**: Once the halo is received, the PE computes the next time step $u_{t+1}$ using the 5-point Laplacian stencil:
   $$u_{t+1} = u_{t} + \alpha \Delta t \left( \frac{u_{i+1,j} + u_{i-1,j} + u_{i,j+1} + u_{i,j-1} - 4u_{i,j}}{\Delta x^2} \right)$$
4. **Sync**: A call to `sync()` marks the completion of the superstep, ensuring all PEs have finished their computation and communication before proceeding to the next time step.
5. **Loop**: This process repeats for $T$ time steps.

## CS3 DSL Implementation

```cs3
kernel heat_equation {
    // Grid parameters
    const TILE_W = 16;
    const TILE_H = 16;
    
    // Local state in SRAM
    float u[TILE_W][TILE_H];
    float u_next[TILE_W][TILE_H];
    float halo_n[TILE_W], halo_s[TILE_W], halo_e[TILE_H], halo_w[TILE_H];

    loop t in 0..T {
        // 1. Halo Exchange: Share boundary values with neighbors via global memory
        // North boundary
        store_global(output, (py-1)*800*64 + px*64, u[0..TILE_W-1][0]);
        halo_n = load_global(input, (py-1)*800*64 + px*64);
        
        // South boundary
        store_global(output, (py+1)*800*64 + px*64, u[0..TILE_W-1][TILE_H-1]);
        halo_s = load_global(input, (py+1)*800*64 + px*64);
        
        // East boundary
        store_global(output, py*800*64 + (px+1)*64, u[TILE_W-1][0..TILE_H-1]);
        halo_e = load_global(input, py*800*64 + (px+1)*64);
        
        // West boundary
        store_global(output, py*800*64 + (px-1)*64, u[0][0..TILE_H-1]);
        halo_w = load_global(input, py*800*64 + (px-1)*64);

        // 2. Compute 5-point stencil
        for x in 0..TILE_W-1 {
            for y in 0..TILE_H-1 {
                float center = u[x][y];
                float north = (y == 0) ? halo_n[x] : u[x][y-1];
                float south = (y == TILE_H-1) ? halo_s[x] : u[x][y+1];
                float west  = (x == 0) ? halo_w[y] : u[x-1][y];
                float east  = (x == TILE_W-1) ? halo_e[y] : u[x+1][y];
                
                u_next[x][y] = center + alpha * (north + south + west + east - 4*center);
            }
        }

        // Update state for next timestep
        u = u_next;
        
        // 3. Synchronize the PE array
        sync();
    }
}
```

## Execution Timeline (Halo Exchange)

The halo exchange occurs in a coordinated superstep. Below is the conceptual timeline of events for a single PE:

```text
Time Step t:
|--- [Compute Internal] ---|
|--- [SEND N,S,E,W] ------>| (Async Mesh Transfer)
| <--- [RECV N,S,E,W] ----| (Blocking on Halo Arrival)
|--- [Compute Boundary] ---|
|--- [sync()] ------------>| (Barrier)
|--- [Next Step t+1] ----->|
```

## Analysis

### Compute Intensity
The compute intensity is **Medium**. While the stencil operation is simple (a few additions and multiplications per pixel), the high volume of data movement relative to computation makes the kernel sensitive to mesh performance.

### Bottlenecks
The primary bottleneck is **Mesh Latency**. Because every PE must wait for its four neighbors to provide their boundary values before the boundary computations can finalize, the synchronization overhead and communication latency dominate the execution time.

### Mesh Utilization
**Maximum**. This kernel exhibits a high degree of spatial locality and connectivity. Every PE in the grid communicates with all four cardinal neighbors in every single time step, fully utilizing the 2D torus mesh interconnect.

### Performance Estimate
Given the tile size and the mesh speed, the estimated performance is:
- **Cycles per time step**: $\approx 1,200$ cycles (including communication overhead and SRAM access).
