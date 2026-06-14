import numpy as np
import unittest
import sys
sys.path.insert(0, '/Users/gregorydiamos/checkout/cerebras-sim/src')
from cerebras_sim.hw.memory import WeightServer, DevicePtr

class TestWeightServer(unittest.TestCase):
    def setUp(self):
        self.ws = WeightServer()

    def test_malloc_returns_ptr(self):
        ptr = self.ws.malloc(1024)
        self.assertIsInstance(ptr, DevicePtr)
        self.assertIsNotNone(ptr)

    def test_malloc_advances_ptr(self):
        ptr1 = self.ws.malloc(1024)
        ptr2 = self.ws.malloc(1024)
        self.assertNotEqual(ptr1.address, ptr2.address)

    def test_memcpy_roundtrip(self):
        data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        size = data.nbytes
        ptr = self.ws.malloc(size)
        self.ws.memcpy_h2d(ptr, data)

        result_bytes = self.ws.memcpy_d2h(ptr, size)
        result_array = np.frombuffer(result_bytes, dtype=np.float32)
        np.testing.assert_array_equal(data, result_array)

    def test_load_store(self):
        ptr = self.ws.malloc(1024)
        val = 42.42
        self.ws.store(ptr, 0, val)
        read_val = self.ws.load(ptr, 0)
        # float32 round-trip, so compare with tolerance
        self.assertAlmostEqual(val, read_val, places=4)

    def test_bandwidth_tracking(self):
        initial_bw = self.ws.total_bytes_transferred
        data = np.zeros(100, dtype=np.float32)
        ptr = self.ws.malloc(data.nbytes)
        self.ws.memcpy_h2d(ptr, data)
        self.assertEqual(self.ws.total_bytes_transferred, initial_bw + data.nbytes)
