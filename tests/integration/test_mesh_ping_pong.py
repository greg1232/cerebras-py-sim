"""
Integration test for intra-block mesh communication: Ping-Pong.
Verifies that two PEs can send and receive packets using a tick-based scheduler.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from cerebras_sim.engine.scheduler import BSPScheduler
from cerebras_sim.engine.decoder import decode_instruction

def pack_mesh_instr(func_code: int, rd: int = 0):
    """
    Packs a MESH instruction binary.
    Opcode=0x03 (MESH), rd=rd, rs1=0, rs2=0, func=func_code
    """
    return (0x03 << 26) | (rd << 21) | func_code

class TestMeshPingPong(unittest.TestCase):
    def test_ping_pong_exchange(self):
        """
        PE(0,0) sends EAST -> PE(1,0) receives WEST (from East)
        PE(1,0) sends WEST  -> PE(0,0) receives EAST (from West)
        """
        # Grid 2x1, Block 2x1, all sampled
        sched = BSPScheduler(block_w=2, block_h=1, sampling_rate=1.0,
                             mesh_width=2, mesh_height=1)

        # PE(0,0) Program:
        # 1. SEND_E (0x02) -> Packet goes to PE(1,0) WEST buffer
        # 2. WAIT_E (0x0A)  -> Wait for packet in EAST buffer (from PE 1,0)
        # 3. RECV_E (0x06)   -> Pop from EAST buffer into reg 3
        prog0 = [
            pack_mesh_instr(0x02), # SEND_E
            pack_mesh_instr(0x0A), # WAIT_E
            pack_mesh_instr(0x06, rd=3) # RECV_E
        ]

        # PE(1,0) Program:
        # 1. WAIT_W (0x0B)   -> Wait for packet in WEST buffer (from PE 0,0)
        # 2. RECV_W (0x07)   -> Pop from WEST buffer into reg 3
        # 3. SEND_W (0x03)   -> Send packet to PE(0,0) EAST buffer
        prog1 = [
            pack_mesh_instr(0x0B), # WAIT_W
            pack_mesh_instr(0x07, rd=3), # RECV_W
            pack_mesh_instr(0x03), # SEND_W
        ]

        sched.cores[0][0].program = prog0
        sched.cores[1][0].program = prog1

        # run_superstep executes until all PEs reach sync/halt.
        # Since no SYNC is present, they run until program ends.
        sched.run_superstep()

        # PE(0,0) should have received a packet in reg 3
        self.assertEqual(sched.cores[0][0].regs[3].f32[0], 1.0)
        # PE(1,0) should have received a packet in reg 3
        self.assertEqual(sched.cores[1][0].regs[3].f32[0], 1.0)

if __name__ == '__main__':
    unittest.main()
