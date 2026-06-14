# RECV_S (Receive South)

## Description
Receives a packet from the South neighbor and stores it in the specified register.

## Behavior
```c
void execute_recv_s(CS3CoreState *state, int rd, MeshNetwork *net) {
    MeshPacket pkt = net->pop_packet(state->core_x, state->core_y, SOUTH);
    state->regs[rd].data.f32[0] = (float)pkt.payload;
}
```
