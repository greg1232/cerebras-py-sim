# Sampling Strategy: Functional Verification at Scale

## Overview
The CS3 simulator is designed to model a massive array of Processing Elements (PEs). Simulating the full state and execution of ~720k cores in Python is computationally infeasible. To bridge the gap between functional correctness and simulation performance, the CS3 simulator employs a **Randomly Sampled Functional Verification** strategy.

## The Problem
Simulating 720k cores requires tracking millions of register states and SRAM contents, and processing billions of instructions per cycle. In a high-level language like Python, the overhead of object management and loop iteration for this many entities results in simulation speeds that are too slow for practical development cycles.

## The Solution: Randomly Sampled Functional Verification
Instead of simulating every core, we simulate a representative subset of the grid. This allows us to verify that the kernel logic is functionally correct across the fabric without the overhead of full-scale simulation.

### 1. Sampling Unit
The simulator supports sampling at two levels:
- **Single PE:** Individual cores are selected randomly.
- **Tile (Recommended):** A block of PEs (e.g., 16x16) is selected as a single unit. 

**Rationale:** For stencil-based workloads (common in CS3), communication happens primarily between neighboring PEs. Sampling by Tile preserves local mesh communication patterns and synchronization boundaries, providing higher confidence in the correctness of the data-flow logic compared to sparse single-PE sampling.

### 2. The Sampling Algorithm
Upon kernel launch, the simulator determines which elements of the grid will be fully simulated.

- **Sample Set ($S$):** A subset of the grid $S \subset \text{Grid}$ is generated.
- **Sampling Rate ($\rho$):** A configurable parameter (e.g., $\rho = 0.001$ for 0.1% or $\rho = 0.01$ for 1% of total cores).
- **Distribution:** The set $S$ is chosen using a uniform random distribution across the grid dimensions.

### 3. Execution Path Divergence
The simulator bifurcates execution based on whether a PE/Tile is in the sample set $S$.

#### Sampled Path (Full Simulation)
Cores in $S$ undergo the full simulation pipeline:
`Instruction Fetch` $\rightarrow$ `Decode` $\rightarrow$ `Execute` $\rightarrow$ `Update SRAM/Registers` $\rightarrow$ `Inter-PE Communication`.

#### Non-Sampled Path (Abstract Execution)
Cores not in $S$ are treated as "black boxes" that maintain timing:
- The simulator calculates the "typical" latency of the current instruction.
- The global clock advances based on this latency.
- No actual computation is performed; register and SRAM states are not updated.
- This ensures that the sampled cores interact with the rest of the fabric at the correct relative time.

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

The following logic determines if a specific PE should be fully simulated:

```python
import random

class SamplingManager:
    def __init__(self, grid_width, grid_height, sampling_rate, sample_by_tile=True, tile_size=16):
        self.sampling_rate = sampling_rate
        self.sample_by_tile = sample_by_tile
        self.tile_size = tile_size
        self.sampled_tiles = set()
        
        if self.sample_by_tile:
            self._initialize_tile_sampling(grid_width, grid_height)
        else:
            self._initialize_pe_sampling(grid_width, grid_height)

    def _initialize_tile_sampling(self, w, h):
        num_tiles_x = w // self.tile_size
        num_tiles_y = h // self.tile_size
        total_tiles = num_tiles_x * num_tiles_y
        num_to_sample = max(1, int(total_tiles * self.sampling_rate))
        
        # Select random tile coordinates
        all_tiles = [(x, y) for x in range(num_tiles_x) for y in range(num_tiles_y)]
        self.sampled_tiles = set(random.sample(all_tiles, num_to_sample))

    def _initialize_pe_sampling(self, w, h):
        # For single PE sampling, we store a set of sampled PE IDs
        total_pes = w * h
        num_to_sample = max(1, int(total_pes * self.sampling_rate))
        self.sampled_pes = set(random.sample(range(total_pes), num_to_sample))

    def should_simulate_fully(self, pe_id, x=None, y=None):
        """
        Returns True if the PE is part of the sample set.
        """
        if self.sample_by_tile:
            if x is None or y is None:
                # Need coordinates to determine tile
                raise ValueError("x and y coordinates required for tile sampling")
            tile_x = x // self.tile_size
            tile_y = y // self.tile_size
            return (tile_x, tile_y) in self.sampled_tiles
        else:
            return pe_id in self.sampled_pes
```
