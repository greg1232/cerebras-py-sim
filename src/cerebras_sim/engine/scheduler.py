from typing import List
from ..hw.core import Core
from ..hw.mesh import MeshNetwork
from .sampler import SamplingManager
from .perf_model import PerformanceCounter
from ..utils.constants import MESH_WIDTH, MESH_HEIGHT

class BSPScheduler:
    """
    Orchestrates the Bulk Synchronous Parallel execution loop.
    """
    def __init__(self, block_width: int, block_height: int, sampling_rate: float):
        self.cores = [[Core(x, y) for y in range(MESH_HEIGHT)] for x in range(MESH_WIDTH)]
        self.mesh = MeshNetwork(block_width, block_height)
        self.sampler = SamplingManager(block_width, block_height, sampling_rate)
        self.perf = PerformanceCounter()

    def run_superstep(self):
        """
        Executes one BSP superstep: Compute -> Communicate -> Sync.
        """
        # 1. Compute Phase
        for x in range(MESH_WIDTH):
            for y in range(MESH_HEIGHT):
                core = self.cores[x][y]
                if core.halted:
                    continue

                # Determine if this PE is functionally simulated or abstractly timed
                is_sampled = self.sampler.is_pe_sampled(x, y)

                # Fetch & Execute (Simplified for skeleton)
                # In a real run, we'd fetch the opcode from core.sram[core.pc]
                opcode = "VADD" # Dummy for now

                # Performance Tracking: Always count latency
                self.perf.add_instruction_latency(opcode)

                # Functional Track: Only compute if sampled
                if is_sampled:
                    # core.execute_vadd(...)
                    pass

                core.pc += 4 # Advance PC

        # 2. Communicate Phase (Mesh movement)
        # We simulate the mesh logic globally for the superstep
        # This is where the mesh routing logic from mesh.py is invoked
        # and mesh latencies are added to self.perf.

        # 3. Sync Phase
        self.perf.finalize_superstep()

    def execute_kernel(self, steps: int):
        """Runs the wafer for a fixed number of supersteps."""
        for i in range(steps):
            self.run_superstep()
        return self.perf.get_estimated_runtime(750) # Return seconds at 750MHz
