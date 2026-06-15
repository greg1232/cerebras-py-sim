import numpy as np
from src.cerebras_sim.compiler.kernel import cs3_kernel

# Constants for the kernel
B = 16  # Block size
K_BLOCKS = 4
A_PTR = 0x1000
B_PTR = 0x2000
C_PTR = 0x3000

@cs3_kernel(block_w=B, block_h=B)
def blocked_gemm_stencil_kernel(ctx):
    """
    Implements a Blocked GEMM with a final stencil operation.
    Constraint: Communication is only allowed within the block boundary.
    """
    # 1. Allocate SRAM tiles
    # We use dictionaries/handles as returned by ctx.sram_alloc
    a_tile = ctx.sram_alloc("a_tile", B * B)
    b_tile = ctx.sram_alloc("b_tile", B * B)
    c_tile = ctx.sram_alloc("c_tile", B * B)

    # PE coordinates and block-local coordinates
    px = ctx.pe_x()
    py = ctx.pe_y()
    local_x = px % B
    local_y = py % B

    # Initialize accumulator
    ctx.sram_store(c_tile, 0, 0.0)

    for k in range(K_BLOCKS):
        # --- LOAD PHASE ---
        # Each PE loads its starting tile based on its global position
        # Simulation: offsets are derived from k and PE indices
        val_a = ctx.load_global(A_PTR, (k * B * B) + (local_x * B) + local_y)
        ctx.sram_store(a_tile, local_x, val_a)

        val_b = ctx.load_global(B_PTR, (k * B * B) + (local_y * B) + local_x)
        ctx.sram_store(b_tile, local_y, val_b)

        ctx.sync()

        # --- COMPUTE & SHIFT PHASE (Systolic Wavefront) ---
        for i in range(B):
            # Data movement: Pull from neighbor if within block
            # Shift A (Horizontal)
            if local_x > 0:
                a_val = ctx.shift_right(a_tile, local_x - 1)
            else:
                a_val = ctx.sram_load(a_tile, local_x)

            # Shift B (Vertical)
            if local_y > 0:
                b_val = ctx.shift_down(b_tile, local_y - 1)
            else:
                b_val = ctx.sram_load(b_tile, local_y)

            # Compute: C += A * B
            current_c = ctx.sram_load(c_tile, 0)
            ctx.sram_store(c_tile, 0, current_c + (a_val * b_val))

        ctx.sync()

    # --- STENCIL PHASE ---
    # Perform a 4-neighbor average stencil on the final C result
    # Boundary check: only load from neighbor if they are in the same block
    sum_neighbors = 0.0

    # North
    if local_y > 0:
        sum_neighbors += ctx.neighbor_load(c_tile, "NORTH", 0)
    # South
    if local_y < B - 1:
        sum_neighbors += ctx.neighbor_load(c_tile, "SOUTH", 0)
    # East
    if local_x < B - 1:
        sum_neighbors += ctx.neighbor_load(c_tile, "EAST", 0)
    # West
    if local_x > 0:
        sum_neighbors += ctx.neighbor_load(c_tile, "WEST", 0)

    final_c = ctx.sram_load(c_tile, 0)
    # Apply stencil: New C = 0.5 * current + 0.125 * sum(neighbors)
    stencil_c = (final_c * 0.5) + (sum_neighbors * 0.125)

    # Store final result back to global memory
    ctx.store_global(C_PTR, (px * B + py) * 4, stencil_c)
