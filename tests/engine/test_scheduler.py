import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.engine.scheduler import BSPScheduler
from cerebras_sim.engine.decoder import decode_instruction

class TestBSPScheduler(unittest.TestCase):
    def test_scheduler_runtime_accumulation(self):
        # Setup: Grid 16x16 (small for testing) to avoid massive core allocation
        # Actually, let's monkeypatch MESH_WIDTH/HEIGHT for this test to keep it fast
        import cerebras_sim.utils.constants as const
        orig_w, orig_h = const.MESH_WIDTH, const.MESH_HEIGHT
        const.MESH_WIDTH, const.MESH_HEIGHT = 2, 2

        try:
            # Specify small grid dimensions (2x2) to keep tests fast
            scheduler = BSPScheduler(block_width=2, block_height=2, sampling_rate=1.0, mesh_width=2, mesh_height=2)

            # VADD binary: 0x04611000 (Latency = 1)
            program = [0x04611000]

            # Run 10 supersteps
            # Expected: 10 supersteps * max(VADD_latency=1, mesh=0) = 10 cycles
            scheduler.execute_kernel(program, steps=10)

            self.assertEqual(scheduler.perf.total_cycles, 10)
        finally:
            const.MESH_WIDTH, const.MESH_HEIGHT = orig_w, orig_h

    def test_functional_sampling_behavior(self):
        import cerebras_sim.utils.constants as const
        orig_w, orig_h = const.MESH_WIDTH, const.MESH_HEIGHT
        const.MESH_WIDTH, const.MESH_HEIGHT = 2, 2

        try:
            # Sampling rate 0.0 means only a minimal set (1 block) is simulated
            scheduler = BSPScheduler(block_width=2, block_height=2, sampling_rate=0.0, mesh_width=2, mesh_height=2)

            # VADD rd=3, rs1=1, rs2=2
            binary = 0x04611000
            program = [binary]

            # Setup state for one core
            core = scheduler.cores[0][0]
            core.regs[1].f32[:] = 1.0
            core.regs[2].f32[:] = 2.0
            core.set_mask(0xFF)

            scheduler.execute_kernel(program, steps=1)

            # Check if the core was sampled. If it was, reg[3] should be 3.0.
            # If not, it remains 0.0.
            is_sampled = scheduler.sampler.is_pe_sampled(0, 0)
            if is_sampled:
                self.assertEqual(core.regs[3].f32[0], 3.0)
            else:
                self.assertEqual(core.regs[3].f32[0], 0.0)

        finally:
            const.MESH_WIDTH, const.MESH_HEIGHT = orig_w, orig_h

if __name__ == "__main__":
    unittest.main()
