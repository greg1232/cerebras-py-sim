import unittest
import sys
sys.path.insert(0, '/Users/gregorydiamos/checkout/cerebras-sim/src')
from cerebras_sim.engine.perf_model import PerformanceCounter

class TestPerformanceCounter(unittest.TestCase):
    def setUp(self):
        self.pc = PerformanceCounter()

    def test_instruction_latency(self):
        # VFMADD=1, VEXP=5 (from constants.py)
        self.pc.add_instruction_latency('VFMADD')
        self.assertEqual(self.pc.current_step_cycles, 1)

        self.pc.current_step_cycles = 0 # reset for next check
        self.pc.add_instruction_latency('VEXP')
        self.assertEqual(self.pc.current_step_cycles, 5)

    def test_max_not_sum(self):
        # two instructions take max latency per superstep
        self.pc.add_instruction_latency('VFMADD') # 1
        self.pc.add_instruction_latency('VEXP')   # 5
        self.assertEqual(self.pc.current_step_cycles, 5)

    def test_finalize(self):
        self.pc.current_step_cycles = 10
        self.pc.finalize_superstep()
        self.assertEqual(self.pc.total_cycles, 10)
        self.assertEqual(self.pc.current_step_cycles, 0)

    def test_runtime_estimate(self):
        # get_estimated_runtime divides cycles by (clock_mhz * 1e6):
        # 1000 cycles / (1000 * 1e6) = 1e-6 s
        self.pc.total_cycles = 1000
        self.assertAlmostEqual(self.pc.get_estimated_runtime(1000), 1e-6)
