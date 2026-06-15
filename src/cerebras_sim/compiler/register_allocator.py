from typing import List, Tuple
from .ir import TACInstruction, TAC_Op

class RegisterAllocator:
    """
    A simple linear scan register allocator.
    Maps virtual TAC registers to physical vector registers (v0-v31).
    """
    def __init__(self):
        self.next_reg = 0
        self.mapping = {}

    def allocate(self, virtual_reg: int) -> int:
        if virtual_reg in self.mapping:
            return self.mapping[virtual_reg]

        if self.next_reg >= 32:
            raise RuntimeError("Out of physical registers! Spill to SRAM not yet implemented.")

        reg = self.next_reg
        self.mapping[virtual_reg] = reg
        self.next_reg += 1
        return reg

    def reset(self):
        self.next_reg = 0
        self.mapping = {}
