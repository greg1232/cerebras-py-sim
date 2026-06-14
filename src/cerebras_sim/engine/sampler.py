import random
from typing import Set, Tuple
from ..utils.constants import MESH_WIDTH, MESH_HEIGHT

class SamplingManager:
    """
    Implements the Block-Level Sampling strategy.
    Determines which thread blocks are fully simulated vs. abstractly timed.
    """
    def __init__(self, block_width: int, block_height: int, sampling_rate: float = 0.01):
        self.block_width = block_width
        self.block_height = block_height
        self.sampling_rate = sampling_rate

        self.num_blocks_x = MESH_WIDTH // block_width
        self.num_blocks_y = MESH_HEIGHT // block_height

        # The set of blocks chosen for full functional simulation
        self.sampled_blocks: Set[Tuple[int, int]] = set()
        self._generate_samples()

    def _generate_samples(self):
        """Randomly select blocks based on the sampling rate."""
        total_blocks = self.num_blocks_x * self.num_blocks_y
        num_to_sample = max(1, int(total_blocks * self.sampling_rate))

        # Generate all possible block coordinates
        all_blocks = [
            (bx, by)
            for bx in range(self.num_blocks_x)
            for by in range(self.num_blocks_y)
        ]

        self.sampled_blocks = set(random.sample(all_blocks, num_to_sample))

    def should_simulate_block(self, block_x: int, block_y: int) -> bool:
        """Check if a specific block is in the functional sample set."""
        return (block_x, block_y) in self.sampled_blocks

    def is_pe_sampled(self, pe_x: int, pe_y: int) -> bool:
        """Determine if a specific PE should be functionally simulated."""
        block_x = pe_x // self.block_width
        block_y = pe_y // self.block_height
        return self.should_simulate_block(block_x, block_y)
