"""
End-to-end SAXPY test: Z = alpha * X + Y

Grid: 4x1 PEs, block 4x1, sampling_rate=1.0 (all PEs verified).
Each PE owns one element: PE at x=i handles index i.
"""
import unittest
import sys
import os

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.compiler.kernel import cs3_kernel
from cerebras_sim.engine.scheduler import BSPScheduler
from cerebras_sim.hw.memory import WeightServer


N = 4
ALPHA = 2.0


def _build_saxpy_kernel(ptr_X, ptr_Y, ptr_Z, alpha):
    @cs3_kernel(block_w=N, block_h=1)
    def saxpy(ctx):
        idx = ctx.pe_x()
        x_val = ctx.load_global(ptr_X, idx * 4)
        y_val = ctx.load_global(ptr_Y, idx * 4)
        z_val = alpha * x_val + y_val
        ctx.store_global(ptr_Z, idx * 4, z_val)
    return saxpy


class TestSAXPYEndToEnd(unittest.TestCase):
    def setUp(self):
        self.ws = WeightServer()
        self.X = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        self.Y = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32)

        self.ptr_X = self.ws.malloc(N * 4)
        self.ptr_Y = self.ws.malloc(N * 4)
        self.ptr_Z = self.ws.malloc(N * 4)

        self.ws.memcpy_h2d(self.ptr_X, self.X)
        self.ws.memcpy_h2d(self.ptr_Y, self.Y)

    def test_saxpy_correctness(self):
        """All 4 PEs sampled: result must equal alpha*X + Y."""
        kernel = _build_saxpy_kernel(self.ptr_X, self.ptr_Y, self.ptr_Z, ALPHA)

        scheduler = BSPScheduler(
            block_w=N, block_h=1, sampling_rate=1.0,
            mesh_width=N, mesh_height=1,
        )
        scheduler.execute_kernel_fn(kernel, self.ws, steps=1)

        result_bytes = self.ws.memcpy_d2h(self.ptr_Z, N * 4)
        result = np.frombuffer(bytes(result_bytes), dtype=np.float32)

        expected = ALPHA * self.X + self.Y  # [12, 24, 36, 48]
        np.testing.assert_array_almost_equal(result, expected)

    def test_saxpy_perf_model(self):
        """SAXPY superstep: 2 LDR_GLOBAL + 1 STR_GLOBAL → max(100,100,100) = 100 cycles."""
        kernel = _build_saxpy_kernel(self.ptr_X, self.ptr_Y, self.ptr_Z, ALPHA)

        scheduler = BSPScheduler(
            block_w=N, block_h=1, sampling_rate=1.0,
            mesh_width=N, mesh_height=1,
        )
        scheduler.execute_kernel_fn(kernel, self.ws, steps=1)

        self.assertEqual(scheduler.perf.total_cycles, 100)

    def test_saxpy_sampling_partial(self):
        """sampling_rate=0.0 → only 1 block sampled, but output is still written for that block."""
        kernel = _build_saxpy_kernel(self.ptr_X, self.ptr_Y, self.ptr_Z, ALPHA)

        scheduler = BSPScheduler(
            block_w=N, block_h=1, sampling_rate=0.0,
            mesh_width=N, mesh_height=1,
        )
        # With one 4x1 block covering the entire 4x1 grid, sampling_rate=0.0
        # still forces at least 1 block — so all 4 PEs run.
        scheduler.execute_kernel_fn(kernel, self.ws, steps=1)

        result_bytes = self.ws.memcpy_d2h(self.ptr_Z, N * 4)
        result = np.frombuffer(bytes(result_bytes), dtype=np.float32)
        expected = ALPHA * self.X + self.Y
        np.testing.assert_array_almost_equal(result, expected)

    def test_saxpy_runtime_estimate(self):
        """get_estimated_runtime returns total_cycles / (clock_mhz * 1e6)."""
        kernel = _build_saxpy_kernel(self.ptr_X, self.ptr_Y, self.ptr_Z, ALPHA)

        scheduler = BSPScheduler(
            block_w=N, block_h=1, sampling_rate=1.0,
            mesh_width=N, mesh_height=1,
        )
        runtime = scheduler.execute_kernel_fn(kernel, self.ws, steps=1)

        # 100 cycles @ 750 MHz = 100 / 750e6 ≈ 1.333e-7 s
        expected = 100 / (750 * 1e6)
        self.assertAlmostEqual(runtime, expected, places=15)


if __name__ == '__main__':
    unittest.main()
