import unittest
import sys
import os
import numpy as np

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.hw.core import Core, VectorReg
from cerebras_sim.engine.decoder import decode_instruction

class TestCoreExecution(unittest.TestCase):
    def setUp(self):
        self.core = Core(0, 0)

    def test_execute_vadd_flow(self):
        # Setup: Reg 1 = [1,1...], Reg 2 = [2,2...], Mask = 0xFF
        self.core.regs[1].f32[:] = 1.0
        self.core.regs[2].f32[:] = 2.0
        self.core.set_mask(0xFF)

        # Binary for VADD rd=3, rs1=1, rs2=2, func=0
        # Opcode=1 (COMPUTE) | rd=3 | rs1=1 | rs2=2 | func=0
        # (1<<26) | (3<<21) | (1<<16) | (2<<11) | 0 = 0x04611000
        binary = 0x04611000
        instr = decode_instruction(binary)

        self.core.execute(instr)

        # Result should be 3.0 in all 8 lanes of Reg 3
        np.testing.assert_array_almost_equal(self.core.regs[instr.rd].f32, np.full(8, 3.0))

    def test_execute_vadd_masked(self):
        self.core.regs[1].f32[:] = 1.0
        self.core.regs[2].f32[:] = 2.0
        self.core.set_mask(0b00000001) # Only lane 0 active

        # Same binary: rd=3, rs1=1, rs2=2
        binary = 0x04611000
        instr = decode_instruction(binary)

        self.core.execute(instr)

        # Lane 0 should be 3.0, others should remain 0.0
        self.assertEqual(self.core.regs[instr.rd].f32[0], 3.0)
        self.assertEqual(self.core.regs[instr.rd].f32[1], 0.0)




    def test_execute_vrelu_flow(self):
        # Setup: Reg 1 = [-1, 1, -2, 2, ...]
        self.core.regs[1].f32[:] = np.array([-1.0, 1.0, -2.0, 2.0, -3.0, 3.0, -4.0, 4.0], dtype=np.float32)
        self.core.mask = 0xFF

        # VRELU rd=3, rs1=1, func=0x09 (binary computed based on R-type)
        # Opcode=0x01 | rd=3 | rs1=1 | rs2=0 | func=0x09
        # binary: 000001 | 00011 | 00001 | 00000 | 00000001001 -> 0x0461009
        binary = (0x01 << 26) | (3 << 21) | (1 << 16) | 0x09
        instr = decode_instruction(binary)

        self.core.execute(instr)

        expected = np.array([0.0, 1.0, 0.0, 2.0, 0.0, 3.0, 0.0, 4.0], dtype=np.float32)
        np.testing.assert_array_almost_equal(self.core.regs[3].f32, expected)

if __name__ == "__main__":
    unittest.main()
