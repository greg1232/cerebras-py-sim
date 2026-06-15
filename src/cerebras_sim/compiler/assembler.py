from typing import List, Tuple
from .ir import TACInstruction, TAC_Op

class Assembler:
    """
    Translates allocated TAC instructions into 32-bit binary integers.
    Refer to docs/isa/encoding.md for bit layouts.
    """
    def __init__(self):
        # Opcode mappings (6-bit)
        self.OPCODES = {
            "COMPUTE": 0x01,
            "CAST": 0x02,
            "MESH": 0x03,
            "MEMORY": 0x04,
            "CONTROL": 0x05,
            "SYSTEM": 0x06,
            "DSD": 0x07,
            "LDR_GLOBAL": 0x08,
            "STR_GLOBAL": 0x09,
        }

        # R-type func codes (COMPUTE group)
        self.COMPUTE_FUNCS = {
            TAC_Op.VADD: 0x00,
            TAC_Op.VSUB: 0x01,
            TAC_Op.VMUL: 0x02,
            TAC_Op.VDIV: 0x03,
            TAC_Op.VFMADD: 0x04,
            TAC_Op.VRELU: 0x09,
        }

    def assemble(self, instructions: List[TACInstruction]) -> List[int]:
        binary = []
        for instr in instructions:
            binary.append(self._pack(instr))
        return binary

    def _pack(self, instr: TACInstruction) -> int:
        # G-Type: Global Load/Store
        if instr.op == TAC_Op.LOAD_GLOBAL:
            # [31:26] opcode | [25:21] rd | [20:0] imm21
            return (self.OPCODES["LDR_GLOBAL"] << 26) | (instr.dest << 21) | (instr.imm & 0x1FFFFF)

        if instr.op == TAC_Op.STORE_GLOBAL:
            # [31:26] opcode | [25:21] rd (src) | [20:0] imm21
            return (self.OPCODES["STR_GLOBAL"] << 26) | (instr.src1 << 21) | (instr.imm & 0x1FFFFF)

        # R-Type: Compute
        if instr.op in self.COMPUTE_FUNCS:
            # [31:26] opcode | [25:21] rd | [20:16] rs1 | [15:11] rs2 | [10:0] func
            func = self.COMPUTE_FUNCS[instr.op]
            return (self.OPCODES["COMPUTE"] << 26) | (instr.dest << 21) | (instr.src1 << 16) | (instr.src2 << 11) | func

        # S-Type: System (e.g. GET_ID)
        if instr.op == TAC_Op.GET_ID:
            # [31:26] opcode | [25:21] rd | [20:0] imm21
            return (self.OPCODES["SYSTEM"] << 26) | (instr.dest << 21) | (instr.imm & 0x1FFFFF)

        # C-Type: Control
        if instr.op == TAC_Op.SYNC:
            # [31:26] opcode | [25:0] imm26 (SYNC func=0x03)
            # Note: In the ISA, SYNC is often a specific func of the CONTROL group
            return (self.OPCODES["CONTROL"] << 26) | (0x03 << 21) # Simplified as rd=func

        raise NotImplementedError(f"Assembler does not yet support operation: {instr.op}")
