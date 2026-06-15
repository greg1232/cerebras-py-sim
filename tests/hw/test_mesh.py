import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.hw.mesh import Direction, MeshPacket, MeshBuffer, MeshNode, MeshNetwork


def make_packet(data: bytes = b'\x01\x02\x03\x04') -> MeshPacket:
    return MeshPacket(payload=data, source_dir=Direction.NORTH, flags=0)


class TestDirection(unittest.TestCase):
    def test_opposite_north_south(self):
        self.assertEqual(Direction.NORTH.opposite(), Direction.SOUTH)
        self.assertEqual(Direction.SOUTH.opposite(), Direction.NORTH)

    def test_opposite_east_west(self):
        self.assertEqual(Direction.EAST.opposite(), Direction.WEST)
        self.assertEqual(Direction.WEST.opposite(), Direction.EAST)


class TestMeshBuffer(unittest.TestCase):
    def test_push_pop_fifo(self):
        buf = MeshBuffer(capacity=4)
        p1 = make_packet(b'\x01')
        p2 = make_packet(b'\x02')
        buf.push(p1)
        buf.push(p2)
        self.assertEqual(buf.pop(), p1)
        self.assertEqual(buf.pop(), p2)

    def test_capacity_overflow(self):
        buf = MeshBuffer(capacity=2)
        buf.push(make_packet(b'\x01'))
        buf.push(make_packet(b'\x02'))
        with self.assertRaises(OverflowError):
            buf.push(make_packet(b'\x03'))

    def test_pop_empty_raises(self):
        buf = MeshBuffer()
        with self.assertRaises(IndexError):
            buf.pop()

    def test_len_and_is_empty(self):
        buf = MeshBuffer()
        self.assertTrue(buf.is_empty())
        buf.push(make_packet())
        self.assertEqual(len(buf), 1)
        self.assertFalse(buf.is_empty())


class TestMeshNetwork(unittest.TestCase):
    def setUp(self):
        # block_size=(4,4) so the 800x900 grid has 4-PE-wide blocks for isolation
        self.net = MeshNetwork(block_size=(4, 4))

    # ── hop_count ──────────────────────────────────────────────────────────────
    def test_hop_count_same_node(self):
        self.assertEqual(self.net.hop_count(3, 3, 3, 3), 0)

    def test_hop_count_horizontal(self):
        self.assertEqual(self.net.hop_count(0, 0, 3, 0), 3)

    def test_hop_count_manhattan(self):
        self.assertEqual(self.net.hop_count(0, 0, 2, 3), 5)

    # ── send / recv / has_packet ────────────────────────────────────────────────
    def test_send_recv_east(self):
        """Send EAST from (0,0): packet arrives in (1,0)'s WEST buffer."""
        pkt = make_packet(b'hello')
        self.net.send_packet(0, 0, Direction.EAST, pkt)
        self.assertTrue(self.net.has_packet(1, 0, Direction.WEST))
        received = self.net.recv_packet(1, 0, Direction.WEST)
        self.assertEqual(received.payload, b'hello')

    def test_send_recv_south(self):
        """Send SOUTH from (0,0): packet arrives in (0,1)'s NORTH buffer."""
        pkt = make_packet(b'data')
        self.net.send_packet(0, 0, Direction.SOUTH, pkt)
        self.assertTrue(self.net.has_packet(0, 1, Direction.NORTH))
        received = self.net.recv_packet(0, 1, Direction.NORTH)
        self.assertEqual(received.payload, b'data')

    def test_has_packet_false_when_empty(self):
        self.assertFalse(self.net.has_packet(5, 5, Direction.NORTH))

    def test_send_out_of_bounds_raises(self):
        with self.assertRaises(IndexError):
            # Sending WEST from column 0 is out of bounds
            self.net.send_packet(0, 0, Direction.WEST, make_packet())

    # ── block isolation ────────────────────────────────────────────────────────
    def test_block_isolation_same_block_allowed(self):
        """Nodes (0,0) and (3,3) are in the same 4x4 block — no error."""
        self.net.send_packet(0, 0, Direction.EAST, make_packet())  # (0,0)→(1,0) same block

    def test_block_isolation_cross_block_raises(self):
        """Sending from column 3 to column 4 crosses block boundary."""
        with self.assertRaises(PermissionError):
            self.net.send_packet(3, 0, Direction.EAST, make_packet())

    # ── route_global_load ──────────────────────────────────────────────────────
    def test_route_within_block_delivers(self):
        """XY routing (0,0)→(2,1) stays within block[0] — packet arrives."""
        payload = b'\xDE\xAD\xBE\xEF'
        self.net.route_global_load(0, 0, 2, 1, payload)
        # The final destination (2,1) should have the packet
        self.assertTrue(
            self.net.has_packet(2, 1, Direction.NORTH) or
            self.net.has_packet(2, 1, Direction.SOUTH) or
            self.net.has_packet(2, 1, Direction.EAST) or
            self.net.has_packet(2, 1, Direction.WEST),
            "Packet did not arrive at destination (2,1)"
        )

    def test_route_same_node_noop(self):
        """Routing src==dst places no packets."""
        before = sum(
            len(self.net._get_node(1, 1).buffers[d]) for d in Direction
        )
        self.net.route_global_load(1, 1, 1, 1, b'noop')
        after = sum(
            len(self.net._get_node(1, 1).buffers[d]) for d in Direction
        )
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
