import unittest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.engine.decoder import Instruction, decode_instruction, DecodingError

class TestInstructionDecoder(unittest.TestCase):
    def test_decode_vadd(self):
        # R-type: Opcode=0x01, rd=1, rs1=2, rs2=3, func=0
        # binary: 000001 | 00001 | 00010 | 00011 | 00000
        # 0x04 | 0x20 | 0x60 | 0x00 -> 0x04206000 (conceptual)
        # Using the encoding defined in docs/isa/encoding.md
        # Opcode (6) | Rd (5) | Rs1 (5) | Rs2 (5) | Func (11)
        # 000001 (1) | 00001 (1) | 00010 (2) | 00011 (3) | 00000000000 (0)
        # (1<<26)|(1<<21)|(2<<16)|(3<<11) = 0x04221800
        binary = 0x04221800
        instr = decode_instruction(binary)
        self.assertEqual(instr.opcode, "VADD")
        self.assertEqual(instr.rd, 1)
        self.assertEqual(instr.rs1, 2)
        self.assertEqual(instr.rs2, 3)

    def test_decode_ldr_global(self):
        # G-type: Opcode=0x08, rd=5, imm=0x1234
        # Opcode (6) | Rd (5) | Imm (21)
        # 001000 (8) | 00101 (5) | 00000000000000100100100
        # binary: 00100000101000000000000100100100 -> 0x20A00124
        binary = 0x20A00124
        instr = decode_instruction(binary)
        self.assertEqual(instr.opcode, "LDR_GLOBAL")
        self.assertEqual(instr.rd, 5)
        self.assertEqual(instr.imm, 0x124)

    def test_decode_vmask(self):
        # C-type: Opcode=0x05, imm=0xAA
        # Opcode (6) | Imm (26)
        # 000101 (5) | ... 10101010
        binary = (0x05 << 26) | 0xAA
        instr = decode_instruction(binary)
        self.assertEqual(instr.opcode, "VMASK")
        self.assertEqual(instr.imm, 0xAA)

    def test_invalid_opcode(self):
        # Opcode 0x3F (63) is not defined in our current set
        binary = 0x3F << 26
        with self.assertRaises(DecodingError):
            decode_instruction(binary)

if __name__ == "__main__":
    unittest.main()
