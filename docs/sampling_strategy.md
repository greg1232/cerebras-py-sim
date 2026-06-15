# Sampling Strategy: Functional Verification at Scale

## Overview
The CS3 simulator is designed to model a massive array of Processing Elements (PEs). Simulating the full state and execution of ~720k cores in Python is computationally infeasible. To bridge the gap between functional correctness and simulation performance, the CS3 simulator employs a **Randomly Sampled Functional Verification** strategy.

## The Problem
Simulating 720k cores requires tracking millions of register states and SRAM contents, and processing billions of instructions per cycle. In a high-level language like Python, the overhead of object management and loop iteration for this many entities results in simulation speeds that are too slow for practical development cycles.

## The Solution: Block-Level Sampled Functional Verification
Instead of simulating every core, we simulate a representative subset of the grid at the block level. This allows us to verify that the kernel logic is functionally correct across the fabric without the overhead of full-scale simulation.

### 1. Sampling Unit
The unit of sampling is the **Thread Block** (e.g., 16x16 PEs).

**Rationale:** For stencil-based workloads (common in CS3), communication happens primarily between neighboring PEs. By sampling entire blocks, we ensure that every PE within a sampled block is fully simulated. This eliminates the "symmetry problem" within a block—we verify the entire block's internal communication, boundary logic, and synchronization. A block is either "Fully Simulated" (sampled) or "Abstractly Simulated" (timing only); there is no partial sampling within a block.

### 2. The Sampling Algorithm
Upon kernel launch, the simulator determines which elements of the grid will be fully simulated.

- **Sample Set ($S$):** A subset of the blocks $S \subset \text{Blocks}$ is generated.
- **Sampling Rate ($\rho$):** A configurable parameter (e.g., $\rho = 0.001$ for 0.1% or $\rho = 0.01$ for 1% of total blocks).
- **Distribution:** The set $S$ is chosen using a uniform random distribution across the grid dimensions.

### 3. Execution Path Divergence
The simulator bifurcates execution based on whether a PE/Tile is in the sample set $S$.

#### Sampled Path (Full Simulation)
All PEs within a sampled block undergo the full simulation pipeline:
`Instruction Fetch` $\rightarrow$ `Decode` $\rightarrow$ `Execute` $\rightarrow$ `Update SRAM/Registers` $\rightarrow$ `Inter-PE Communication`.

#### Non-Sampled Path (Abstract Execution)
Blocks not in $S$ are treated as "black boxes" that maintain timing:
- The simulator calculates the "typical" latency of the current instruction.
- The global clock advances based on this latency.
- No actual computation is performed; register and SRAM states are not updated.
- This ensures that the sampled blocks interact with the rest of the fabric at the correct relative time.

## Correctness Assumptions
This strategy relies on the **Symmetry of Execution**. Because all PEs in the CS3 architecture execute the same kernel code (SIMT-like behavior), we assume that the behavior of a randomly selected representative sample is indicative of the behavior of the entire grid. If the logic is correct for the sampled cores, it is functionally correct for all cores, provided the data distribution is uniform or the kernel is symmetric.

## Verification Workflow
To verify a new kernel, the following two-step process is used:

1. **Small Scale Simulation:**
   - Configure Grid = 16x16.
   - Set $\rho = 1.0$ (100% sampling).
   - Validate absolute functional correctness.

2. **Full Scale Simulation:**
   - Configure Grid = 800x900.
   - Set $\rho = 0.001$ (0.1% sampling).
   - Compare the output of the sampled cores in the Full Scale run against the expected results from the Small Scale run.

## Trade-off Analysis

| Sampling Rate ($\rho$) | Confidence in Correctness | Simulation Speed |
| :--- | :--- | :--- |
| $\uparrow$ High | $\uparrow$ Increases (Better coverage) | $\downarrow$ Decreases (Higher overhead) |
| $\downarrow$ Low | $\downarrow$ Decreases (Risk of missing edge cases) | $\uparrow$ Increases (Faster iterations) |

## Implementation Pseudo-code

The following logic determines if a specific block should be fully simulated:

```python
import random

class SamplingManager:
    def __init__(self, grid_width, grid_height, sampling_rate, tile_size=16):
        self.sampling_rate = sampling_rate
        self.tile_size = tile_size
        self.sampled_blocks = set()
        
        self._initialize_block_sampling(grid_width, grid_height)

    def _initialize_block_sampling(self, w, h):
        num_tiles_x = w // self.tile_size
        num_tiles_y = h // self.tile_size
        total_tiles = num_tiles_x * num_tiles_y
        num_to_sample = max(1, int(total_tiles * self.sampling_rate))
        
        # Select random block coordinates
        all_blocks = [(x, y) for x in range(num_tiles_x) for y in range(num_tiles_y)]
        self.sampled_blocks = set(random.sample(all_blocks, num_to_sample))

    def should_simulate_block(self, block_id, x=None, y=None):
        """
        Returns True if the block is part of the sample set.
        """
        if x is None or y is None:
            # Need coordinates to determine block
            raise ValueError("x and y coordinates required for block sampling")
        block_x = x // self.tile_size
        block_y = y // self.tile_size
        return (block_x, block_y) in self.sampled_blocks
```
