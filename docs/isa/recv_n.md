# RECV_N (Receive North)

## Description
Receives a packet from the North neighbor and stores it in the specified register.

## Behavior
```c
void execute_recv_n(CS3CoreState *state, int rd, MeshNetwork *net) {
    MeshPacket pkt = net->pop_packet(state->core_x, state->core_y, NORTH);
    state->regs[rd].data.f32[0] = (float)pkt.payload;
}
```
