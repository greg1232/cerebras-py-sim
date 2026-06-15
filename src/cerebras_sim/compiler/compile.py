import ast
import inspect
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List
from .ir import TACInstruction, TAC_Op
from .ast_parser import ASTParser
from .register_allocator import RegisterAllocator
from .assembler import Assembler


@dataclass
class CompiledKernel:
    """
    Output of compile_kernel().
    binary   — list of 32-bit ISA words for BSPScheduler.execute_kernel()
    constants — {physical_reg: float_value} for registers pre-loaded with literals
    """
    binary: List[int]
    constants: Dict[int, float] = field(default_factory=dict)


def compile_kernel(func) -> CompiledKernel:
    """
    Full pipeline: Python function → TAC → register allocation → ISA binary.
    Constants (numeric literals) are extracted and returned in CompiledKernel.constants
    so the scheduler can pre-populate core registers before execution.
    """
    # 1. Parse source → AST → FunctionDef
    source = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source)
    func_def = next(
        (n for n in ast.walk(tree)
         if isinstance(n, ast.FunctionDef) and n.name == func.__name__),
        None,
    )
    if func_def is None:
        raise ValueError(f"Could not find function definition for '{func.__name__}'")

    # 2. AST → TAC
    parser = ASTParser()
    tac = parser.parse(func_def)

    # 3. TAC → allocated TAC (virtual regs → physical regs)
    allocator = RegisterAllocator()
    allocated = _allocate(tac, allocator)

    # 4. Allocated TAC → binary
    asm = Assembler()
    binary = asm.assemble(allocated)

    # 5. Extract scalar constants so the scheduler can pre-load them into registers.
    #    The parser records numeric literals as symbols named "__const_<value>".
    constants: Dict[int, float] = {}
    for sym_name, v_reg in parser.symbols.items():
        if sym_name.startswith("__const_"):
            raw = sym_name[len("__const_"):]
            try:
                val = float(raw)
            except ValueError:
                continue
            if v_reg in allocator.mapping:
                constants[allocator.mapping[v_reg]] = val

    return CompiledKernel(binary=binary, constants=constants)


def _allocate(tac: List[TACInstruction], allocator: RegisterAllocator) -> List[TACInstruction]:
    """Rewrite virtual register IDs to physical register IDs."""
    allocated = []
    for instr in tac:
        dest = allocator.allocate(instr.dest) if instr.dest is not None else None
        src1 = allocator.allocate(instr.src1) if isinstance(instr.src1, int) else instr.src1
        src2 = allocator.allocate(instr.src2) if isinstance(instr.src2, int) else instr.src2
        allocated.append(TACInstruction(
            op=instr.op, dest=dest, src1=src1, src2=src2,
            imm=instr.imm, meta=instr.meta,
        ))
    return allocated
