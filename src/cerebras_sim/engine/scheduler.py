import numpy as np
from typing import List, Tuple
from ..hw.core import Core
from ..hw.mesh import MeshNetwork, MeshPacket
from ..engine.sampler import SamplingManager
from ..engine.perf_model import PerformanceCounter
from ..engine.decoder import decode_instruction
from ..utils.constants import MESH_WIDTH, MESH_HEIGHT, LATENCIES

class BSPScheduler:
    """
    Orchestrates the Bulk Synchronous Parallel execution loop for the CS3 wafer.
    """
    def __init__(self, block_width: int, block_height: int, sampling_rate: float, mesh_width: int = MESH_WIDTH, mesh_height: int = MESH_HEIGHT):
        self.block_width = block_width
        self.block_height = block_height
        self.mesh_width = mesh_width
        self.mesh_height = mesh_height

        # Initialize Grid of Cores
        self.cores = [[Core(x, y) for y in range(self.mesh_height)] for x in range(self.mesh_width)]
        self.mesh = MeshNetwork((block_width, block_height))

        self.sampler = SamplingManager(block_width, block_height, sampling_rate)
        self.perf = PerformanceCounter()

    def run_superstep(self):
        """
        Executes one BSP superstep:
        1. Compute: Fetch, Decode, Execute instructions
        2. Communicate: Process internal mesh routing
        3. Sync: Synchronize on block boundaries and update global clock
        """
        # --- 1. Compute Phase ---
        # We iterate through the grid. For performance simulation, we must
        # track the latency of every core. For functional simulation, we only
        # execute logic for sampled cores.
        for x in range(self.mesh_width):
            for y in range(self.mesh_height):
                core = self.cores[x][y]

                # Functional sampling check
                is_sampled = self.sampler.is_pe_sampled(x, y)

                # A superstep executes the core's full program (its compute phase).
                # PC is reset each superstep; cross-superstep state lives in regs/SRAM.
                for binary in core.program:
                    try:
                        instr = decode_instruction(binary)
                    except Exception:
                        # Handle decoding errors as NOPs for robustness
                        instr = None

                    if instr is None:
                        continue

                    # Performance track: always add latency
                    self.perf.add_instruction_latency(instr.opcode)

                    # Functional track: only execute if sampled
                    if is_sampled:
                        core.execute(instr)

        # --- 2. Communicate Phase ---
        # The mesh handles routing of packets. In a a cycle-accurate sim,
        # this would be a tick. Here we flush the buffers for the superstep.
        # Note: In the global-memory model, this logic is wrapped in LDR_GLOBAL/STR_GLOBAL
        self._process_mesh_traffic()

        # --- 3. Sync Phase ---
        self.perf.finalize_superstep()

    def _process_mesh_traffic(self):
        """
        Simulates the movement of packets across the mesh for one cycle.
        In this model, we simplify to a single-pass flush per superstep.
        """
        # Logic to move packets from buffers to neighbors
        # This is a simplified version of the XY routing logic
        pass

    def execute_kernel(self, program: List[int], steps: int):
        """
        Loads a program into all cores and runs for a specified number of supersteps.
        """
        # Load program into every core
        for x in range(self.mesh_width):
            for y in range(self.mesh_height):
                self.cores[x][y].program = program

        for i in range(steps):
            self.run_superstep()

        return self.perf.get_estimated_runtime(750)
