"""
Tests for the full compile pipeline: Python DSL → TAC → binary.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.compiler.compile import compile_kernel
from cerebras_sim.compiler.ir import TAC_Op
from cerebras_sim.compiler.ast_parser import ASTParser
from cerebras_sim.compiler.assembler import Assembler
from cerebras_sim.engine.decoder import decode_instruction


def simple_add(ctx):
    x = ctx.load_global(None, 0)
    y = ctx.load_global(None, 4)
    z = x + y
    ctx.store_global(None, 8, z)


def simple_saxpy(ctx):
    x = ctx.load_global(None, 0)
    y = ctx.load_global(None, 4)
    z = 2.0 * x + y
    ctx.store_global(None, 8, z)


class TestAssembler(unittest.TestCase):
    """Verifies the assembler packs bits correctly per the ISA encoding spec."""

    def test_ldr_global_encoding(self):
        from cerebras_sim.compiler.ir import TACInstruction
        asm = Assembler()
        instr = TACInstruction(TAC_Op.LOAD_GLOBAL, dest=3, imm=0)
        binary = asm._pack(instr)
        decoded = decode_instruction(binary)
        self.assertEqual(decoded.opcode, "LDR_GLOBAL")
        self.assertEqual(decoded.rd, 3)

    def test_str_global_encoding(self):
        from cerebras_sim.compiler.ir import TACInstruction
        asm = Assembler()
        instr = TACInstruction(TAC_Op.STORE_GLOBAL, src1=5, imm=8)
        binary = asm._pack(instr)
        decoded = decode_instruction(binary)
        self.assertEqual(decoded.opcode, "STR_GLOBAL")
        self.assertEqual(decoded.rd, 5)  # STR_GLOBAL uses rd field for src

    def test_vadd_encoding(self):
        from cerebras_sim.compiler.ir import TACInstruction
        asm = Assembler()
        instr = TACInstruction(TAC_Op.VADD, dest=3, src1=1, src2=2)
        binary = asm._pack(instr)
        decoded = decode_instruction(binary)
        self.assertEqual(decoded.opcode, "VADD")
        self.assertEqual(decoded.rd, 3)
        self.assertEqual(decoded.rs1, 1)
        self.assertEqual(decoded.rs2, 2)

    def test_vmul_encoding(self):
        from cerebras_sim.compiler.ir import TACInstruction
        asm = Assembler()
        instr = TACInstruction(TAC_Op.VMUL, dest=4, src1=1, src2=2)
        binary = asm._pack(instr)
        decoded = decode_instruction(binary)
        self.assertEqual(decoded.opcode, "VMUL")
        self.assertEqual(decoded.rd, 4)


class TestASTParser(unittest.TestCase):
    """Verifies the AST parser emits the correct TAC sequence."""

    def _parse(self, func):
        import ast, inspect, textwrap
        source = textwrap.dedent(inspect.getsource(func))
        tree = ast.parse(source)
        func_def = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        parser = ASTParser()
        return parser.parse(func_def)

    def test_simple_add_tac(self):
        tac = self._parse(simple_add)
        ops = [t.op for t in tac]
        self.assertIn(TAC_Op.LOAD_GLOBAL, ops)
        self.assertIn(TAC_Op.VADD, ops)
        self.assertIn(TAC_Op.STORE_GLOBAL, ops)

    def test_saxpy_tac_order(self):
        tac = self._parse(simple_saxpy)
        ops = [t.op for t in tac]
        # Expect: load_global(x), load_global(y), const (2.0), mul, add, store_global
        self.assertEqual(ops.count(TAC_Op.LOAD_GLOBAL), 2)
        self.assertIn(TAC_Op.VMUL, ops)
        self.assertIn(TAC_Op.VADD, ops)
        self.assertIn(TAC_Op.STORE_GLOBAL, ops)


class TestCompilePipeline(unittest.TestCase):
    """Verifies the compile() function produces a decodeable binary sequence."""

    def test_simple_add_compiles_to_binary(self):
        binary = compile_kernel(simple_add)
        self.assertIsInstance(binary, list)
        self.assertGreater(len(binary), 0)
        # Every word must be decodeable
        for word in binary:
            instr = decode_instruction(word)
            self.assertIsNotNone(instr.opcode)

    def test_saxpy_compiles_to_binary(self):
        binary = compile_kernel(simple_saxpy)
        ops = [decode_instruction(w).opcode for w in binary]
        self.assertIn("LDR_GLOBAL", ops)
        self.assertIn("VMUL", ops)
        self.assertIn("VADD", ops)
        self.assertIn("STR_GLOBAL", ops)

    def test_binary_register_sequence(self):
        """Registers must be allocated linearly: r0, r1, r2 … for simple_add."""
        binary = compile_kernel(simple_add)
        instrs = [decode_instruction(w) for w in binary]

        ldr_instrs = [i for i in instrs if i.opcode == "LDR_GLOBAL"]
        add_instr = next(i for i in instrs if i.opcode == "VADD")
        str_instr = next(i for i in instrs if i.opcode == "STR_GLOBAL")

        # r0 ← load x,  r1 ← load y,  r2 = r0+r1,  store r2
        self.assertEqual(ldr_instrs[0].rd, 0)
        self.assertEqual(ldr_instrs[1].rd, 1)
        self.assertEqual(add_instr.rs1, 0)
        self.assertEqual(add_instr.rs2, 1)
        self.assertEqual(add_instr.rd, 2)
        self.assertEqual(str_instr.rd, 2)


if __name__ == '__main__':
    unittest.main()
