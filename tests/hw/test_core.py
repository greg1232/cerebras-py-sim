import numpy as np
import unittest
import sys
sys.path.insert(0, '/Users/gregorydiamos/checkout/cerebras-sim/src')
from cerebras_sim.hw.core import VectorReg, Core

class TestVectorReg(unittest.TestCase):
    def test_f32_initializes_to_zeros(self):
        reg = VectorReg()
        np.testing.assert_array_equal(reg.f32, np.zeros(8, dtype=np.float32))

class TestCore(unittest.TestCase):
    def setUp(self):
        self.core = Core(0, 0)

    def test_init_zeros(self):
        # Registers
        for reg in self.core.regs:
            np.testing.assert_array_equal(reg.f32, np.zeros(8, dtype=np.float32))
        # SRAM
        np.testing.assert_array_equal(self.core.sram, np.zeros(48 * 1024, dtype=np.uint8))

    def test_vadd_all_lanes(self):
        # setup [1..8] in rs1 and rs2
        self.core.regs[1].f32 = np.arange(1, 9, dtype=np.float32)
        self.core.regs[2].f32 = np.arange(1, 9, dtype=np.float32)
        self.core.execute_vadd(1, 2, 3)
        # [1,2,3,4,5,6,7,8] + [1,2,3,4,5,6,7,8] = [2,4,6,8,10,12,14,16]
        expected = np.array([2, 4, 6, 8, 10, 12, 14, 16], dtype=np.float32)
        np.testing.assert_array_equal(self.core.regs[3].f32, expected)

    def test_vadd_masked(self):
        # mask = 0b00001111 (lanes 0-3 active)
        self.core.set_mask(0x0F)
        self.core.regs[1].f32 = np.ones(8, dtype=np.float32)
        self.core.regs[2].f32 = np.ones(8, dtype=np.float32)
        self.core.regs[3].f32 = np.zeros(8, dtype=np.float32)

        self.core.execute_vadd(1, 2, 3)

        # Lanes 0-3 should be 2.0, lanes 4-7 should remain 0.0
        expected = np.array([2.0, 2.0, 2.0, 2.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        np.testing.assert_array_equal(self.core.regs[3].f32, expected)

    def test_vfmadd(self):
        # rd = (rs1 * rs2) + rd
        self.core.regs[1].f32 = np.array([1, 2, 3, 4, 5, 6, 7, 8], dtype=np.float32)
        self.core.regs[2].f32 = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], dtype=np.float32)
        self.core.regs[3].f32 = np.array([10, 10, 10, 10, 10, 10, 10, 10], dtype=np.float32)

        self.core.execute_vfmadd(1, 2, 3)

        # (1*0.5)+10 = 10.5, (2*0.5)+10 = 11.0, ...
        expected = np.array([10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0], dtype=np.float32)
        np.testing.assert_array_equal(self.core.regs[3].f32, expected)

    def test_vrelu_positive(self):
        self.core.regs[1].f32 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], dtype=np.float32)
        self.core.execute_vrelu(1, 2)
        np.testing.assert_array_equal(self.core.regs[2].f32, self.core.regs[1].f32)

    def test_vrelu_negative(self):
        self.core.regs[1].f32 = np.array([-1.0, -2.0, 3.0, -4.0, 5.0, -6.0, 7.0, -8.0], dtype=np.float32)
        self.core.execute_vrelu(1, 2)
        expected = np.array([0.0, 0.0, 3.0, 0.0, 5.0, 0.0, 7.0, 0.0], dtype=np.float32)
        np.testing.assert_array_equal(self.core.regs[2].f32, expected)

    def test_sram_roundtrip(self):
        val = 3.14159
        addr = 100
        self.core.write_sram_f32(addr, val)
        read_val = self.core.read_sram_f32(addr)
        self.assertAlmostEqual(val, read_val, places=6)

    def test_sram_out_of_bounds(self):
        with self.assertRaises(MemoryError):
            self.core.read_sram_f32(48 * 1024)
