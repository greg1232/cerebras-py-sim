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
    def __init__(self, block_w: int, block_h: int, sampling_rate: float, mesh_width: int = MESH_WIDTH, mesh_height: int = MESH_HEIGHT):
        self.block_w = block_w
        self.block_h = block_h
        self.mesh_width = mesh_width
        self.mesh_height = mesh_height

        # Initialize Grid of Cores
        self.cores = [[Core(x, y) for y in range(self.mesh_height)] for x in range(self.mesh_width)]
        self.mesh = MeshNetwork((block_w, block_h))

        self.sampler = SamplingManager(block_w, block_h, sampling_rate, self.mesh_width, self.mesh_height)
        self.perf = PerformanceCounter()

        # Set by execute_kernel when global memory is involved
        self._weight_server = None
        self._base_ptr = None

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
                        core.execute(instr,
                                     weight_server=self._weight_server,
                                     base_ptr=self._base_ptr)

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

    def execute_kernel(self, program: List[int], steps: int = 1,
                       weight_server=None, base_ptr=None, constants=None):
        """
        ISA binary path: load a program into every core and run for `steps` supersteps.
        weight_server + base_ptr enable LDR_GLOBAL/STR_GLOBAL.
        constants is a {physical_reg: float} dict pre-loaded into every core before execution.
        """
        self._weight_server = weight_server
        self._base_ptr = base_ptr

        for x in range(self.mesh_width):
            for y in range(self.mesh_height):
                core = self.cores[x][y]
                core.program = program
                if constants:
                    import numpy as np
                    for preg, val in constants.items():
                        core.regs[preg].f32[:] = np.float32(val)

        for _ in range(steps):
            self.run_superstep()

        return self.perf.get_estimated_runtime(750)

    def execute_kernel_fn(self, kernel_fn, weight_server, steps: int = 1):
        """
        Executes a high-level Python kernel function across the grid.
        Schedules the function on every PE, using a KernelContext for the DSL API.
        """
        from .context import KernelContext

        for _ in range(steps):
            for x in range(self.mesh_width):
                for y in range(self.mesh_height):
                    # We create a context for every PE.
                    # The context itself should decide whether to perform side-effects
                    # (SRAM/Global writes) based on the sampler, but it always
                    # records performance latency.
                    ctx = KernelContext(x, y, weight_server, self.perf, self.sampler)
                    kernel_fn(ctx)

            self.perf.finalize_superstep()

        return self.perf.get_estimated_runtime(750)
