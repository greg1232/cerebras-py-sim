import numpy as np
from typing import List, Tuple
from ..hw.core import Core
from ..hw.mesh import MeshNetwork, MeshPacket, Direction
from ..engine.sampler import SamplingManager
from ..engine.perf_model import PerformanceCounter
from ..engine.decoder import decode_instruction
from ..utils.constants import MESH_WIDTH, MESH_HEIGHT, LATENCIES

class BSPScheduler:
    """
    Orchestrates the Bulk Synchronous Parallel execution loop for the CS3 wafer.
    """
    def __init__(self, block_w: int, block_h: int, sampling_rate: float, mesh_width: int = MESH_WIDTH, mesh_height: int = MESH_HEIGHT, verbose: bool = False):
        self.block_w = block_w
        self.block_h = block_h
        self.mesh_width = mesh_width
        self.mesh_height = mesh_height
        self.verbose = verbose

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
        1. Compute Phase: Tick-based execution. PEs execute instructions one by one.
           PESS stall if they hit a WAIT/RECV with empty buffers.
           The phase ends when all PEs in sampled blocks reach a SYNC or HALT.
        2. Communicate Phase: Flush internal mesh routing.
        3. Sync Phase: Update global clock.
        """
        num_blocks_x = self.mesh_width // self.block_w
        num_blocks_y = self.mesh_height // self.block_h

        # Track which PEs are still active (not halted and not at a barrier)
        # We only track active status for sampled blocks.
        active_pes = []
        for bx in range(num_blocks_x):
            for by in range(num_blocks_y):
                if self.sampler.should_simulate_block(bx, by):
                    for x in range(bx * self.block_w, (bx + 1) * self.block_w):
                        for y in range(by * self.block_h, (by + 1) * self.block_h):
                            active_pes.append(self.cores[x][y])

        # --- Tick-based Compute Loop ---
        tick = 0
        while active_pes:
            tick += 1
            tick_latency = 0
            still_active = []

            if self.verbose:
                print(f"--- Tick {tick} ---")

            # IMPORTANT: We must process PEs in a way that avoids bias,
            # but for a simple functional sim, a stable order is fine.
            for core in active_pes:
                if core.halted:
                    continue

                if core.pc >= len(core.program):
                    core.halted = True
                    continue

                binary = core.program[core.pc]
                try:
                    instr = decode_instruction(binary)
                except Exception:
                    instr = None

                if instr is None:
                    core.pc += 1
                    still_active.append(core)
                    continue

                # 1. Handle Mesh/Control instructions in the scheduler (The "Tick" logic)
                stalled = False
                if instr.opcode == "MESH":
                    stalled = self._handle_mesh_instr(core, instr)
                elif instr.opcode == "CONTROL" and instr.func == 0x03: # SYNC
                    # PE has reached the barrier for this superstep
                    if self.verbose:
                        print(f"[Tick] PE({core.x},{core.y}) reached SYNC")
                    continue
                else:
                    # 2. Regular execution
                    stalled, latency = core.execute(instr,
                                                 weight_server=self._weight_server,
                                                 base_ptr=self._base_ptr)
                    tick_latency = max(tick_latency, latency)
                    if self.verbose:
                        op_name = f"{instr.opcode}" if instr.opcode != "CONTROL" else f"CTRL_{instr.func}"
                        print(f"[Tick] PE({core.x},{core.y}) EXEC {op_name} (lat={latency}, stall={stalled})")

                if not stalled:
                    core.pc += 1

                still_active.append(core)

            # Update global cycles for this tick
            self.perf.current_step_cycles += tick_latency
            active_pes = still_active
            if tick > 1000:
                break

        # --- 2. Communicate Phase ---
        self._process_mesh_traffic()

        # --- 3. Sync Phase ---
        self.perf.finalize_superstep()

    def _handle_mesh_instr(self, core: Core, instr: any) -> bool:
        """
        Handles MESH instructions (SEND/RECV/WAIT).
        Returns: True if the PE is stalled (cannot advance PC).
        """
        func = instr.func

        # SEND instructions (0x00 - 0x03)
        if 0x00 <= func <= 0x03:
            direction = Direction(func)
            pkt = MeshPacket(payload=b'\x00', source_dir=direction, flags=0)
            try:
                self.mesh.send_packet(core.x, core.y, direction, pkt)
                if self.verbose:
                    print(f"[Tick] PE({core.x},{core.y}) SEND {direction.name}")
            except OverflowError:
                if self.verbose:
                    print(f"[Tick] PE({core.x},{core.y}) SEND {direction.name} STALLED (Overflow)")
                return True
            return False

        # RECV instructions (0x04 - 0x07)
        if 0x04 <= func <= 0x07:
            direction = Direction(func - 4)
            if self.mesh.has_packet(core.x, core.y, direction):
                pkt = self.mesh.recv_packet(core.x, core.y, direction)
                # Use the rd field from the instruction for the target register
                # We just simulate a successful load of 1.0
                core.regs[instr.rd].f32[:] = 1.0
                if self.verbose:
                    print(f"[Tick] PE({core.x},{core.y}) RECV {direction.name} -> reg {instr.rd} (1.0)")
                return False
            if self.verbose:
                print(f"[Tick] PE({core.x},{core.y}) RECV {direction.name} STALLED (Empty)")
            return True

        # WAIT instructions (0x08 - 0x0B)
        if 0x08 <= func <= 0x0B:
            direction = Direction(func - 8)
            if self.mesh.has_packet(core.x, core.y, direction):
                if self.verbose:
                    print(f"[Tick] PE({core.x},{core.y}) WAIT {direction.name} RESOLVED")
                return False
            if self.verbose:
                print(f"[Tick] PE({core.x},{core.y}) WAIT {direction.name} STALLED")
            return True

        return False

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
