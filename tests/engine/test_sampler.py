import unittest
import sys
sys.path.insert(0, '/Users/gregorydiamos/checkout/cerebras-sim/src')
from cerebras_sim.engine.sampler import SamplingManager

class TestSamplingManager(unittest.TestCase):
    def test_full_sampling(self):
        # rate=1.0 should sample all blocks
        sm = SamplingManager(block_width=10, block_height=10, sampling_rate=1.0)
        total_blocks = (800 // 10) * (900 // 10)
        self.assertEqual(len(sm.sampled_blocks), total_blocks)

    def test_min_one_block(self):
        # rate=0.0001 should still sample at least 1 block
        sm = SamplingManager(block_width=10, block_height=10, sampling_rate=0.0001)
        self.assertGreaterEqual(len(sm.sampled_blocks), 1)

    def test_pe_to_block_mapping(self):
        # pe(0,0) maps to block(0,0)
        sm = SamplingManager(block_width=10, block_height=10, sampling_rate=0.01)
        # Force block(0,0) to be sampled for the test
        sm.sampled_blocks = {(0, 0)}
        self.assertTrue(sm.is_pe_sampled(0, 0))
        self.assertFalse(sm.is_pe_sampled(11, 0)) # belongs to block(1,0)
