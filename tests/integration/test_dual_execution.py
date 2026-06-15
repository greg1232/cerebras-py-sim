"""
Dual-execution test: compile Python DSL kernel → ISA binary, run both paths,
compare outputs against each other as a golden reference.

Binary path: compile_kernel → BSPScheduler.execute_kernel (Core instruction dispatch)
Python path: BSPScheduler.execute_kernel_fn (KernelContext DSL)
"""
import unittest
import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.compiler.compile import compile_kernel
from cerebras_sim.compiler.kernel import cs3_kernel
from cerebras_sim.engine.scheduler import BSPScheduler
from cerebras_sim.hw.memory import WeightServer


# ── Kernels under test ────────────────────────────────────────────────────────
# Written with None as ptr: the binary path uses a scheduler-level base_ptr
# while the Python path uses the real DevicePtr in a closure.

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


def _make_golden_add(base_ptr):
    @cs3_kernel(block_w=1, block_h=1)
    def golden(ctx):
        x = ctx.load_global(base_ptr, 0)
        y = ctx.load_global(base_ptr, 4)
        z = x + y
        ctx.store_global(base_ptr, 8, z)
    return golden


def _make_golden_saxpy(base_ptr):
    @cs3_kernel(block_w=1, block_h=1)
    def golden(ctx):
        x = ctx.load_global(base_ptr, 0)
        y = ctx.load_global(base_ptr, 4)
        z = 2.0 * x + y
        ctx.store_global(base_ptr, 8, z)
    return golden


class TestDualExecutionAdd(unittest.TestCase):
    """Verifies compiled binary produces the same result as the Python golden path."""

    def setUp(self):
        self.X = 3.0
        self.Y = 7.0

    def _run_binary(self, kernel_fn):
        ws = WeightServer()
        base = ws.malloc(3 * 4)
        ws.store(base, 0, self.X)
        ws.store(base, 4, self.Y)

        compiled = compile_kernel(kernel_fn)
        sched = BSPScheduler(block_w=1, block_h=1, sampling_rate=1.0,
                             mesh_width=1, mesh_height=1)
        sched.execute_kernel(compiled.binary, steps=1, weight_server=ws, base_ptr=base, constants=compiled.constants)
        return ws.load(base, 8)

    def _run_python(self, make_golden):
        ws = WeightServer()
        base = ws.malloc(3 * 4)
        ws.store(base, 0, self.X)
        ws.store(base, 4, self.Y)

        golden = make_golden(base)
        sched = BSPScheduler(block_w=1, block_h=1, sampling_rate=1.0,
                             mesh_width=1, mesh_height=1)
        sched.execute_kernel_fn(golden, ws, steps=1)
        return ws.load(base, 8)

    def test_add_binary_correctness(self):
        """Binary path: 3.0 + 7.0 = 10.0"""
        result = self._run_binary(simple_add)
        self.assertAlmostEqual(result, self.X + self.Y, places=5)

    def test_add_dual_paths_agree(self):
        """Binary path and Python path produce the same result."""
        binary_result = self._run_binary(simple_add)
        python_result = self._run_python(_make_golden_add)
        self.assertAlmostEqual(binary_result, python_result, places=5)

    def test_saxpy_binary_correctness(self):
        """Binary path: 2.0 * 3.0 + 7.0 = 13.0"""
        result = self._run_binary(simple_saxpy)
        self.assertAlmostEqual(result, 2.0 * self.X + self.Y, places=5)

    def test_saxpy_dual_paths_agree(self):
        """Compiled SAXPY binary matches Python golden reference."""
        binary_result = self._run_binary(simple_saxpy)
        python_result = self._run_python(_make_golden_saxpy)
        self.assertAlmostEqual(binary_result, python_result, places=5)

    def test_binary_perf_tracked(self):
        """LDR_GLOBAL (100 cy) dominates; total_cycles == 100 after one superstep."""
        ws = WeightServer()
        base = ws.malloc(3 * 4)
        ws.store(base, 0, self.X)
        ws.store(base, 4, self.Y)

        compiled = compile_kernel(simple_add)
        sched = BSPScheduler(block_w=1, block_h=1, sampling_rate=1.0,
                             mesh_width=1, mesh_height=1)
        sched.execute_kernel(compiled.binary, steps=1, weight_server=ws, base_ptr=base, constants=compiled.constants)
        self.assertEqual(sched.perf.total_cycles, 100)


if __name__ == '__main__':
    unittest.main()
