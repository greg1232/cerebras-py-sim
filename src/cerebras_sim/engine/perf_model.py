from ..utils.constants import LATENCIES
from dataclasses import dataclass

@dataclass
class PerformanceCounter:
    """
    Tracks the global cycle count and total execution time for the wafer.
    """
    total_cycles: int = 0
    current_step_cycles: int = 0

    def add_instruction_latency(self, opcode: str):
        """Add the latency of a specific instruction to the current superstep."""
        latency = LATENCIES.get(opcode, 1)
        self.current_step_cycles = max(self.current_step_cycles, latency)

    def add_mesh_latency(self, hops: int):
        """Add mesh communication latency (1 cycle per hop)."""
        self.current_step_cycles = max(self.current_step_cycles, hops)

    def finalize_superstep(self):
        """Commit the max latency of the superstep to the global counter."""
        self.total_cycles += self.current_step_cycles
        self.current_step_cycles = 0

    def get_estimated_runtime(self, clock_mhz: int) -> float:
        """Convert total cycles to seconds based on clock speed."""
        return self.total_cycles / (clock_mhz * 1e6)
