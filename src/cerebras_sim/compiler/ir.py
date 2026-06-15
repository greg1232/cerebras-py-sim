from dataclasses import dataclass
from enum import auto, Enum
from typing import Any, Optional

class TAC_Op(Enum):
    # Memory
    LOAD_GLOBAL = auto()
    STORE_GLOBAL = auto()
    SRAM_ALLOC = auto()
    SRAM_LOAD = auto()
    SRAM_STORE = auto()
    # Compute
    VADD = auto()
    VSUB = auto()
    VMUL = auto()
    VDIV = auto()
    VFMADD = auto()
    VRELU = auto()
    # Mesh
    MESH_SHIFT = auto()
    MESH_READ = auto()
    # System
    GET_ID = auto()
    # Control
    SYNC = auto()

@dataclass
class TACInstruction:
    op: TAC_Op
    dest: Optional[int] = None
    src1: Optional[Any] = None
    src2: Optional[Any] = None
    imm: Optional[Any] = None
    meta: Optional[dict] = None

    def __repr__(self):
        return f"{self.op.name} {self.dest if self.dest is not None else ''} {self.src1 if self.src1 is not None else ''} {self.src2 if self.src2 is not None else ''} {self.imm if self.imm is not None else ''}"
