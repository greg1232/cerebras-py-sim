import ast
from typing import List
from .ir import TACInstruction, TAC_Op


def _const_val(node: ast.expr):
    """Extract a raw Python scalar from a Constant AST node (returns 0 for None)."""
    if isinstance(node, ast.Constant):
        return node.value if node.value is not None else 0
    return 0


class ASTParser:
    """
    Traverses a Python function's AST and emits a linear TAC instruction sequence.
    Supports the CS3 DSL: load_global, store_global, pe_x, pe_y, +, -, *, /.
    """

    def __init__(self):
        self.tac_list: List[TACInstruction] = []
        self.virtual_reg_count = 0
        self.symbols: dict = {}  # variable name → virtual reg

    def _new_reg(self) -> int:
        self.virtual_reg_count += 1
        return self.virtual_reg_count

    def parse(self, func_def: ast.FunctionDef) -> List[TACInstruction]:
        self.tac_list = []
        self.virtual_reg_count = 0
        self.symbols = {}

        for stmt in func_def.body:
            self._visit_stmt(stmt)

        return self.tac_list

    # ── statements ─────────────────────────────────────────────────────────────

    def _visit_stmt(self, stmt: ast.stmt):
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    reg = self._visit_expr(stmt.value)
                    self.symbols[target.id] = reg
        elif isinstance(stmt, ast.Expr):
            # Bare expression statement — usually a store_global / sync call
            self._visit_expr(stmt.value)

    # ── expressions ────────────────────────────────────────────────────────────

    def _visit_expr(self, expr: ast.expr) -> int:
        # Binary arithmetic
        if isinstance(expr, ast.BinOp):
            op_map = {
                ast.Add: TAC_Op.VADD,
                ast.Sub: TAC_Op.VSUB,
                ast.Mult: TAC_Op.VMUL,
                ast.Div: TAC_Op.VDIV,
            }
            tac_op = op_map.get(type(expr.op))
            if tac_op is None:
                raise NotImplementedError(f"Binary operator {type(expr.op)} not supported")
            left = self._visit_expr(expr.left)
            right = self._visit_expr(expr.right)
            dest = self._new_reg()
            self.tac_list.append(TACInstruction(tac_op, dest=dest, src1=left, src2=right))
            return dest

        # Function / method calls
        if isinstance(expr, ast.Call):
            # Support both ctx.method() and standalone method()
            if isinstance(expr.func, ast.Attribute):
                func_name = expr.func.attr
            elif isinstance(expr.func, ast.Name):
                func_name = expr.func.id
            else:
                raise NotImplementedError(f"Unsupported call target: {ast.dump(expr.func)}")

            return self._visit_call(func_name, expr.args)

        # Variable reference
        if isinstance(expr, ast.Name):
            if expr.id in self.symbols:
                return self.symbols[expr.id]
            # Unknown name — allocate a fresh register (caller must populate)
            reg = self._new_reg()
            self.symbols[expr.id] = reg
            return reg

        # Numeric literal — allocate a register; host pre-loads the constant
        if isinstance(expr, ast.Constant):
            key = f"__const_{expr.value}"
            if key in self.symbols:
                return self.symbols[key]
            reg = self._new_reg()
            self.symbols[key] = reg
            return reg

        # Unary minus  (-x → VSUB 0, x)
        if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
            zero = self._ensure_zero_reg()
            operand = self._visit_expr(expr.operand)
            dest = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.VSUB, dest=dest, src1=zero, src2=operand))
            return dest

        raise NotImplementedError(f"Expression type {type(expr).__name__} not supported: {ast.dump(expr)}")

    # ── DSL call dispatch ──────────────────────────────────────────────────────

    def _visit_call(self, func_name: str, args: list) -> int:
        if func_name == "load_global":
            # load_global(ptr, byte_offset) → LDR_GLOBAL rd, imm
            dest = self._new_reg()
            offset = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.LOAD_GLOBAL, dest=dest, imm=offset))
            return dest

        if func_name == "store_global":
            # store_global(ptr, byte_offset, val) → STR_GLOBAL src1=val, imm=offset
            offset = _const_val(args[1]) if len(args) > 1 else 0
            val_reg = self._visit_expr(args[2]) if len(args) > 2 else 0
            self.tac_list.append(TACInstruction(TAC_Op.STORE_GLOBAL, src1=val_reg, imm=offset))
            return 0  # void

        if func_name == "sram_alloc":
            # sram_alloc(name, size) → SRAM_ALLOC rd, imm=size
            dest = self._new_reg()
            size = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.SRAM_ALLOC, dest=dest, imm=size))
            return dest

        if func_name == "sram_load":
            # sram_load(handle, offset) → SRAM_LOAD rd, src1=handle, imm=offset
            dest = self._new_reg()
            handle = self._visit_expr(args[0])
            offset = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.SRAM_LOAD, dest=dest, src1=handle, imm=offset))
            return dest

        if func_name == "sram_store":
            # sram_store(handle, offset, val) → SRAM_STORE src1=handle, src2=val, imm=offset
            handle = self._visit_expr(args[0])
            val_reg = self._visit_expr(args[2]) if len(args) > 2 else 0
            offset = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.SRAM_STORE, src1=handle, src2=val_reg, imm=offset))
            return 0

        if func_name == "sram_load_2d":
            # sram_load_2d(handle, x, y) → SRAM_LOAD rd, src1=handle, imm=offset(calc)
            # Since we can't easily emit a complex offset in one TAC, we emit
            # a sequence: x_reg, y_reg, offset_reg = y * width + x
            dest = self._new_reg()
            handle = self._visit_expr(args[0])
            x_reg = self._visit_expr(args[1])
            y_reg = self._visit_expr(args[2])

            # Width is assumed 16 for now as a constant
            width_reg = self._new_reg()
            self.symbols["__width_16"] = width_reg # Simplified: just use a constant register

            # Linear offset calculation: y * 16 + x
            prod_reg = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.VMUL, dest=prod_reg, src1=y_reg, src2=width_reg))
            offset_reg = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.VADD, dest=offset_reg, src1=prod_reg, src2=x_reg))

            # Now perform the load using the calculated offset register
            # Note: our TACInstruction.imm is Optional[Any], but SRAM_LOAD usually expects a constant.
            # In a real compiler, we'd have a register-based offset load.
            # For the simulator's sake, we'll just use the offset_reg as src2.
            self.tac_list.append(TACInstruction(TAC_Op.SRAM_LOAD, dest=dest, src1=handle, src2=offset_reg))
            return dest

        if func_name == "sram_store_2d":
            # sram_store_2d(handle, x, y, val)
            handle = self._visit_expr(args[0])
            x_reg = self._visit_expr(args[1])
            y_reg = self._visit_expr(args[2])
            val_reg = self._visit_expr(args[3])

            width_reg = self._new_reg()
            prod_reg = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.VMUL, dest=prod_reg, src1=y_reg, src2=width_reg))
            offset_reg = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.VADD, dest=offset_reg, src1=prod_reg, src2=x_reg))

            self.tac_list.append(TACInstruction(TAC_Op.SRAM_STORE, src1=handle, src2=val_reg, imm=offset_reg))
            return 0

        if func_name == "shift_right":
            # shift_right(handle, offset) → MESH_SHIFT rd, src1=handle, imm=offset
            dest = self._new_reg()
            handle = self._visit_expr(args[0])
            offset = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.MESH_SHIFT, dest=dest, src1=handle, imm=offset))
            return dest

        if func_name == "shift_down":
            # shift_down(handle, offset) → MESH_SHIFT rd, src1=handle, imm=offset (encoded in ISA)
            dest = self._new_reg()
            handle = self._visit_expr(args[0])
            offset = _const_val(args[1]) if len(args) > 1 else 0
            self.tac_list.append(TACInstruction(TAC_Op.MESH_SHIFT, dest=dest, src1=handle, imm=offset))
            return dest

        if func_name == "neighbor_load":
            # neighbor_load(handle, dir, offset) → MESH_READ rd, src1=handle, imm=offset
            dest = self._new_reg()
            handle = self._visit_expr(args[0])
            # Direction is handled as meta or a specialized immediate in the compiler
            offset = _const_val(args[2]) if len(args) > 2 else 0
            self.tac_list.append(TACInstruction(TAC_Op.MESH_READ, dest=dest, src1=handle, imm=offset))
            return dest

        if func_name == "pe_x":
            dest = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.GET_ID, dest=dest, imm=0))
            return dest

        if func_name == "pe_y":
            dest = self._new_reg()
            self.tac_list.append(TACInstruction(TAC_Op.GET_ID, dest=dest, imm=1))
            return dest

        if func_name == "sync":
            self.tac_list.append(TACInstruction(TAC_Op.SYNC))
            return 0

        raise NotImplementedError(f"DSL call '{func_name}' not supported")

    def _ensure_zero_reg(self) -> int:
        key = "__const_0"
        if key not in self.symbols:
            reg = self._new_reg()
            self.symbols[key] = reg
        return self.symbols[key]
