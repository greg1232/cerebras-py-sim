import unittest
import numpy as np
from src.cerebras_sim.engine.context import KernelContext
from src.cerebras_sim.engine.perf_model import PerformanceCounter
from src.cerebras_sim.hw.memory import WeightServer
from src.cerebras_sim.engine.sampler import SamplingManager

def heat_equation_kernel(ctx, u_ptr, u_next_ptr):
    W, H = 16, 16
    u = ctx.sram_alloc("u", W * H)
    u_next = ctx.sram_alloc("u_next", W * H)
    halo_n = ctx.sram_alloc("halo_n", W)
    halo_s = ctx.sram_alloc("halo_s", W)
    halo_w = ctx.sram_alloc("halo_w", H)
    halo_e = ctx.sram_alloc("halo_e", H)

    # Load tile
    for y in range(H):
        for x in range(W):
            val = ctx.load_global(u_ptr, (y * W + x) * 4)
            ctx.sram_store_2d(u, x, y, val)

    # Halo Exchange (Simplified for test: just pull neighbors)
    for x in range(W):
        ctx.sram_store_2d(halo_n, x, 0, ctx.neighbor_load(u, "NORTH", x * 4))
        ctx.sram_store_2d(halo_s, x, 0, ctx.neighbor_load(u, "SOUTH", (15 * W + x) * 4))
    for y in range(H):
        ctx.sram_store_2d(halo_w, 0, y, ctx.neighbor_load(u, "WEST", (y * 1) * 4))
        ctx.sram_store_2d(halo_e, 0, y, ctx.neighbor_load(u, "EAST", (y * 1 + 15) * 4))

    ctx.sync()

    alpha = 0.1
    for y in range(H):
        for x in range(W):
            curr = ctx.sram_load_2d(u, x, y)
            left  = ctx.sram_load_2d(u, x-1, y) if x > 0 else ctx.sram_load_2d(halo_w, 0, y)
            right = ctx.sram_load_2d(u, x+1, y) if x < 15 else ctx.sram_load_2d(halo_e, 0, y)
            up    = ctx.sram_load_2d(u, x, y-1) if y > 0 else ctx.sram_load_2d(halo_n, x, 0)
            down  = ctx.sram_load_2d(u, x, y+1) if y < 15 else ctx.sram_load_2d(halo_s, x, 0)

            val_next = curr + alpha * (left + right + up + down - 4 * curr)
            ctx.sram_store_2d(u_next, x, y, val_next)

    for y in range(H):
        for x in range(W):
            val = ctx.sram_load_2d(u_next, x, y)
            ctx.store_global(u_next_ptr, (y * W + x) * 4, val)

class TestHeatEquation(unittest.TestCase):
    def setUp(self):
        self.B = 16
        self.ws = WeightServer()
        self.perf = PerformanceCounter()
        self.sampler = SamplingManager(self.B, self.B)
        self.ws.memory = {}

    def test_execution(self):
        ctx = KernelContext(0, 0, self.ws, self.perf, self.sampler)
        ctx.load_global = lambda ptr, offset: 1.0
        ctx.neighbor_load = lambda h, d, o: 2.0

        try:
            heat_equation_kernel(ctx, 0x1000, 0x2000)
        except Exception as e:
            self.fail(f"Kernel crashed: {e}")

if __name__ == "__main__":
    unittest.main()
