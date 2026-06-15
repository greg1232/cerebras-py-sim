import ast
import inspect
from typing import List
from .ir import TACInstruction, TAC_Op
from .ast_parser import ASTParser
from .register_allocator import RegisterAllocator
from .assembler import Assembler


def compile_kernel(func) -> List[int]:
    """
    Full pipeline: Python function → TAC → allocated TAC → binary.
    Returns a list of 32-bit integers ready for BSPScheduler.execute_kernel().
    """
    # 1. Get the function's AST
    source = inspect.getsource(func)
    # dedent handles methods indented inside a class/decorator
    source = _dedent(source)
    tree = ast.parse(source)

    # Find the FunctionDef node (skip the decorator)
    func_def = None
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func.__name__:
            func_def = node
            break
    if func_def is None:
        raise ValueError(f"Could not find function definition for '{func.__name__}'")

    # 2. Parse AST → TAC
    parser = ASTParser()
    tac = parser.parse(func_def)

    # 3. Allocate registers: replace virtual regs with physical regs
    allocator = RegisterAllocator()
    allocated = _allocate(tac, allocator)

    # 4. Assemble → binary
    asm = Assembler()
    return asm.assemble(allocated)


def _dedent(source: str) -> str:
    """Strip common leading whitespace so ast.parse doesn't fail."""
    import textwrap
    return textwrap.dedent(source)


def _allocate(tac: List[TACInstruction], allocator: RegisterAllocator) -> List[TACInstruction]:
    """Rewrite virtual register IDs to physical register IDs in-place."""
    allocated = []
    for instr in tac:
        dest = allocator.allocate(instr.dest) if instr.dest is not None else None
        src1 = allocator.allocate(instr.src1) if isinstance(instr.src1, int) else instr.src1
        src2 = allocator.allocate(instr.src2) if isinstance(instr.src2, int) else instr.src2
        allocated.append(TACInstruction(
            op=instr.op,
            dest=dest,
            src1=src1,
            src2=src2,
            imm=instr.imm,
            meta=instr.meta,
        ))
    return allocated
