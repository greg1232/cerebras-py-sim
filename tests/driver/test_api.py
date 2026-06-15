import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.driver.api import CS3Driver
from cerebras_sim.driver.queue import CommandType
from cerebras_sim.compiler.kernel import cs3_kernel


class TestCS3Driver(unittest.TestCase):
    def setUp(self):
        self.driver = CS3Driver()

    # ── malloc ─────────────────────────────────────────────────────────────────
    def test_malloc_returns_device_ptr(self):
        ptr = self.driver.cs3_malloc(1024)
        self.assertIsNotNone(ptr)
        self.assertGreater(int(ptr), 0)

    def test_malloc_enqueues_command(self):
        self.driver.cs3_malloc(512)
        cmds = self.driver.queue.drain()
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0].type, CommandType.MALLOC)
        self.assertEqual(cmds[0].args['size'], 512)

    def test_malloc_out_of_memory_raises(self):
        # Exhaust device memory: WeightServer cap is 1.5 TB, so ask for more
        with self.assertRaises(MemoryError):
            self.driver.cs3_malloc(2 * 1024 ** 4)  # 2 TB

    # ── memcpy h2d / d2h ───────────────────────────────────────────────────────
    def test_memcpy_h2d_enqueues_command(self):
        ptr = self.driver.cs3_malloc(4)
        self.driver.queue.drain()  # clear malloc cmd

        src_data = b'\x01\x02\x03\x04'
        self.driver.cs3_memcpy_h2d(ptr, src_data, 4)
        cmds = self.driver.queue.drain()
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0].type, CommandType.MEMCPY_H2D)
        self.assertEqual(cmds[0].args['dst'], ptr)
        self.assertEqual(cmds[0].args['size'], 4)

    def test_memcpy_d2h_returns_buffer_and_enqueues(self):
        ptr = self.driver.cs3_malloc(8)
        self.driver.queue.drain()

        buf = self.driver.cs3_memcpy_d2h(ptr, 8)
        self.assertIsInstance(buf, bytearray)
        self.assertEqual(len(buf), 8)
        cmds = self.driver.queue.drain()
        self.assertEqual(cmds[0].type, CommandType.MEMCPY_D2H)

    # ── launch ─────────────────────────────────────────────────────────────────
    def test_launch_enqueues_kernel_launch(self):
        @cs3_kernel(block_w=4, block_h=4)
        def my_kernel(args):
            pass

        self.driver.cs3_launch(my_kernel, grid_w=8, grid_h=8,
                               block_w=4, block_h=4, args={'n': 16})
        cmds = self.driver.queue.drain()
        self.assertEqual(len(cmds), 1)
        cmd = cmds[0]
        self.assertEqual(cmd.type, CommandType.KERNEL_LAUNCH)
        self.assertEqual(cmd.args['grid_w'], 8)
        self.assertEqual(cmd.args['grid_h'], 8)
        self.assertEqual(cmd.args['block_w'], 4)
        self.assertEqual(cmd.args['block_h'], 4)
        self.assertEqual(cmd.args['args']['n'], 16)

    # ── sync ───────────────────────────────────────────────────────────────────
    def test_sync_enqueues_barrier(self):
        self.driver.cs3_sync()
        cmds = self.driver.queue.drain()
        self.assertEqual(len(cmds), 1)
        self.assertEqual(cmds[0].type, CommandType.SYNC_BARRIER)

    # ── command sequence ───────────────────────────────────────────────────────
    def test_full_sequence_order(self):
        """malloc → memcpy_h2d → sync should appear in FIFO order."""
        ptr = self.driver.cs3_malloc(64)
        self.driver.cs3_memcpy_h2d(ptr, b'\x00' * 64, 64)
        self.driver.cs3_sync()

        cmds = self.driver.queue.drain()
        types = [c.type for c in cmds]
        self.assertEqual(types, [CommandType.MALLOC, CommandType.MEMCPY_H2D, CommandType.SYNC_BARRIER])


if __name__ == '__main__':
    unittest.main()
