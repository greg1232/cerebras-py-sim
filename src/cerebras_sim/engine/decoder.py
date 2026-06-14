from dataclasses import dataclass, field
from typing import Optional

# Opcode table from docs/isa/encoding.md
# Major opcodes (6-bit)
OPCODES = {
    # R-type: Compute SIMD (opcode=0x01, distinguished by func)
    0x01: "COMPUTE",
    # Cast (opcode=0x02, distinguished by func)
    0x02: "CAST",
    # M-type: Mesh internal (opcode=0x03, distinguished by func)
    0x03: "MESH",
    # I-type: Memory SRAM (opcode=0x04)
    0x04: "MEMORY",
    # C-type: Control (opcode=0x05)
    0x05: "CONTROL",
    # S-type: System (opcode=0x06)
    0x06: "SYSTEM",
    # D-type: DSD (opcode=0x07)
    0x07: "DSD",
    # G-type: Global Memory (opcode=0x08 = LDR_GLOBAL, 0x09 = STR_GLOBAL)
    0x08: "LDR_GLOBAL",
    0x09: "STR_GLOBAL",
}

# R-type func codes for COMPUTE group (opcode=0x01)
COMPUTE_FUNCS = {
    0x00: "VADD",
    0x01: "VSUB",
    0x02: "VMUL",
    0x03: "VDIV",
    0x04: "VFMADD",
    0x05: "VABS",
    0x06: "VMAX",
    0x07: "VMIN",
    0x08: "VNEG",
    0x09: "VRELU",
    0x0A: "VGELU",
    0x0B: "VSIGMOID",
    0x0C: "VTANH",
    0x0D: "VEXP",
    0x0E: "VLOG",
    0x0F: "VSQRT",
}

# R-type func codes for CAST group (opcode=0x02)
CAST_FUNCS = {
    0x00: "VCAST_F16_F32",
    0x01: "VCAST_F32_F16",
    0x02: "VCAST_I8_F16",
    0x03: "VCAST_F16_I8",
    0x04: "VCLIP",
}

# I-type func codes for MEMORY group (opcode=0x04)
MEMORY_FUNCS = {
    0x00: "LDR",
    0x01: "STR",
    0x02: "LDR_INC",
    0x03: "STR_INC",
}

# D-type func codes for DSD group (opcode=0x07)
DSD_FUNCS = {
    0x00: "SET_DSD",
    0x01: "LDR_DSD",
    0x02: "STR_DSD",
    0x03: "NEXT_DSD",
}

# C-type func codes for CONTROL group (opcode=0x05)
CONTROL_FUNCS = {
    0x00: "VMASK",
    0x01: "B_COND",
    0x02: "B_JMP",
    0x03: "SYNC",
    0x04: "HALT",
}

# S-type func codes for SYSTEM group (opcode=0x06)
SYSTEM_FUNCS = {
    0x00: "SET_CLK",
    0x01: "GET_TICK",
    0x02: "SET_ID",
    0x03: "SMI_READ",
}

# Internal Mesh funcs (opcode=0x03) — not user-accessible
MESH_FUNCS = {
    0x00: "SEND_N", 0x01: "SEND_S", 0x02: "SEND_E", 0x03: "SEND_W",
    0x04: "RECV_N", 0x05: "RECV_S", 0x06: "RECV_E", 0x07: "RECV_W",
    0x08: "WAIT_N", 0x09: "WAIT_S", 0x0A: "WAIT_E", 0x0B: "WAIT_W",
    0x0C: "POLL_MESH",
}


class DecodingError(Exception):
    pass


@dataclass
class Instruction:
    opcode: str
    rd: int = 0
    rs1: int = 0
    rs2: int = 0
    imm: int = 0
    func: int = 0


def decode_instruction(binary: int) -> Instruction:
    """
    Decode a 32-bit instruction word into an Instruction.

    Bit layouts (from docs/isa/encoding.md):
      R-type: [31:26] opcode | [25:21] rd | [20:16] rs1 | [15:11] rs2 | [10:0] func
      I-type: [31:26] opcode | [25:21] rd | [20:5] imm16 | [4:0] func
      G-type: [31:26] opcode | [25:21] rd | [20:0] imm21
      C-type: [31:26] opcode | [25:0] imm26
      S-type: [31:26] opcode | [25:21] rd | [20:0] imm21
    """
    opcode_bits = (binary >> 26) & 0x3F
    group = OPCODES.get(opcode_bits)

    if group is None:
        raise DecodingError(f"Unknown opcode: 0x{opcode_bits:02X} in instruction 0x{binary:08X}")

    # G-type: LDR_GLOBAL / STR_GLOBAL
    if group in ("LDR_GLOBAL", "STR_GLOBAL"):
        rd  = (binary >> 21) & 0x1F
        imm = binary & 0x1FFFFF
        return Instruction(opcode=group, rd=rd, imm=imm)

    # Extract common fields
    rd   = (binary >> 21) & 0x1F
    rs1  = (binary >> 16) & 0x1F
    rs2  = (binary >> 11) & 0x1F
    func = binary & 0x7FF

    if group == "COMPUTE":
        opcode = COMPUTE_FUNCS.get(func)
        if opcode is None:
            raise DecodingError(f"Unknown COMPUTE func: 0x{func:03X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, rs2=rs2, func=func)

    if group == "CAST":
        opcode = CAST_FUNCS.get(func)
        if opcode is None:
            raise DecodingError(f"Unknown CAST func: 0x{func:03X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, rs2=rs2, func=func)

    if group == "MESH":
        opcode = MESH_FUNCS.get(func)
        if opcode is None:
            raise DecodingError(f"Unknown MESH func: 0x{func:03X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, func=func)

    if group == "MEMORY":
        imm = (binary >> 5) & 0xFFFF
        func4 = binary & 0xF
        opcode = MEMORY_FUNCS.get(func4)
        if opcode is None:
            raise DecodingError(f"Unknown MEMORY func: 0x{func4:02X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, imm=imm, func=func4)

    if group == "DSD":
        func4 = binary & 0xF
        opcode = DSD_FUNCS.get(func4)
        if opcode is None:
            raise DecodingError(f"Unknown DSD func: 0x{func4:02X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, func=func4)

    if group == "CONTROL":
        imm  = binary & 0x3FFFFFF
        func4 = (binary >> 21) & 0x1F  # reuse rd field as func for C-type
        opcode = CONTROL_FUNCS.get(func4)
        if opcode is None:
            raise DecodingError(f"Unknown CONTROL func: 0x{func4:02X}")
        return Instruction(opcode=opcode, rd=rd, rs1=rs1, imm=binary & 0x3FFFFF, func=func4)

    if group == "SYSTEM":
        imm  = binary & 0x1FFFFF
        func4 = binary & 0xF
        opcode = SYSTEM_FUNCS.get(func4)
        if opcode is None:
            raise DecodingError(f"Unknown SYSTEM func: 0x{func4:02X}")
        return Instruction(opcode=opcode, rd=rd, imm=imm, func=func4)

    raise DecodingError(f"Unhandled group: {group}")
