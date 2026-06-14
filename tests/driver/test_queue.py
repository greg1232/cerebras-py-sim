import unittest
import sys
sys.path.insert(0, '/Users/gregorydiamos/checkout/cerebras-sim/src')
from cerebras_sim.driver.queue import CS3Queue, CommandType

class TestCS3Queue(unittest.TestCase):
    def test_fifo_order(self):
        q = CS3Queue()
        q.enqueue(CommandType.MALLOC, size=1024)
        q.enqueue(CommandType.FREE, ptr=123)
        q.enqueue(CommandType.SYNC_BARRIER)

        drained = q.drain()
        self.assertEqual(len(drained), 3)
        self.assertEqual(drained[0].type, CommandType.MALLOC)
        self.assertEqual(drained[1].type, CommandType.FREE)
        self.assertEqual(drained[2].type, CommandType.SYNC_BARRIER)

    def test_drain_clears(self):
        q = CS3Queue()
        q.enqueue(CommandType.MALLOC, size=1024)
        q.drain()
        self.assertEqual(len(q._commands), 0)
