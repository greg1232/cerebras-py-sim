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
