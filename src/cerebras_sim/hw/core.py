import numpy as np
from enum import IntEnum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Constants from ISA spec
CLK_BASE = 750
CLK_MID = 850
CLK_BOOST = 1200
CLK_MAX = 1400

class Direction(IntEnum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3

@dataclass
class VectorReg:
    """
    SIMD-8 Vector Register.
    Internal storage uses NumPy arrays for performance.
    """
    f32: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.float32))
    i8: np.ndarray = field(default_factory=lambda: np.zeros(8, dtype=np.int8))

class Core:
    """
    Represents a single CS3 Processing Element (PE).
    """
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

        # Architectural State
        self.regs = [VectorReg() for _ in range(32)]
        self.pc = 0
        self.mask = 0xFF  # All 8 lanes active by default

        # 48KB Local SRAM
        self.sram = np.zeros(48 * 1024, dtype=np.uint8)

        # DSD (Data Structure Descriptor)
        self.dsd = {
            'base_addr': 0,
            'stride': 0,
            'limit': 0,
            'current_ptr': 0
        }

        # System State
        self.clock_freq = CLK_BASE
        self.tick_counter = 0
        self.halted = False
        self.smi_status = 0

        # Program memory (loaded from compiler)
        self.program = []

    def set_mask(self, mask_value: int):
        self.mask = mask_value & 0xFF

    def read_sram_f32(self, addr: int) -> float:
        if addr + 4 > len(self.sram):
            raise MemoryError(f"SRAM Out of Bounds at {addr}")
        return np.frombuffer(self.sram[addr:addr+4], dtype=np.float32)[0]

    def write_sram_f32(self, addr: int, val: float):
        if addr + 4 > len(self.sram):
            raise MemoryError(f"SRAM Out of Bounds at {addr}")
        self.sram[addr:addr+4] = np.asarray([val], dtype=np.float32).tobytes()

    def execute_vadd(self, rs1: int, rs2: int, rd: int):
        """Vector Addition: rd = rs1 + rs2 (masked)"""
        # NumPy vectorization handles the 8 lanes efficiently
        res = self.regs[rs1].f32 + self.regs[rs2].f32
        # Apply mask: only update lanes where mask bit is 1
        mask_bits = np.array([(self.mask >> i) & 1 for i in range(8)], dtype=bool)
        self.regs[rd].f32[mask_bits] = res[mask_bits]

    def execute_vmul(self, rs1: int, rs2: int, rd: int):
        """Vector Multiplication: rd = rs1 * rs2 (masked)"""
        res = self.regs[rs1].f32 * self.regs[rs2].f32
        mask_bits = np.array([(self.mask >> i) & 1 for i in range(8)], dtype=bool)
        self.regs[rd].f32[mask_bits] = res[mask_bits]

    def execute_vfmadd(self, rs1: int, rs2: int, rd: int):
        """Vector Fused Multiply-Add: rd = (rs1 * rs2) + rd (masked)"""
        res = (self.regs[rs1].f32 * self.regs[rs2].f32) + self.regs[rd].f32
        mask_bits = np.array([(self.mask >> i) & 1 for i in range(8)], dtype=bool)
        self.regs[rd].f32[mask_bits] = res[mask_bits]

    def execute_vrelu(self, rs1: int, rd: int):
        """Vector ReLU: rd = max(0, rs1) (masked)"""
        res = np.maximum(0.0, self.regs[rs1].f32)
        mask_bits = np.array([(self.mask >> i) & 1 for i in range(8)], dtype=bool)
        self.regs[rd].f32[mask_bits] = res[mask_bits]
