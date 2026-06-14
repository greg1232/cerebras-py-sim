# RECV_E (Receive East)

## Description
Receives a packet from the East neighbor and stores it in the specified register.

## Behavior
```c
void execute_recv_e(CS3CoreState *state, int rd, MeshNetwork *net) {
    MeshPacket pkt = net->pop_packet(state->core_x, state->core_y, EAST);
    state->regs[rd].data.f32[0] = (float)pkt.payload;
}
```
